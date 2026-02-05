from django.utils import timezone

from integrations.kaspi.importer import KaspiOrderImporter
from orders.models import Order


class KaspiOrderProcessor:
    def process(self, event):
        payload = event.payload

        raw = payload["order"]
        store_id = payload["store_id"]

        attrs = raw["attributes"]

        Order.objects.update_or_create(
            marketplace="kaspi",
            external_id=raw["id"],
            defaults={
                "store_id": store_id,
                "status": attrs.get("status"),
                "state": attrs.get("state"),
                "total_price": attrs.get("totalPrice", 0),
                "delivery_cost": attrs.get("deliveryCost", 0),
                "customer_name": (
                    f"{attrs.get('customer', {}).get('firstName', '')} "
                    f"{attrs.get('customer', {}).get('lastName', '')}"
                ).strip(),
                "customer_phone": attrs.get("customer", {}).get("cellPhone"),
                "raw_data": raw,
                "created_at": timezone.datetime.fromtimestamp(
                    attrs["creationDate"] / 1000, tz=timezone.utc
                ),
            },
        )


def import_order_from_kaspi(raw_order: dict):
    """
    Унифицированный импорт заказа Kaspi
    Используется Celery / backfill / ручным импортом
    """
    importer = KaspiOrderImporter()

    order, _ = importer.import_order(raw_order)

    items = raw_order.get("relationships", {}).get("entries", {}).get("data", [])
    if items:
        importer.import_items(order, items)

    return order