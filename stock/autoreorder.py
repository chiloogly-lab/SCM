from .models import Stock
from orders.models import SupplyOrder, SupplyItem
from django.utils import timezone


def check_and_create_supply_order(stock: Stock):
    """
    Если остаток ниже минимума → создаём заказ поставщику
    """
    if stock.quantity >= stock.min_quantity:
        return

    product = stock.product

    # Проверяем: нет ли уже активного заказа на этот товар
    if SupplyItem.objects.filter(
        product=product,
        supply__status="new"
    ).exists():
        return

    supplier = getattr(product, "supplier", None)
    if not supplier:
        return

    order = SupplyOrder.objects.create(
        supplier=supplier,
        status="new",
        created_at=timezone.now()
    )

    SupplyItem.objects.create(
        supply=order,
        product=product,
        quantity=max(stock.min_quantity * 2, 10),
        purchase_price=product.purchase_price
    )
