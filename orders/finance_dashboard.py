from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Avg, F, ExpressionWrapper, DecimalField

from .models import OrderFinanceSnapshot, OrderItem


def finance_dashboard_stats():
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now - timedelta(days=30)

    stats = {
        "profit_today": OrderFinanceSnapshot.objects.filter(
            order__created_at_source__gte=today_start
        ).aggregate(s=Sum("net_profit"))["s"] or 0,

        "profit_month": OrderFinanceSnapshot.objects.filter(
            order__created_at_source__gte=month_start
        ).aggregate(s=Sum("net_profit"))["s"] or 0,

        "revenue_month": OrderFinanceSnapshot.objects.filter(
            order__created_at_source__gte=month_start
        ).aggregate(s=Sum("order__total_price"))["s"] or 0,

        "avg_margin": OrderFinanceSnapshot.objects.filter(
            order__created_at_source__gte=month_start
        ).aggregate(a=Avg("margin"))["a"] or 0,
    }

    top_products = (
        OrderItem.objects
        .annotate(
            profit=ExpressionWrapper(
                (F("unit_price") - F("purchase_price")) * F("quantity"),
                output_field=DecimalField()
            )
        )
        .values("name")
        .annotate(total_profit=Sum("profit"))
        .order_by("-total_profit")[:10]
    )

    worst_orders = (
        OrderFinanceSnapshot.objects
        .select_related("order")
        .order_by("net_profit")[:10]
    )

    return stats, top_products, worst_orders
