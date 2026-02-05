from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum

from .models import OrderItem, WarehouseStock


def get_avg_daily_sales(product, days=14):
    since = timezone.now() - timedelta(days=days)

    sold = (
        OrderItem.objects
        .filter(
            sku=product.sku,
            order__created_at_source__gte=since
        )
        .aggregate(s=Sum("quantity"))["s"] or 0
    )

    return sold / days if days else 0


def get_days_left(product):
    try:
        stock = product.stock.quantity
    except WarehouseStock.DoesNotExist:
        return 0

    avg_sales = get_avg_daily_sales(product)

    if avg_sales == 0:
        return 999

    return round(stock / avg_sales, 1)
