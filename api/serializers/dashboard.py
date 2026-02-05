from rest_framework import serializers


class DashboardSerializer(serializers.Serializer):
    sales_today = serializers.DecimalField(max_digits=14, decimal_places=2)
    sales_7d = serializers.DecimalField(max_digits=14, decimal_places=2)
    sales_30d = serializers.DecimalField(max_digits=14, decimal_places=2)

    forecast_30 = serializers.IntegerField()
    forecast_90 = serializers.IntegerField()

    supply = serializers.ListField()
