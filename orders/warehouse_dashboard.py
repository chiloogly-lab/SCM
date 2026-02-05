from .models import Product
from .warehouse_services import get_avg_daily_sales, get_days_left


def warehouse_dashboard_stats():
    rows = []

    for product in Product.objects.all():
        avg_sales = round(get_avg_daily_sales(product), 2)
        days_left = get_days_left(product)

        try:
            stock = product.stock.quantity
        except:
            stock = 0

        rows.append({
            "sku": product.sku,
            "name": product.name,
            "stock": stock,
            "avg_sales": avg_sales,
            "days_left": days_left,
            "is_critical": days_left < 7
        })

    return rows
