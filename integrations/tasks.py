import time
import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from orders.models import Order, OrderItem
from integrations.kaspi.client import KaspiClient
from integrations.kaspi.service.orders import iter_orders
from integrations.kaspi.entries import get_order_entries
from integrations.kaspi.products import get_entry_product

logger = logging.getLogger(__name__)


# ==========================================================
# STATUS RESOLVER — ЕДИНСТВЕННЫЙ ИСТОЧНИК ИСТИНЫ
# ==========================================================

def resolve_order_status(attrs: dict) -> str:
    """
    Определяем бизнес-статус заказа ТОЛЬКО по факту,
    а не по документации.
    """

    marketplace_status = attrs.get("status")
    marketplace_state = attrs.get("state")
    kaspi_delivery = attrs.get("kaspiDelivery") or {}

    # факт передачи в доставку
    is_transferred = (
        kaspi_delivery.get("waybillNumber") is not None
        or kaspi_delivery.get("courierTransmissionDate") is not None
    )

    # 1️⃣ Архив / финал
    if marketplace_state == "ARCHIVE":
        if marketplace_status == "COMPLETED":
            return Order.Status.COMPLETED
        if marketplace_status in ("CANCELLED", "CANCELLING"):
            return Order.Status.CANCELLED
        if marketplace_status in (
            "RETURNED",
            "KASPI_DELIVERY_RETURN_REQUESTED",
        ):
            return Order.Status.RETURNED

    # 2️⃣ Передан в доставку
    if is_transferred:
        return Order.Status.IN_TRANSIT

    # 3️⃣ Всё остальное — НОВЫЙ заказ
    return Order.Status.NEW


# ==========================================================
# ARCHIVE IMPORT (one-time)
# ==========================================================

@shared_task(
    bind=True,
    name="kaspi.import.archive",
    autoretry_for=(Exception,),
    retry_backoff=120,
    retry_kwargs={"max_retries": 5},
)
def import_kaspi_archive(self, days=180):
    """
    Полный архивный импорт (1 раз при подключении магазина)
    """

    logger.warning("[KASPI][ARCHIVE] import started")

    client = KaspiClient(settings.KASPI_API_TOKEN)

    end = timezone.now()
    start = end - timedelta(days=days)

    cursor = start
    chunk_size = 14

    while cursor < end:
        chunk_end = min(cursor + timedelta(days=chunk_size), end)

        logger.warning(
            f"[KASPI][ARCHIVE] chunk {cursor.date()} → {chunk_end.date()}"
        )

        _import_orders(
            client=client,
            start=cursor,
            end=chunk_end,
        )

        cursor = chunk_end
        time.sleep(2)

    logger.warning("[KASPI][ARCHIVE] import finished")


# ==========================================================
# ACTIVE ORDERS (periodic)
# ==========================================================

@shared_task(
    bind=True,
    name="kaspi.import.active",
    autoretry_for=(Exception,),
    retry_backoff=30,
    retry_kwargs={"max_retries": 3},
)
def import_kaspi_active(self):
    """
    Актуальные заказы:
    - новые
    - переданные в доставку
    """

    logger.info("[KASPI][ACTIVE] sync started")

    client = KaspiClient(settings.KASPI_API_TOKEN)

    end = timezone.now()
    start = end - timedelta(days=14)

    _import_orders(
        client=client,
        start=start,
        end=end,
        skip_archive=True,
    )

    logger.info("[KASPI][ACTIVE] sync finished")


# ==========================================================
# NEW ORDERS (frequent polling)
# ==========================================================

@shared_task(
    bind=True,
    name="kaspi.import.new",
    acks_late=True,
)
def import_kaspi_new(self):
    """
    Частый импорт:
    ТОЛЬКО заказы, НЕ переданные в доставку
    """

    logger.info("[KASPI][NEW] polling")

    client = KaspiClient(settings.KASPI_API_TOKEN)

    end = timezone.now()
    start = end - timedelta(hours=6)

    _import_orders(
        client=client,
        start=start,
        end=end,
        only_new=True,
    )


# ==========================================================
# CORE IMPORT
# ==========================================================

def _import_orders(
    client,
    start,
    end,
    only_new=False,
    skip_archive=False,
):
    for order_json in iter_orders(client, start, end):
        attrs = order_json["attributes"]

        marketplace_state = attrs.get("state")
        kaspi_delivery = attrs.get("kaspiDelivery") or {}

        is_transferred = (
            kaspi_delivery.get("waybillNumber") is not None
            or kaspi_delivery.get("courierTransmissionDate") is not None
        )

        # фильтры
        if skip_archive and marketplace_state == "ARCHIVE":
            continue

        if only_new and is_transferred:
            continue

        created_at = timezone.make_aware(
            datetime.fromtimestamp(attrs["creationDate"] / 1000)
        )

        status = resolve_order_status(attrs)

        order, _ = Order.objects.update_or_create(
            external_id=order_json["id"],
            defaults={
                "source": Order.Source.KASPI,
                "code": attrs.get("code"),
                "status": status,
                "marketplace_status": attrs.get("status"),
                "marketplace_state": marketplace_state,
                "total_price": attrs.get("totalPrice"),
                "created_at_source": created_at,
                "raw_data": order_json,
            },
        )

        logger.info(
            f"[KASPI] {order.code} → {order.status}"
        )

        _import_entries(client, order)


# ==========================================================
# ENTRIES
# ==========================================================

def _import_entries(client, order):
    entries = get_order_entries(client, order.external_id)

    for entry in entries:
        attrs = entry["attributes"]

        item, _ = OrderItem.objects.get_or_create(
            order=order,
            external_id=entry["id"],
            defaults={
                "quantity": attrs.get("quantity", 1),
                "raw_data": entry,
            },
        )

        if item.sku and item.unit_price:
            continue

        time.sleep(0.4)

        product = get_entry_product(client, entry["id"])
        if not product:
            continue

        pattrs = product["attributes"]
        unit_price = pattrs.get("price") or pattrs.get("basePrice")

        item.sku = pattrs.get("code")
        item.name = pattrs.get("name")
        item.category = pattrs.get("category")
        item.unit_price = unit_price
        item.total_price = unit_price * item.quantity if unit_price else None
        item.raw_data = {
            "entry": entry,
            "product": product,
        }
        item.save()

        time.sleep(0.5)
