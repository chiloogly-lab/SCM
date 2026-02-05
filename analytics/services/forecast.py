from orders.models import WarehouseStock, Product as StockProduct
from catalog.models import Product as CatalogProduct
from datetime import timedelta
from django.utils.timezone import now
from django.db.models import Sum
from analytics.models import Sale




def forecast_total(days=30):
    today = now().date()

    base = Sale.objects.filter(
        date__gte=today - timedelta(days=30)
    ).aggregate(qty=Sum("qty"))["qty"] or 0

    avg = base / 30

    return round(avg * days)


def product_forecast(product, days=14):
    today = now().date()

    total = Sale.objects.filter(
        product=product,
        date__gte=today - timedelta(days=30)
    ).aggregate(qty=Sum("qty"))["qty"] or 0

    avg = total / 30

    return round(avg * days)


def purchase_recommendation(product: CatalogProduct):
    """
    product — catalog.Product
    склад работает через orders.Product, поэтому связываем по SKU
    """

    forecast_14 = product_forecast(product, 14)

    stock_product = StockProduct.objects.filter(
        sku=product.sku
    ).first()

    if not stock_product:
        return round(forecast_14 * 1.3)

    stock = (
        WarehouseStock.objects
        .filter(product=stock_product)
        .values_list("quantity", flat=True)
        .first()
    ) or 0

    safety = forecast_14 * 0.3

    return max(0, round(forecast_14 + safety - stock))