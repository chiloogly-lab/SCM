from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from orders.models import Order
from api.serializers.order import OrderSerializer


class OrderListAPIView(ListAPIView):
    queryset = Order.objects.all().order_by("-created_at_source")
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "source"]
    ordering_fields = ["created_at_source", "total_price"]
