from django.conf import settings
import requests


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
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(
                f"Failed to subscribe {shopify_domain} to {topic} webhook. Error: {e}"
            )
