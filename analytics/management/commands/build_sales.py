from django.core.management.base import BaseCommand
from django.db import transaction

from analytics.models import Sale
from orders.models import Order


class Command(BaseCommand):
    help = "Build sales from kaspi archive orders"

    @transaction.atomic
    def handle(self, *args, **options):
        Sale.objects.all().delete()

        orders = Order.objects.filter(
            source="kaspi",
            marketplace_status="Выдан",
        ).prefetch_related("items", "items__product")

        created = 0
        skipped = 0

        for order in orders:
            # ✅ ТОЛЬКО ИСТОРИЧЕСКАЯ ДАТА
            sale_dt = order.delivered_at or order.created_at_source

            if not sale_dt:
                skipped += 1
                continue

            sale_date = sale_dt.date()

            for item in order.items.all():
                Sale.objects.create(
                    date=sale_date,
                    marketplace=order.source,
                    order_id=order.external_id or order.code,
                    product=item.product,
                    sku=item.sku,
                    name=item.name,
                    category=item.category,
                    qty=item.quantity,
                    price=item.unit_price,
                    revenue=item.total_price,
                    created_at=sale_dt,
                )
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sales rebuilt: {created}, skipped orders: {skipped}"
            )
        )
