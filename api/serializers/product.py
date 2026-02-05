from rest_framework import serializers

class ProductStockSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sku = serializers.CharField()
    name = serializers.CharField()
    quantity = serializers.IntegerField()
