from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg

from .models import Order


def orders_dashboard_stats():
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)

    stats = {
        "today": Order.objects.filter(created_at_source__gte=today_start).count(),
        "week": Order.objects.filter(created_at_source__gte=last_7_days).count(),
        "month": Order.objects.filter(created_at_source__gte=last_30_days).count(),

        "revenue_today": Order.objects.filter(
            created_at_source__gte=today_start
        ).aggregate(s=Sum("total_price"))["s"] or 0,

        "revenue_month": Order.objects.filter(
            created_at_source__gte=last_30_days
        ).aggregate(s=Sum("total_price"))["s"] or 0,

        "avg_check": Order.objects.filter(
            created_at_source__gte=last_30_days
        ).aggregate(a=Avg("total_price"))["a"] or 0,

        "active_orders": Order.objects.exclude(
            status__in=[
                Order.Status.COMPLETED,
                Order.Status.CANCELLED,
                Order.Status.RETURNED,
            ]
        ).count(),
    }

    funnel = Order.objects.values("status").annotate(c=Count("id"))

    return stats, funnel
