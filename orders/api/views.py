from django.db.models import F
from rest_framework.generics import ListAPIView

from orders.models import Product
from .serializers import ProductStockSerializer
from ...api.serializers.order import OrderSerializer


class ProductStockListView(ListAPIView):
    serializer_class = ProductStockSerializer

    def get_queryset(self):
        return (
            Product.objects
            .select_related()
            .annotate(
                quantity=F("stock__quantity")
            )
            .order_by("name")
        )

class ActiveOrdersListView(ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Order.objects
            .filter(
                status__in=[
                    Order.Status.NEW,
                    Order.Status.APPROVED,
                    Order.Status.PACKING,
                    Order.Status.SHIPPED,
                    Order.Status.IN_TRANSIT,
                ]
            )
            .order_by("-created_at_source")
        )
