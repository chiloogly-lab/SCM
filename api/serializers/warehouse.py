from rest_framework import serializers


class StockRowSerializer(serializers.Serializer):
    sku = serializers.CharField()
    name = serializers.CharField()
    stock = serializers.IntegerField()
    forecast_14 = serializers.IntegerField()
    recommended_purchase = serializers.IntegerField()
