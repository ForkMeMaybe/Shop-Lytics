from rest_framework import serializers
from .models import (
    Tenant,
    Customer,
    Product,
    Order,
    OrderItem,
    CustomEvent,
    WebhookSubscription,
)


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "shopify_domain", "created_at", "access_token"]
        extra_kwargs = {"access_token": {"write_only": True}}


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "tenant",
            "shopify_customer_id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "address1",
            "address2",
            "city",
            "province",
            "country",
            "zip",
            "company",
            "created_at",
            "updated_at",
        ]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "tenant",
            "shopify_product_id",
            "title",
            "description",
            "price",
            "sku",
            "inventory_quantity",
            "created_at",
            "updated_at",
        ]


class OrderItemReadSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "order", "product", "quantity", "price"]


class OrderReadSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    items = OrderItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "tenant",
            "shopify_order_id",
            "customer",
            "total_price",
            "currency",
            "financial_status",
            "fulfillment_status",
            "created_at",
            "updated_at",
            "items",
        ]


class OrderItemWriteSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product"
    )

    class Meta:
        model = OrderItem
        fields = ("product_id", "quantity", "price")


class OrderWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = (
            "tenant",
            "shopify_order_id",
            "customer",
            "total_price",
            "currency",
            "financial_status",
            "fulfillment_status",
            "created_at",
            "updated_at",
        )


class CustomEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomEvent
        fields = ["id", "tenant", "event_type", "customer", "metadata", "created_at"]


class WebhookSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookSubscription
        fields = [
            "id",
            "tenant",
            "topic",
            "address",
            "status",
            "last_response",
            "updated_at",
        ]
