import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from catalog.models import Product
from stock.models import Stock


class Command(BaseCommand):
    help = "Импорт товаров из Kaspi XML"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str)

    def handle(self, *args, **options):
        tree = ET.parse(options["file"])
        root = tree.getroot()

        offers = root.find("offers")
        if offers is None:
            self.stdout.write(self.style.WARNING("Нет offers"))
            return

        created, updated = 0, 0

        for offer in offers.findall("offer"):
            sku = offer.attrib.get("sku")
            name = offer.findtext("model", "")
            price = offer.findtext("price", "0")
            quantity = offer.findtext("quantity", "0")
            category = offer.findtext("category")

            product, is_created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": category,
                    "purchase_price": price,
                    "kaspi_enabled": True,
                }
            )

            Stock.objects.update_or_create(
                product=product,
                defaults={"quantity": int(quantity)},
            )

            created += int(is_created)
            updated += int(not is_created)

        self.stdout.write(
            self.style.SUCCESS(
                f"Импорт завершён. Создано: {created}, обновлено: {updated}"
            )
        )
