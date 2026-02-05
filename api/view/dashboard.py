from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response

from analytics.models import Sale
from analytics.services.forecast import forecast_total, purchase_recommendation
from catalog.models import Product
from orders.models import Order
from django.db.models import Sum
from collections import OrderedDict
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count
from rest_framework.decorators import api_view

from analytics.models import Sale
from orders.models import Product, WarehouseStock
from django.db.models import F, Sum, DecimalField, ExpressionWrapper




class DashboardAPIView(APIView):

    def get(self, request):
        today = now().date()

        sales_today = Sale.objects.filter(date=today).aggregate(
            revenue=Sum("revenue")
        )["revenue"] or 0

        sales_7d = Sale.objects.filter(
            date__gte=today - timedelta(days=7)
        ).aggregate(revenue=Sum("revenue"))["revenue"] or 0

        sales_30d = Sale.objects.filter(
            date__gte=today - timedelta(days=30)
        ).aggregate(revenue=Sum("revenue"))["revenue"] or 0

        supply = []
        for product in Product.objects.all():
            qty = purchase_recommendation(product)
            if qty > 0:
                supply.append({
                    "sku": product.sku,
                    "name": product.name,
                    "qty": qty
                })

        return Response({
            "sales": {
                "today": sales_today,
                "7d": sales_7d,
                "30d": sales_30d
            },
            "forecast": {
                "30d": forecast_total(30),
                "90d": forecast_total(90)
            },
            "supply": supply
        })



@api_view(["GET"])
def dashboard_kpi(request):
    today = timezone.now().date()
    start_30 = today - timedelta(days=30)
    prev_30 = today - timedelta(days=60)

    sales_30 = Sale.objects.filter(
        date__gte=start_30
    )

    sales_prev_30 = Sale.objects.filter(
        date__gte=prev_30,
        date__lt=start_30
    )

    revenue_30 = sales_30.aggregate(
        total=Sum("revenue")
    )["total"] or 0

    revenue_prev = sales_prev_30.aggregate(
        total=Sum("revenue")
    )["total"] or 0

    revenue_diff = (
        ((revenue_30 - revenue_prev) / revenue_prev) * 100
        if revenue_prev else 0
    )

    sales_count_30 = sales_30.count()
    sales_count_prev = sales_prev_30.count()

    sales_diff = (
        ((sales_count_30 - sales_count_prev) / sales_count_prev) * 100
        if sales_count_prev else 0
    )

    sku_count = Product.objects.count()

    stock_value = WarehouseStock.objects.aggregate(
        total=Sum(
            ExpressionWrapper(
                F("quantity") * F("product__price"),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )
    )["total"] or 0

    return Response({
        "revenue_30d": float(revenue_30),
        "revenue_diff": round(revenue_diff, 1),
        "sales_30d": sales_count_30,
        "sales_diff": round(sales_diff, 1),
        "sku_count": sku_count,
        "stock_value": stock_value,
    })

@api_view(["GET"])
def dashboard_sales_weekly(request):
    today = timezone.now().date()
    start = today - timedelta(days=6)

    qs = (
        Sale.objects
        .filter(date__gte=start)
        .values("date")
        .annotate(total=Sum("qty"))
    )

    data = OrderedDict()
    for i in range(7):
        d = start + timedelta(days=i)
        data[d] = 0

    for row in qs:
        data[row["date"]] = row["total"]

    return Response({
        "labels": ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"],
        "values": list(data.values()),
    })


@api_view(["GET"])
def dashboard_last_orders(request):
    limit = int(request.GET.get("limit", 4))

    orders = (
        Order.objects
        .order_by("-created_at")[:limit]
    )

    return Response([
        {
            "id": o.external_id or o.code,
            "status": o.marketplace_status,
            "total": float(o.total_price),
        }
        for o in orders
    ])