import pandas as pd
from decimal import Decimal
from datetime import datetime, time

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from orders.models import Order, OrderItem, Product


class Command(BaseCommand):
    help = "Import Kaspi archive orders from Excel file"

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            type=str,
            help="Path to Kaspi archive Excel file (.xlsx)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options["file"]

        df = pd.read_excel(file_path)
        df = df.fillna("")

        created_orders = 0
        skipped_orders = 0
        created_items = 0
        skipped_no_date = 0

        for _, row in df.iterrows():
            order_external_id = str(row.get("№ заказа", "")).strip()
            if not order_external_id:
                continue

            # =========================
            # DATE (ИЗ EXCEL)
            # =========================
            parsed_date = None
            for col in (
                "Дата поступления заказа",
                "Дата заказа",
                "Дата оформления",
                "Дата создания заказа",
                "Дата и время заказа",
                "Дата",
            ):
                if col in row and row.get(col):
                    parsed_date = self.parse_datetime(row.get(col))
                    if parsed_date:
                        break

            if not parsed_date:
                self.stderr.write(
                    f"⚠️ No date for order {order_external_id}, row skipped"
                )
                skipped_no_date += 1
                continue

            created_at_source = parsed_date

            # =========================
            # ORDER
            # =========================
            order, created = Order.objects.get_or_create(
                external_id=order_external_id,
                source="kaspi",
                defaults={
                    "code": order_external_id,
                    "status": "imported",
                    "marketplace_status": row.get("Статус", ""),
                    "total_price": self.decimal(row.get("Сумма")),
                    "delivery_cost": self.decimal(
                        row.get("Стоимость доставки для продавца")
                    ),
                    "payment_mode": "",
                    "delivery_mode": row.get("Способ доставки", ""),
                    "is_express": False,
                    "is_preorder": False,
                    "signature_required": False,

                    # 🔥 ИСТОРИЧЕСКАЯ ДАТА
                    "created_at_source": created_at_source,
                    "delivered_at": created_at_source,

                    "raw_data": row.to_dict(),
                },
            )

            if created:
                created_orders += 1
            else:
                skipped_orders += 1

            # =========================
            # ORDER ITEM
            # =========================
            sku = str(row.get("Артикул", "")).strip()
            if not sku:
                continue

            quantity = int(row.get("Количество") or 1)
            total_price = self.decimal(row.get("Сумма"))
            unit_price = (
                total_price / quantity if quantity else Decimal("0")
            )

            product = Product.objects.filter(sku=sku).first()

            if OrderItem.objects.filter(order=order, sku=sku).exists():
                continue

            OrderItem.objects.create(
                order=order,
                external_id=f"{order_external_id}:{sku}",
                sku=sku,
                name=row.get("Название в системе продавца", ""),
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                purchase_price=Decimal("0"),
                category=row.get("Категория", ""),
                product=product,
                raw_data=row.to_dict(),
            )

            created_items += 1

        self.stdout.write(self.style.SUCCESS(
            "\nImport finished successfully\n"
            f"Orders created: {created_orders}\n"
            f"Orders skipped (existing): {skipped_orders}\n"
            f"Orders skipped (no date): {skipped_no_date}\n"
            f"Order items created: {created_items}"
        ))

    # =========================
    # HELPERS
    # =========================

    def parse_datetime(self, value):
        """
        Convert Excel value to timezone-aware datetime.
        Supports:
        - pandas Timestamp
        - datetime
        - DD.MM.YYYY
        - DD.MM.YYYY HH:MM
        """
        if not value:
            return None

        # pandas Timestamp
        if hasattr(value, "to_pydatetime"):
            dt = value.to_pydatetime()

        # already datetime
        elif isinstance(value, datetime):
            dt = value

        # string formats
        elif isinstance(value, str):
            value = value.strip()
            if not value:
                return None

            dt = None
            for fmt in (
                "%d.%m.%Y %H:%M",
                "%d.%m.%Y",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
            ):
                try:
                    dt = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue

            if not dt:
                return None
        else:
            return None

        # если дата без времени — ставим 00:00
        if isinstance(dt, datetime) and dt.time() == time(0, 0):
            dt = datetime.combine(dt.date(), time.min)

        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)

        return dt

    def decimal(self, value):
        try:
            return Decimal(str(value)) if value != "" else Decimal("0")
        except Exception:
            return Decimal("0")
