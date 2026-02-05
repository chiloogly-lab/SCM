from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum

from .models import FinanceEvent


def cashflow_stats():
    now = timezone.now()
    next_7_days = now + timedelta(days=7)
    next_30_days = now + timedelta(days=30)

    inflow_7 = FinanceEvent.objects.filter(
        event_type=FinanceEvent.Type.INFLOW,
        planned_at__lte=next_7_days
    ).aggregate(s=Sum("amount"))["s"] or 0

    outflow_7 = FinanceEvent.objects.filter(
        event_type=FinanceEvent.Type.OUTFLOW,
        planned_at__lte=next_7_days
    ).aggregate(s=Sum("amount"))["s"] or 0

    inflow_30 = FinanceEvent.objects.filter(
        event_type=FinanceEvent.Type.INFLOW,
        planned_at__lte=next_30_days
    ).aggregate(s=Sum("amount"))["s"] or 0

    outflow_30 = FinanceEvent.objects.filter(
        event_type=FinanceEvent.Type.OUTFLOW,
        planned_at__lte=next_30_days
    ).aggregate(s=Sum("amount"))["s"] or 0

    return {
        "net_7": inflow_7 - outflow_7,
        "net_30": inflow_30 - outflow_30,
        "in_7": inflow_7,
        "out_7": outflow_7,
        "in_30": inflow_30,
        "out_30": outflow_30,
    }
