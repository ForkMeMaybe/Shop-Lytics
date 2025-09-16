from django.shortcuts import render, redirect
from django.core.mail import BadHeaderError
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.views.decorators.csrf import csrf_exempt
import json
from smtplib import SMTPException
from templated_mail.mail import BaseEmailMessage
from .utils import generate_otp, validate_otp
import requests
import hmac
import hashlib
from django.http import JsonResponse
from store.models import Tenant
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from store.tasks import fetch_existing_data_task, subscribe_to_webhooks_task


@csrf_exempt
def send_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON format."})

        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({"success": False, "message": "Invalid email format."})

        email_otp = generate_otp()
        redis_key = f"otp:{email}"
        cache.set(redis_key, email_otp)

        try:
            message = BaseEmailMessage(
                template_name="emails/otp_template.html",
                context={"email_otp": email_otp},
            )
            message.send([email])
        except (BadHeaderError, SMTPException) as e:
            return JsonResponse(
                {"success": False, "message": f"Failed to send OTP. Error: {str(e)}"}
            )

        return JsonResponse(
            {
                "success": True,
                "message": "OTP sent successfully. Please check your email.",
            }
        )


@csrf_exempt
def verify_otp(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            user_otp = data.get("otp")
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON format."})

        if not email or not user_otp:
            return JsonResponse(
                {"success": False, "message": "Email and OTP are required."}
            )

        redis_key = f"otp:{email}"
        stored_otp = cache.get(redis_key)

        if stored_otp is None:
            return JsonResponse(
                {"success": False, "message": "OTP expired or not found."}
            )

        if validate_otp(stored_otp, user_otp):
            cache.delete(redis_key)
            cache.set(f"otp_verified:{email}", True, timeout=600)
            return JsonResponse(
                {"success": True, "message": "OTP verified successfully."}
            )
        else:
            cache.delete(redis_key)
            return JsonResponse({"success": False, "message": "Invalid OTP."})

    return JsonResponse({"success": False, "message": "Invalid request method."})


def shopify_auth(request):
    shop = request.GET.get("shop")
    if not shop:
        return render(request, "error.html", {"message": "Missing shop parameter."})

    scopes = ["read_products", "read_orders", "read_customers"]
    redirect_uri = f"https://{request.get_host()}/auth/shopify/callback/"
    auth_url = f"https://{shop}/admin/oauth/authorize?client_id={settings.SHOPIFY_API_KEY}&scope={','.join(scopes)}&redirect_uri={redirect_uri}"
    return redirect(auth_url)


def shopify_callback(request):
    shop = request.GET.get("shop")
    code = request.GET.get("code")
    hmac_param = request.GET.get("hmac")

    query_string = request.META["QUERY_STRING"]
    params = {
        k: v
        for k, v in [
            p.split("=") for p in query_string.split("&") if p.split("=")[0] != "hmac"
        ]
    }
    message = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    digest = hmac.new(
        settings.SHOPIFY_API_SECRET.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(digest, hmac_param):
        return render(request, "error.html", {"message": "Invalid HMAC."})

    token_url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        "client_id": settings.SHOPIFY_API_KEY,
        "client_secret": settings.SHOPIFY_API_SECRET,
        "code": code,
    }
    response = requests.post(token_url, json=payload)

    if response.status_code != 200:
        return render(request, "error.html", {"message": "Failed to get access token."})

    access_token = response.json()["access_token"]

    user = request.user
    if not user.is_authenticated:
        shop_url = f"https://{shop}/admin/api/2023-10/shop.json"
        headers = {"X-Shopify-Access-Token": access_token}
        shop_response = requests.get(shop_url, headers=headers)

        if shop_response.status_code != 200:
            return render(
                request, "error.html", {"message": "Failed to fetch shop details."}
            )

        shop_data = shop_response.json()["shop"]
        user_email = shop_data.get("email")
        first_name = shop_data.get("shop_owner", "").split(" ")[0]
        last_name = " ".join(shop_data.get("shop_owner", "").split(" ")[1:])

        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=user_email,
            defaults={
                "username": user_email,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        if created:
            user.set_password(get_random_string(12))
            user.save()

        login(request, user)

    tenant, _ = Tenant.objects.update_or_create(
        shopify_domain=shop,
        defaults={
            "user": user,
            "name": shop.split(".")[0],
            "access_token": access_token,
        },
    )

    print("WEBHOOKS SUBS")
    subscribe_to_webhooks_task.delay(tenant.id)
    fetch_existing_data_task.delay(tenant.id)
    print("EXISTING DATA")

    return redirect("https://shop-lytics-frontend.onrender.com")

