from decimal import Decimal, ROUND_HALF_UP
from finance.models import OrderFinanceSnapshot


MARKETPLACE_FEE_PERCENT = Decimal("15")
FACTORING_PERCENT = Decimal("8.5")


def calculate_delivery_cost(total_price: Decimal, weight=0) -> Decimal:
    total_price = Decimal(total_price)

    if total_price < 1000:
        return Decimal("49.14")
    elif total_price < 3000:
        return Decimal("149.14")
    elif total_price < 5000:
        return Decimal("199.14")
    elif total_price < 10000:
        return Decimal("799.14")

    if weight <= 5:
        return Decimal("1299.14")
    elif weight <= 15:
        return Decimal("1699.14")
    elif weight <= 30:
        return Decimal("3599.14")
    elif weight <= 60:
        return Decimal("5649.14")
    elif weight <= 100:
        return Decimal("8549.14")
    else:
        return Decimal("11999.14")


def calculate_order_finance(order: Order):
    purchase_cost = sum(
        (i.purchase_price * i.quantity for i in order.items.all()),
        Decimal("0")
    )

    total_price = Decimal(order.total_price)

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
        (net_profit / total_price * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if total_price else Decimal("0")
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


MARKETPLACE_COMMISSION = Decimal("0.15")   # 15%
FACTORING_RATE = Decimal("0.085")          # 8.5%


def calculate_delivery_cost(total_price: Decimal) -> Decimal:
    """
    Тарифная сетка доставки (пример — заменим на твою таблицу)
    """
    if total_price < 5000:
        return Decimal("1200")
    elif total_price < 10000:
        return Decimal("1500")
    elif total_price < 20000:
        return Decimal("1800")
    return Decimal("2000")


def calculate_order_finance(order):
    total = Decimal(order.total_price)

    marketplace_fee = total * MARKETPLACE_COMMISSION
    factoring_fee = total * FACTORING_RATE
    delivery_cost = calculate_delivery_cost(total)

    # TODO: заменим на реальную себестоимость из склада
    purchase_cost = Decimal("0")

    gross_profit = total - purchase_cost
    net_profit = total - (
        purchase_cost + marketplace_fee + factoring_fee + delivery_cost
    )

    margin = (
        (net_profit / total) * 100
        if total > 0 else Decimal("0")
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