from orders.models import Order

KASPI_STATUS_MAP = {
    # Банк / принятие
    "APPROVED_BY_BANK": Order.Status.NEW,
    "ACCEPTED_BY_MERCHANT": Order.Status.APPROVED,

    # Доставка
    "DELIVERY": Order.Status.SHIPPED,
    "KASPI_DELIVERY": Order.Status.IN_TRANSIT,

    # Финал
    "COMPLETED": Order.Status.COMPLETED,
    "CANCELLED": Order.Status.CANCELLED,
    "RETURNED": Order.Status.RETURNED,
}
