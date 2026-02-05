from django.core.management.base import BaseCommand
from django.conf import settings
from datetime import datetime, timedelta, timezone
import time

from integrations.kaspi.client import KaspiClient
from integrations.kaspi.orders import iter_orders
from integrations.kaspi.entries import get_order_entries
from integrations.kaspi.products import get_entry_product

from orders.models import Order, OrderItem


class Command(BaseCommand):
    help = "Stable Kaspi import (orders → entries → products)"

    def handle(self, *args, **options):
        client = KaspiClient(settings.KASPI_API_TOKEN)

        end = datetime.now(tz=timezone.utc)
        start = end - timedelta(days=7)

        self.stdout.write("▶ Kaspi import started")

        for order_json in iter_orders(client, start, end):
            order, _ = Order.objects.update_or_create(
                external_id=order_json["id"],   # ❗ только ODA…
                defaults={
                    "code": order_json["attributes"]["code"],
                    "status": order_json["attributes"]["status"],
                    "total_price": order_json["attributes"]["totalPrice"],
                    "created_at": datetime.fromtimestamp(
                        order_json["attributes"]["creationDate"] / 1000,
                        tz=timezone.utc,
                    ),
                },
            )

            self.stdout.write(f"• Order {order.code}")

            entries = get_order_entries(client, order.external_id)

            for entry in entries:
                item, created = OrderItem.objects.get_or_create(
                    order=order,
                    external_id=entry["id"],
                )

                if not created and item.sku and item.name:
                    continue

                product = get_entry_product(client, entry["id"])
                if not product:
                    continue

                attrs = product["attributes"]

                item.sku = attrs.get("code")
                item.name = attrs.get("name")
                item.category = attrs.get("category")
                item.save()

                self.stdout.write(
                    f"  ↳ {item.sku} / {item.name}"
                )

                # дополнительная пауза для product
                time.sleep(0.6)

        self.stdout.write(self.style.SUCCESS("✔ Kaspi import completed"))
