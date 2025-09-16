from django.conf import settings
import requests
import logging
from .models import WebhookSubscription
from .models import Product, Customer, Order, OrderItem, Tenant
from celery import shared_task
import time


def subscribe_to_webhooks(tenant):
    shopify_domain = tenant.shopify_domain
    access_token = tenant.access_token
    base_url = settings.BASE_URL

    webhook_topics = {
        "orders/create": f"{base_url}/api/orders/",
        "products/create": f"{base_url}/api/products/",
        "customers/create": f"{base_url}/api/customers/",
        "checkouts/create": f"{base_url}/api/custom-events/",
        "checkouts/update": f"{base_url}/api/custom-events/",
        "checkouts/delete": f"{base_url}/api/custom-events/",
    }

    for topic, address in webhook_topics.items():
        webhook_url = f"https://{shopify_domain}/admin/api/2024-07/webhooks.json"
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": access_token,
        }
        payload = {
            "webhook": {
                "topic": topic,
                "address": address,
                "format": "json",
            }
        }

        try:
            response = requests.post(webhook_url, json=payload, headers=headers)
            if response.status_code in (200, 201):
                status = "success"
                logging.info(f"Webhook {topic} subscribed for {shopify_domain}")
            else:
                status = f"failed ({response.status_code})"
                logging.warning(
                    f"Webhook {topic} failed for {shopify_domain}: {response.text}"
                )
        except requests.exceptions.RequestException as e:
            status = "error"
            response = None
            logging.error(
                f"Exception subscribing {shopify_domain} to {topic} webhook: {e}"
            )

        WebhookSubscription.objects.update_or_create(
            tenant=tenant,
            topic=topic,
            defaults={
                "address": address,
                "status": status,
                "last_response": response.json() if response else None,
            },
        )


def fetch_existing_data(tenant):
    fetch_products(tenant)
    fetch_customers(tenant)
    fetch_orders(tenant)


def fetch_products(tenant):
    url = f"https://{tenant.shopify_domain}/admin/api/2024-07/products.json"
    headers = {"X-Shopify-Access-Token": tenant.access_token}

    while url:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            products = response.json().get("products", [])

            for product_data in products:
                for variant in product_data.get("variants", []):
                    Product.objects.update_or_create(
                        tenant=tenant,
                        shopify_product_id=variant.get("id"),
                        defaults={
                            "title": f"{product_data.get('title')} - {variant.get('title')}",
                            "description": product_data.get("body_html"),
                            "price": variant.get("price"),
                            "sku": variant.get("sku"),
                            "inventory_quantity": variant.get("inventory_quantity", 0),
                            "created_at": product_data.get("created_at")
                            or product_data.get("published_at"),
                            "updated_at": variant.get("updated_at")
                            or product_data.get("updated_at"),
                        },
                    )
            url = get_next_link(response.headers)
            time.sleep(0.5)
        else:
            break


def fetch_customers(tenant):
    url = f"https://{tenant.shopify_domain}/admin/api/2024-07/customers.json"
    headers = {"X-Shopify-Access-Token": tenant.access_token}

    while url:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            customers = response.json().get("customers", [])

            for customer_data in customers:
                default_address_data = customer_data.get("default_address", {})

                Customer.objects.update_or_create(
                    tenant=tenant,
                    shopify_customer_id=customer_data.get("id"),
                    defaults={
                        "first_name": customer_data.get("first_name"),
                        "last_name": customer_data.get("last_name"),
                        "email": customer_data.get("email"),
                        "phone": customer_data.get("phone")
                        or default_address_data.get("phone"),
                        "address1": default_address_data.get("address1"),
                        "address2": default_address_data.get("address2"),
                        "city": default_address_data.get("city"),
                        "province": default_address_data.get("province"),
                        "country": default_address_data.get("country"),
                        "zip": default_address_data.get("zip"),
                        "company": default_address_data.get("company"),
                        "created_at": customer_data.get("created_at"),
                        "updated_at": customer_data.get("updated_at"),
                    },
                )

            url = get_next_link(response.headers)
            time.sleep(0.5)
        else:
            break


def fetch_orders(tenant):
    url = f"https://{tenant.shopify_domain}/admin/api/2024-07/orders.json?status=any"
    headers = {"X-Shopify-Access-Token": tenant.access_token}
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            orders = response.json().get("orders", [])
            for order_data in orders:
                customer_data = order_data.get("customer")
                customer = None
                if customer_data:
                    customer, _ = Customer.objects.get_or_create(
                        tenant=tenant,
                        shopify_customer_id=customer_data.get("id"),
                        defaults={
                            "first_name": customer_data.get("first_name"),
                            "last_name": customer_data.get("last_name"),
                            "email": customer_data.get("email"),
                            "phone": customer_data.get("phone"),
                            "created_at": customer_data.get("created_at"),
                            "updated_at": customer_data.get("updated_at"),
                        },
                    )
                order, _ = Order.objects.update_or_create(
                    tenant=tenant,
                    shopify_order_id=order_data.get("id"),
                    defaults={
                        "customer": customer,
                        "total_price": order_data.get("total_price"),
                        "currency": order_data.get("currency"),
                        "financial_status": order_data.get("financial_status"),
                        "fulfillment_status": order_data.get("fulfillment_status"),
                        "created_at": order_data.get("created_at"),
                        "updated_at": order_data.get("updated_at"),
                    },
                )
                for item_data in order_data.get("line_items", []):
                    product = Product.objects.filter(
                        shopify_product_id=item_data.get("variant_id")
                    ).first()
                    if product:
                        OrderItem.objects.update_or_create(
                            order=order,
                            product=product,
                            defaults={
                                "quantity": item_data.get("quantity"),
                                "price": item_data.get("price"),
                            },
                        )
            url = get_next_link(response.headers)
            time.sleep(0.5)
        else:
            break


def get_next_link(headers):
    link_header = headers.get("Link")
    if link_header:
        links = link_header.split(", ")
        for link in links:
            if 'rel="next"' in link:
                return link.split(";")[0].strip("<>")
    return None

