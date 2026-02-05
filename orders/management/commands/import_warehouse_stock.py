import pandas as pd
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from orders.models import Product, WarehouseStock


class Command(BaseCommand):
    help = "Import warehouse stock and prices from Excel file"

    def add_arguments(self, parser):
        parser.add_argument(
            "file",
            type=str,
            help="Path to stock Excel file (.xlsx)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options["file"]

        df = pd.read_excel(file_path)
        df = df.fillna("")

        created_products = 0
        updated_products = 0
        updated_stocks = 0
        updated_prices = 0

        stock_columns = ["PP1", "PP2", "PP3", "PP4", "PP5"]

        for _, row in df.iterrows():
            sku = str(row.get("SKU", "")).strip()
            if not sku:
                continue

            name = str(row.get("model", "")).strip()

            # =========================
            # СЧИТАЕМ ОСТАТОК
            # =========================
            qty = 0

            for col in stock_columns:
                raw = row.get(col)

                if raw in ("", None):
                    continue

                try:
                    if pd.isna(raw):
                        continue

                    raw_str = str(raw).strip().lower()

                    # пропускаем yes / no и прочий мусор
                    if raw_str in ("yes", "no"):
                        continue

                    raw_str = raw_str.replace(",", ".")
                    value = float(raw_str)

                    qty += int(value)

                except Exception:
                    self.stderr.write(
                        f"⚠️ Bad qty value: SKU={sku}, {col}={raw}"
                    )

            # =========================
            # PRODUCT
            # =========================
            product, created = Product.objects.get_or_create(
                sku=sku,
                defaults={"name": name or sku},
            )

            if created:
                created_products += 1
            else:
                updated_products += 1

            # обновляем имя, если изменилось
            if name and product.name != name:
                product.name = name
                product.save(update_fields=["name"])

            # =========================
            # PRICE (КЛЮЧЕВО!)
            # =========================
            raw_price = row.get("price")

            if raw_price not in ("", None):
                try:
                    price = Decimal(str(raw_price).replace(",", "."))
                    if price >= 0 and product.price != price:
                        product.price = price
                        product.save(update_fields=["price"])
                        updated_prices += 1
                except Exception:
                    self.stderr.write(
                        f"⚠️ Bad price value: SKU={sku}, price={raw_price}"
                    )

            # =========================
            # WAREHOUSE STOCK
            # =========================
            WarehouseStock.objects.update_or_create(
                product=product,
                defaults={"quantity": qty},
            )
            updated_stocks += 1

        self.stdout.write(self.style.SUCCESS(
            "\nWarehouse import finished\n"
            f"Products created: {created_products}\n"
            f"Products updated: {updated_products}\n"
            f"Prices updated: {updated_prices}\n"
            f"Stocks updated: {updated_stocks}"
        ))
