from rest_framework import serializers
from orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["sku", "name", "quantity", "unit_price", "total_price"]


class OrderDetailSerializer(serializers.ModelSerializer):
    # 👇 entries берём ИЗ items
    entries = OrderItemSerializer(
        many=True,
        read_only=True,
        source="items"
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "code",
            "source",
            "status",
            "total_price",
            "delivery_cost",
            "created_at_source",
            "entries",
        ]
