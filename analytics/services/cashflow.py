from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Sum

from analytics.models import Sale
from orders.models import FinanceEvent
from analytics.services.forecast import forecast_total
from decimal import Decimal



def cashflow_forecast(days=30):
    """
    Возвращает прогноз движения денег на N дней
    """
    today = now().date()

    # Исторический средний дневной оборот
    avg_daily_revenue = (
        Sale.objects
        .filter(date__gte=today - timedelta(days=30))
        .aggregate(v=Sum("revenue"))["v"] or 0
    ) / 30

    # Прогноз поступлений
    inflow = avg_daily_revenue * days

    # Запланированные выплаты
    outflow = (
        FinanceEvent.objects
        .filter(event_type="out", planned_at__date__lte=today + timedelta(days=days))
        .aggregate(v=Sum("amount"))["v"] or 0
    )

    return {
        "forecast_days": days,
        "avg_daily_revenue": round(avg_daily_revenue, 2),
        "expected_inflow": round(inflow, 2),
        "expected_outflow": round(outflow, 2),
        "net_cashflow": round(inflow - outflow, 2),
    }


def break_even_day():
    """
    Через сколько дней будет кассовый разрыв (если будет)
    """
    today = now().date()

    daily_revenue = (
        Sale.objects
        .filter(date__gte=today - timedelta(days=30))
        .aggregate(v=Sum("revenue"))["v"] or 0
    ) / 30

    balance = (
        FinanceEvent.objects
        .filter(event_type="in")
        .aggregate(v=Sum("amount"))["v"] or 0
    ) - (
        FinanceEvent.objects
        .filter(event_type="out")
        .aggregate(v=Sum("amount"))["v"] or 0
    )

    if daily_revenue <= 0:
        return None

    if balance >= 0:
        return None

    days = abs(balance) / daily_revenue
    return round(days, 1)


def safe_purchase_limit():
    """
    Максимальная безопасная сумма закупки
    """
    forecast = cashflow_forecast(30)

    if forecast["net_cashflow"] <= 0:
        return 0

    return (forecast["net_cashflow"] * Decimal("0.6")).quantize(Decimal("0.01"))
