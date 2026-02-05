from rest_framework import serializers
from .models import Order, OrderItem, CustomerSnapshot, DeliverySnapshot


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "sku",
            "name",
            "quantity",
            "unit_price",
            "total_price",
        ]


class CustomerSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerSnapshot
        fields = [
            "first_name",
            "last_name",
            "phone",
        ]


class DeliverySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliverySnapshot
        fields = [
            "city",
            "address",
            "pickup_point",
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer = CustomerSnapshotSerializer(read_only=True)
    delivery = DeliverySnapshotSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "code",
            "source",
            "status",
            "marketplace_status",
            "marketplace_state",
            "total_price",
            "delivery_cost",
            "delivery_mode",
            "created_at_source",
            "items",
            "customer",
            "delivery",
        ]
