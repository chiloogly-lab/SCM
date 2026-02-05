from django.conf import settings
from django.db import transaction

from integrations.kaspi.client import KaspiClient
from orders.models import Order, OrderItem


def import_order_entries_for_existing_orders():
    """
    Импортирует entries + product для уже существующих заказов Kaspi.

    ВАЖНО:
    - Order.external_id  → Kaspi order id (ODAxxxx)
    - Order.code         → бизнес-номер заказа
    - OrderItem.external_id → Kaspi entry id (ODAxxx#0)

    Функция:
    - безопасна для повторного запуска
    - не создаёт дубликатов
    - не использует параллелизм
    """

    print("[KASPI] import_order_entries_for_existing_orders START")

    client = KaspiClient(settings.KASPI_API_TOKEN)

    orders = (
        Order.objects
        .filter(marketplace_status="ACCEPTED_BY_MERCHANT")
        .exclude(items__isnull=False)
        .distinct()
    )

    print(f"[KASPI] orders to process: {orders.count()}")

    for order in orders:
        if not order.external_id:
            print(f"[KASPI] skip order {order.code}: no external_id")
            continue

        print(f"[KASPI] processing order {order.code} ({order.external_id})")

        try:
            entries_response = client.get(
                f"/orders/{order.external_id}/entries"
            )
            entries = entries_response.get("data", [])
        except Exception as exc:
            print(
                f"[KASPI] ERROR fetching entries "
                f"for order {order.code}: {exc}"
            )
            continue

        print(f"[KASPI] entries found: {len(entries)}")

        for entry in entries:
            entry_id = entry.get("id")
            if not entry_id:
                print("[KASPI] skip entry without id")
                continue

            with transaction.atomic():
                item, created = OrderItem.objects.get_or_create(
                    order=order,
                    external_id=entry_id,
                )

                # если уже обогащён — не дёргаем API
                if not created and item.sku and item.name:
                    print(
                        f"[KASPI] item already exists "
                        f"{item.sku} / {item.name}"
                    )
                    continue

                try:
                    product_response = client.get(
                        f"/orderentries/{entry_id}/product"
                    )
                    product = product_response.get("data")
                except Exception as exc:
                    print(
                        f"[KASPI] ERROR fetching product "
                        f"for entry {entry_id}: {exc}"
                    )
                    continue

                if not product:
                    print(f"[KASPI] empty product for entry {entry_id}")
                    continue

                attrs = product.get("attributes", {})

                item.sku = attrs.get("code")
                item.name = attrs.get("name")
                item.category = attrs.get("category")
                item.save()

                print(
                    f"[KASPI] product saved: "
                    f"{item.sku} / {item.name}"
                )

    print("[KASPI] import_order_entries_for_existing_orders DONE")
