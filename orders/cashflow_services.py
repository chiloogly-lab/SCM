from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
from .models import FinanceEvent, Order


FACTORING_PERCENT = Decimal("8.5")


def create_cashflow_events(order: Order):
    """
    Создаёт денежные события по заказу:
    - поступление денег
    - списание факторинга
    """

    now = timezone.now()

    # 1️⃣ Ожидаем поступление денег (через 3 дня)
    inflow_date = now + timedelta(days=3)

    FinanceEvent.objects.get_or_create(
        order=order,
        event_type=FinanceEvent.Type.INFLOW,
        defaults={
            "amount": order.total_price,
            "planned_at": inflow_date,
            "description": f"Оплата заказа {order.code}",
        }
    )

    # 2️⃣ Факторинг — списание сразу
    total_price = Decimal(order.total_price)
    factoring_fee = (total_price * FACTORING_PERCENT) / Decimal("100")

    FinanceEvent.objects.get_or_create(
        order=order,
        event_type=FinanceEvent.Type.OUTFLOW,
        description=f"Факторинг по заказу {order.code}",
        defaults={
            "amount": factoring_fee,
            "planned_at": now,
        }
    )
