from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count

from .models import Order


def get_sales_stats(days):
    since = timezone.now() - timedelta(days=days)

    qs = Order.objects.filter(
        created_at_source__gte=since,
        status__in=[
            Order.Status.DELIVERED,
            Order.Status.COMPLETED
        ]
    )

    total_orders = qs.count()
    revenue = qs.aggregate(s=Sum("total_price"))["s"] or 0

    avg_orders_per_day = total_orders / days if days else 0
    avg_revenue_per_day = revenue / days if days else 0

    return {
        "orders": total_orders,
        "revenue": revenue,
        "avg_orders_per_day": avg_orders_per_day,
        "avg_revenue_per_day": avg_revenue_per_day
    }


def sales_forecast():
    stats_7 = get_sales_stats(7)
    stats_14 = get_sales_stats(14)
    stats_30 = get_sales_stats(30)

    forecast = {
        "7d": {
            "orders": round(stats_7["avg_orders_per_day"] * 7, 1),
            "revenue": round(stats_7["avg_revenue_per_day"] * 7, 0)
        },
        "14d": {
            "orders": round(stats_14["avg_orders_per_day"] * 14, 1),
            "revenue": round(stats_14["avg_revenue_per_day"] * 14, 0)
        },
        "30d": {
            "orders": round(stats_30["avg_orders_per_day"] * 30, 1),
            "revenue": round(stats_30["avg_revenue_per_day"] * 30, 0)
        },
    }

    return forecast
