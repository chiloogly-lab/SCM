from datetime import timedelta

from django.utils.timezone import now
from django.db.models import Sum, Value, F
from django.db.models.functions import Coalesce

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from orders.models import (
    Order,
    WarehouseStock,
    Product as StockProduct,
)

from catalog.models import Product as CatalogProduct
from analytics.models import Sale

from orders.constants import ACTIVE_MARKETPLACE_STATES

from orders.serializers import OrderSerializer
from orders.api.serializers import ProductStockSerializer

from analytics.services.sales import (
    sales_by_category,
    sales_by_day,
)
from analytics.services.forecast import (
    forecast_total,
    purchase_recommendation,
    product_forecast,
)
from analytics.services.cashflow import (
    cashflow_forecast,
    break_even_day,
    safe_purchase_limit,
)

from orders.dashboard import orders_dashboard_stats
from orders.finance_dashboard import finance_dashboard_stats
from orders.warehouse_dashboard import warehouse_dashboard_stats
from orders.sales_forecast import sales_forecast
from orders.cashflow_dashboard import cashflow_stats


# ==========================================================
# ORDERS API — ЕДИНАЯ ТОЧКА ИСТИНЫ
# ==========================================================

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Orders API

    /api/orders/            — все заказы (история)
    /api/orders/active/     — актуальные заказы (Kaspi states)
    /api/orders/new/        — новые заказы (Kaspi NEW)
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Базовый queryset — ВСЕ заказы
        Используется для истории и аналитики
        """
        return Order.objects.all().order_by("-created_at_source")

    @action(detail=False, methods=["get"], url_path="active")
    def active(self, request):
        """
        Актуальные заказы (рабочие)
        """
        qs = (
            Order.objects
            .filter(marketplace_state__in=ACTIVE_MARKETPLACE_STATES)
            .order_by("-created_at_source")
        )
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="new")
    def new(self, request):
        """
        Новые заказы (Kaspi NEW)
        Используется в правой панели
        """
        qs = (
            Order.objects
            .filter(marketplace_state="NEW")
            .order_by("-created_at_source")[:10]
        )
        return Response(self.get_serializer(qs, many=True).data)


# ==========================================================
# OWNER / MOBILE DASHBOARD
# ==========================================================

class OwnerDashboardAPIView(APIView):
    """
    Главный dashboard собственника / мобильного приложения
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = now().date()

        sales_today = (
            Sale.objects.filter(date=today)
            .aggregate(revenue=Sum("revenue"))["revenue"] or 0
        )

        sales_7d = (
            Sale.objects.filter(date__gte=today - timedelta(days=7))
            .aggregate(revenue=Sum("revenue"))["revenue"] or 0
        )

        sales_30d = (
            Sale.objects.filter(date__gte=today - timedelta(days=30))
            .aggregate(revenue=Sum("revenue"))["revenue"] or 0
        )

        supply = []
        for product in CatalogProduct.objects.all():
            qty = purchase_recommendation(product)
            if qty > 0:
                supply.append({
                    "sku": product.sku,
                    "name": product.name,
                    "qty": qty,
                })

        return Response({
            "sales": {
                "today": sales_today,
                "7d": sales_7d,
                "30d": sales_30d,
            },
            "forecast": {
                "30d": forecast_total(30),
                "90d": forecast_total(90),
            },
            "supply": supply,
        })


# ==========================================================
# OPERATIONS DASHBOARD
# ==========================================================

class OperationsDashboardAPIView(APIView):
    """
    Операционный dashboard (заказы, финансы, склад)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats, funnel = orders_dashboard_stats()
        finance_stats, top_products, worst_orders = finance_dashboard_stats()
        warehouse_rows = warehouse_dashboard_stats()
        forecast = sales_forecast()
        cashflow = cashflow_stats()

        return Response({
            "orders": {
                "stats": stats,
                "funnel": list(funnel),
            },
            "finance": {
                "stats": finance_stats,
                "top_products": list(top_products),
                "worst_orders": [
                    {
                        "order": o.order.code,
                        "net_profit": float(o.net_profit),
                        "margin": float(o.margin),
                    }
                    for o in worst_orders
                ],
            },
            "stock": warehouse_rows,
            "forecast": forecast,
            "cashflow": cashflow,
        })


# ==========================================================
# WAREHOUSE
# ==========================================================

class WarehouseAPIView(APIView):
    """
    Остатки + прогноз + рекомендации закупки
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rows = []

        for product in CatalogProduct.objects.all():
            stock_product = StockProduct.objects.filter(
                sku=product.sku
            ).first()

            stock = (
                WarehouseStock.objects
                .filter(product=stock_product)
                .values_list("quantity", flat=True)
                .first()
            ) or 0

            rows.append({
                "sku": product.sku,
                "name": product.name,
                "stock": stock,
                "forecast_14": product_forecast(product, 14),
                "recommended_purchase": purchase_recommendation(product),
            })

        return Response(rows)


# ==========================================================
# CASHFLOW
# ==========================================================

class CashflowAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "30d": cashflow_forecast(30),
            "90d": cashflow_forecast(90),
            "break_even_days": break_even_day(),
            "safe_purchase_limit": safe_purchase_limit(),
        })


# ==========================================================
# ANALYTICS
# ==========================================================

class SalesByCategoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(sales_by_category(30))


class SalesDailyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(sales_by_day(30))


# ==========================================================
# PRODUCT STOCK LIST
# ==========================================================

class ProductStockListView(APIView):
    """
    Список товаров с остатками
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = (
            StockProduct.objects
            .annotate(
                quantity=Coalesce(
                    F("stock__quantity"),
                    Value(0)
                )
            )
            .order_by("name")
        )

        return Response(
            ProductStockSerializer(products, many=True).data
        )
