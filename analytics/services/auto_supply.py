from orders.models import SupplyOrder, SupplyItem, Supplier
from catalog.models import Product
from analytics.services.forecast import purchase_recommendation


def generate_supply_order(supplier: Supplier):
    """
    Генерирует заказ поставщику на основе прогноза и остатков
    """
    items = []

    for product in Product.objects.all():
        qty = purchase_recommendation(product)

        if qty > 0:
            items.append((product, qty))

    if not items:
        return None

    supply = SupplyOrder.objects.create(
        supplier=supplier,
        status=SupplyOrder.Status.DRAFT
    )

    for product, qty in items:
        SupplyItem.objects.create(
            supply=supply,
            product=product,
            quantity=qty,
            purchase_price=0  # заполнишь после
        )

    return supply
