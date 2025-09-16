from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import (
    Tenant,
    Customer,
    Product,
    Order,
    OrderItem,
    CustomEvent,
    WebhookSubscription,
)
from .serializers import (
    TenantSerializer,
    CustomerSerializer,
    ProductSerializer,
    OrderReadSerializer,
    OrderWriteSerializer,
    CustomEventSerializer,
    WebhookSubscriptionSerializer,
)
from django.db import transaction
from .tasks import fetch_existing_data_task, subscribe_to_webhooks_task


class TenantListCreateView(generics.ListCreateAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer

    def perform_create(self, serializer):
        tenant = serializer.save()
        print("WEBHOOK API SUBS")
        subscribe_to_webhooks_task.delay(tenant.id)
        fetch_existing_data_task.delay(tenant.id)
        print("EXISTING DATA API")


class TenantDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer


class CustomerListCreateView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def create(self, request, *args, **kwargs):
        shopify_data = request.data
        shopify_domain = request.headers.get("X-Shopify-Shop-Domain")

        try:
            tenant = Tenant.objects.get(shopify_domain=shopify_domain)
        except Tenant.DoesNotExist:
            return Response(
                {"error": f"Tenant with domain {shopify_domain} not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        default_address_data = shopify_data.get("default_address", {})

        customer, created = Customer.objects.update_or_create(
            shopify_customer_id=shopify_data.get("id"),
            tenant=tenant,
            defaults={
                "first_name": shopify_data.get("first_name"),
                "last_name": shopify_data.get("last_name"),
                "email": shopify_data.get("email"),
                "phone": shopify_data.get("phone") or default_address_data.get("phone"),
                "address1": default_address_data.get("address1"),
                "address2": default_address_data.get("address2"),
                "city": default_address_data.get("city"),
                "province": default_address_data.get("province"),
                "country": default_address_data.get("country"),
                "zip": default_address_data.get("zip"),
                "company": default_address_data.get("company"),
                "created_at": shopify_data.get("created_at"),
                "updated_at": shopify_data.get("updated_at"),
            },
        )

        serializer = self.get_serializer(customer)
        headers = self.get_success_headers(serializer.data)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

        return Response(serializer.data, status=status_code, headers=headers)


class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request, *args, **kwargs):
        shopify_data = request.data
        variants = shopify_data.get("variants")

        if not variants:
            return Response(
                {"error": "Product has no variants."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        shopify_domain = request.headers.get("X-Shopify-Shop-Domain")

        try:
            tenant = Tenant.objects.get(shopify_domain=shopify_domain)
        except Tenant.DoesNotExist:
            return Response(
                {"error": f"Tenant with domain {shopify_domain} not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_products = []

        for variant in variants:
            product, created = Product.objects.update_or_create(
                shopify_product_id=variant.get("id"),
                tenant=tenant,
                defaults={
                    "title": f"{shopify_data.get('title')} - {variant.get('title')}",
                    "description": shopify_data.get("body_html"),
                    "price": variant.get("price"),
                    "sku": variant.get("sku"),
                    "inventory_quantity": variant.get("inventory_quantity", 0),
                    "created_at": shopify_data.get("created_at")
                    or shopify_data.get("published_at"),
                    "updated_at": variant.get("updated_at")
                    or shopify_data.get("updated_at"),
                },
            )

            serializer = self.get_serializer(product)
            created_products.append(serializer.data)

        headers = self.get_success_headers(created_products)
        return Response(
            created_products, status=status.HTTP_201_CREATED, headers=headers
        )


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderWriteSerializer
        return OrderReadSerializer

    def create(self, request, *args, **kwargs):
        shopify_data = request.data
        shopify_domain = request.headers.get("X-Shopify-Shop-Domain")

        try:
            tenant = Tenant.objects.get(shopify_domain=shopify_domain)
        except Tenant.DoesNotExist:
            return Response(
                {"error": f"Tenant with domain {shopify_domain} not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                customer_data = shopify_data.get("customer")
                customer = None

                if customer_data:
                    customer, _ = Customer.objects.update_or_create(
                        shopify_customer_id=customer_data.get("id"),
                        tenant=tenant,
                        defaults={
                            "first_name": customer_data.get("first_name"),
                            "last_name": customer_data.get("last_name"),
                            "email": customer_data.get("email"),
                            "phone": customer_data.get("phone"),
                            "created_at": customer_data.get("created_at")
                            or timezone.now(),
                            "updated_at": customer_data.get("updated_at")
                            or timezone.now(),
                        },
                    )

                order, created = Order.objects.update_or_create(
                    shopify_order_id=shopify_data.get("id"),
                    tenant=tenant,
                    defaults={
                        "customer": customer,
                        "total_price": shopify_data.get("total_price"),
                        "currency": shopify_data.get("currency"),
                        "financial_status": shopify_data.get("financial_status"),
                        "fulfillment_status": shopify_data.get("fulfillment_status"),
                        "created_at": shopify_data.get("created_at"),
                        "updated_at": shopify_data.get("updated_at"),
                    },
                )

                for item_data in shopify_data.get("line_items", []):
                    variant_id = item_data.get("variant_id")
                    product = Product.objects.filter(
                        shopify_product_id=variant_id
                    ).first()

                    if not product:
                        raise Exception(
                            f"Product with variant_id {variant_id} not found."
                        )

                    OrderItem.objects.update_or_create(
                        order=order,
                        product=product,
                        defaults={
                            "quantity": item_data.get("quantity"),
                            "price": item_data.get("price"),
                        },
                    )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderReadSerializer(order)
        headers = self.get_success_headers(serializer.data)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

        return Response(serializer.data, status=status_code, headers=headers)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return OrderWriteSerializer
        return OrderReadSerializer


class CustomEventListCreateView(generics.ListCreateAPIView):
    queryset = CustomEvent.objects.all()
    serializer_class = CustomEventSerializer

    def create(self, request, *args, **kwargs):
        shopify_data = request.data
        shopify_domain = request.headers.get("X-Shopify-Shop-Domain")
        webhook_topic = request.headers.get("X-Shopify-Topic")

        try:
            tenant = Tenant.objects.get(shopify_domain=shopify_domain)
        except Tenant.DoesNotExist:
            return Response(
                {"error": f"Tenant with domain {shopify_domain} not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event_type = "unknown"

        if webhook_topic == "checkouts/create":
            event_type = "checkout_started"
        elif webhook_topic == "checkouts/update":
            event_type = "checkout_updated"
        elif webhook_topic == "checkouts/delete":
            event_type = "checkout_deleted"

        customer_data = shopify_data.get("customer")
        customer = None

        if customer_data:
            customer, _ = Customer.objects.update_or_create(
                shopify_customer_id=customer_data.get("id"),
                tenant=tenant,
                defaults={
                    "first_name": customer_data.get("first_name"),
                    "last_name": customer_data.get("last_name"),
                    "email": customer_data.get("email"),
                    "phone": customer_data.get("phone"),
                    "created_at": customer_data.get("created_at") or timezone.now(),
                    "updated_at": customer_data.get("updated_at") or timezone.now(),
                },
            )

        event = CustomEvent.objects.create(
            tenant=tenant,
            event_type=event_type,
            customer=customer,
            metadata=shopify_data,
        )

        serializer = self.get_serializer(event)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class WebhookSubscriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WebhookSubscriptionSerializer

    def get_queryset(self):
        tenant = getattr(self.request.user, "tenant", None)
        if tenant:
            return WebhookSubscription.objects.filter(tenant=tenant)
        return WebhookSubscription.objects.none()

