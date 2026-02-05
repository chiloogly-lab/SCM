from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.contrib import messages

from .models import Supplier
from .auto_supply import generate_auto_supply
from .models import Order
from .serializers import OrderSerializer
from .constants import ACTIVE_MARKETPLACE_STATES

@staff_member_required
def generate_supply_view(request):
    supplier = Supplier.objects.first()

    if not supplier:
        messages.error(request, "Добавьте поставщика перед формированием заказа.")
        return redirect("/admin/")

    supply = generate_auto_supply(supplier)

    messages.success(
        request,
        f"Авто-заказ #{supply.id} сформирован для {supplier.name}"
    )

    return redirect(f"/admin/orders/supplyorder/{supply.id}/change/")

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Orders API

    /api/orders/           — все заказы (история)
    /api/orders/active/    — актуальные заказы
    /api/orders/new/       — новые заказы (Kaspi NEW)
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        БАЗОВЫЙ queryset:
        используется для /api/orders/
        (история, аналитика, поиск)
        """
        return Order.objects.all().order_by("-created_at_source")

    # =========================================================
    # АКТУАЛЬНЫЕ ЗАКАЗЫ
    # =========================================================
    @action(detail=False, methods=["get"], url_path="active")
    def active_orders(self, request):
        """
        Все заказы, которые АКТУАЛЬНЫ СЕЙЧАС
        (не архивные по логике Kaspi)
        """
        qs = (
            Order.objects
            .filter(marketplace_state__in=ACTIVE_MARKETPLACE_STATES)
            .order_by("-created_at_source")
        )

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # =========================================================
    # НОВЫЕ ЗАКАЗЫ (правая панель)
    # =========================================================
    @action(detail=False, methods=["get"], url_path="new")
    def new_orders(self, request):
        """
        ТОЛЬКО новые заказы Kaspi
        (state = NEW)
        """
        qs = (
            Order.objects
            .filter(marketplace_state="NEW")
            .order_by("-created_at_source")[:5]
        )

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
