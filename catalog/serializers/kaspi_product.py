from rest_framework import serializers
from catalog.models import Product
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from stock.models import Stock


class KaspiProductSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(write_only=True)
    stock_quantity = serializers.IntegerField(
        source="stock.quantity",
        read_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "category",
            "kaspi_enabled",
            "purchase_price",
            "quantity",        # входящее поле
            "stock_quantity",  # отображаемое поле
        ]

    def create(self, validated_data):
        quantity = validated_data.pop("quantity", 0)

        product = Product.objects.create(**validated_data)

        Stock.objects.create(
            product=product,
            quantity=quantity
        )

        return product

    def update(self, instance, validated_data):
        quantity = validated_data.pop("quantity", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if quantity is not None:
            Stock.objects.update_or_create(
                product=instance,
                defaults={"quantity": quantity}
            )

        return instance

class KaspiProductViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        from catalog.serializers.kaspi_product import KaspiProductSerializer
        return KaspiProductSerializer

    def get_queryset(self):
        return (
            Product.objects
            .select_related("stock")
            .order_by("id")
        )