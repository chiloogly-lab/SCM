from rest_framework import serializers
from orders.models import Order
from api.serializers.order_detail import OrderItemSerializer  # путь поправь под себя


class OrderSerializer(serializers.ModelSerializer):
    items_count = serializers.IntegerField(read_only=True)
    entries = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "code",
            "source",
            "status",
            "marketplace_status",
            "total_price",
            "delivery_mode",
            "created_at_source",
            "items_count",
            "entries",
        )

    def get_entries(self, obj):
        """
        Безопасно возвращаем состав заказа.
        НИКОГДА не ломает списки.
        """
        # если у заказа есть связанные items
        if hasattr(obj, "items"):
            qs = obj.items.all()
            if qs.exists():
                return OrderItemSerializer(qs, many=True).data

        # если данных нет — всегда пустой массив
        return []
