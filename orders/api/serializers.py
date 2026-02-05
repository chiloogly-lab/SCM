from rest_framework import serializers
from orders.models import Product, WarehouseStock


class ProductStockSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField()

    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "name",
            "quantity",
        )
