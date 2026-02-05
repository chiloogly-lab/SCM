from decimal import Decimal, ROUND_HALF_UP

from finance.models import OrderFinanceSnapshot
from orders.models import Order


MARKETPLACE_FEE_PERCENT = Decimal("15")   # 15%
FACTORING_PERCENT = Decimal("8.5")         # 8.5%


def calculate_delivery_cost(total_price: Decimal) -> Decimal:
    if total_price < 1000:
        return Decimal("49.14")
    elif total_price < 3000:
        return Decimal("149.14")
    elif total_price < 5000:
        return Decimal("199.14")
    elif total_price < 10000:
        return Decimal("799.14")
    return Decimal("1299.14")


def calculate_order_finance(order: Order):
    total_price = Decimal(order.total_price)

    purchase_cost = sum(
        (item.purchase_price * item.quantity for item in order.items.all()),
        Decimal("0")
    )

    marketplace_fee = (total_price * MARKETPLACE_FEE_PERCENT / 100).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    factoring_fee = (total_price * FACTORING_PERCENT / 100).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    delivery_cost = calculate_delivery_cost(total_price)

    gross_profit = (total_price - purchase_cost).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    net_profit = (
        total_price
        - purchase_cost
        - marketplace_fee
        - factoring_fee
        - delivery_cost
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    margin = (
        (net_profit / total_price * 100).quantize(Decimal("0.01"))
        if total_price > 0 else Decimal("0")
    )

    finance, _ = OrderFinanceSnapshot.objects.update_or_create(
        order=order,
        defaults={
            "purchase_cost": purchase_cost,
            "marketplace_fee": marketplace_fee,
            "factoring_fee": factoring_fee,
            "delivery_cost": delivery_cost,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "margin": margin,
        }
    )

    return finance
