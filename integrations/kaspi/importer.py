from datetime import timezone as dt_timezone
from django.utils import timezone

from orders.models import (
    Order,
    OrderItem,
    CustomerSnapshot,
    DeliverySnapshot,
    OrderStatusHistory,
)


class KaspiOrderImporter:

    def import_order(self, payload: dict):
        data = payload["attributes"]

        order, created = Order.objects.update_or_create(
            external_id=payload["id"],
            defaults={
                "source": Order.Source.KASPI,
                "code": data.get("code"),

                # 🔹 ВАЖНО: корректное маппинг-поле
                "status": self._map_status(data.get("status")),
                "marketplace_status": data.get("status"),
                "marketplace_state": data.get("state"),

                "total_price": data.get("totalPrice", 0),
                "delivery_cost": data.get("deliveryCost", 0),
                "payment_mode": data.get("paymentMode"),
                "delivery_mode": data.get("deliveryMode"),

                "is_express": data.get("kaspiDelivery", {}).get("express", False),
                "is_preorder": data.get("preOrder", False),
                "signature_required": data.get("signatureRequired", False),

                "created_at_source": self._ts(data.get("creationDate")),
                "approved_at_source": self._ts(data.get("approvedByBankDate")),
                "planned_delivery_at": self._ts(data.get("plannedDeliveryDate")),

                "raw_data": payload,
            }
        )

        self._sync_customer(order, data.get("customer"))
        self._sync_delivery(order, data.get("originAddress"))
        self._sync_status(order)

        return order, created

    def import_items(self, order: Order, entries: list):
        order.items.all().delete()

        for entry in entries:
            attr = entry["attributes"]

            OrderItem.objects.create(
                order=order,
                external_id=entry["id"],
                sku=attr["offer"]["code"],
                name=attr["offer"]["name"],
                quantity=attr["quantity"],
                unit_price=attr["basePrice"],
                total_price=attr["totalPrice"],
                category=attr.get("category", {}).get("title"),
                raw_data=entry,
            )

    # ===================== HELPERS =====================

    def _sync_customer(self, order, customer):
        if not customer:
            return

        CustomerSnapshot.objects.update_or_create(
            order=order,
            defaults={
                "external_id": customer.get("id"),
                "first_name": customer.get("firstName"),
                "last_name": customer.get("lastName"),
                "phone": customer.get("cellPhone"),
                "raw_data": customer,
            }
        )

    def _sync_delivery(self, order, origin):
        if not origin:
            return

        addr = origin.get("address", {})

        DeliverySnapshot.objects.update_or_create(
            order=order,
            defaults={
                "city": origin.get("city", {}).get("name"),
                "address": addr.get("formattedAddress"),
                "latitude": addr.get("latitude"),
                "longitude": addr.get("longitude"),
                "pickup_point": origin.get("displayName"),
                "raw_data": origin,
            }
        )

    def _sync_status(self, order):
        last = order.status_history.first()
        if not last or last.status != order.status:
            OrderStatusHistory.objects.create(
                order=order,
                status=order.status,
                changed_at=timezone.now(),
                raw_data={"source": "kaspi"},
            )

    def _ts(self, ts):
        if not ts:
            return None
        return timezone.datetime.fromtimestamp(
            ts / 1000,
            tz=dt_timezone.utc
        )

    def _map_status(self, kaspi_status: str) -> str:
        """
        Приводим статусы Kaspi к нашим бизнес-статусам
        """
        mapping = {
            "NEW": "new",
            "APPROVED": "approved",
            "PACKING": "packing",
            "SHIPPED": "shipped",
            "DELIVERED": "delivered",
            "CANCELLED": "cancelled",
            "RETURNED": "returned",
        }
        return mapping.get(kaspi_status, "new")
