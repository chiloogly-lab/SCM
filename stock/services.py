from .models import Stock
from .autoreorder import check_and_create_supply_order



def deduct_stock_for_order(order):
    for item in order.items.select_related("product"):
        if not item.product:
            continue

        stock, _ = Stock.objects.get_or_create(
            product=item.product,
            defaults={"quantity": 0}
        )

        stock.quantity -= item.quantity
        stock.save()

        check_and_create_supply_order(stock)

