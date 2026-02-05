import time
import requests

from celery import shared_task
from django.conf import settings

from orders.models import Order, OrderItem


KASPI_BASE_URL = "https://kaspi.kz/shop/api/v2"


def kaspi_headers():
    return {
        "Authorization": f"Bearer {settings.KASPI_API_TOKEN}",
        "Accept": "application/vnd.api+json",
    }


def fetch_with_retry(url, headers, timeout=30, retries=3, sleep=2):
    """
    Запрос с retry и backoff.
    Используем ТОЛЬКО для Kaspi product endpoint.
    """
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.ReadTimeout as exc:
            print(
                f"[Kaspi product retry {attempt}/{retries}] "
                f"timeout: {url}"
            )
            if attempt == retries:
                raise
            time.sleep(sleep)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=60, retry_kwargs={"max_retries": 2})
def import_kaspi_order_entries_task(self):
    """
    Импортирует СОСТАВ заказов Kaspi:
    - /orders/{id}/entries
    - /orderentries/{entry_id}/product

    Работает ТОЛЬКО для новых подтверждённых заказов
    """

    headers = kaspi_headers()

    orders = Order.objects.filter(
        marketplace_status="ACCEPTED_BY_MERCHANT"
    ).exclude(
        items__isnull=False
    )

    print(f"[Kaspi entries import] Orders to process: {orders.count()}")

    for order in orders:
        print(f"\n[Kaspi entries import] Order {order.code}")

        try:
            # ─────────────────────────────────────
            # 1️⃣ Получаем ENTRIES заказа
            # ─────────────────────────────────────
            entries_url = (
                f"{KASPI_BASE_URL}/orders/"
                f"{order.external_id}/entries"
            )

            print("ENTRIES URL:", entries_url)

            r = requests.get(entries_url, headers=headers, timeout=15)
            r.raise_for_status()

            entries_data = r.json().get("data", [])

            print(f"Entries count: {len(entries_data)}")

            if not entries_data:
                print("⚠ Entries list is empty")
                continue

            for entry in entries_data:
                entry_id = entry.get("id")

                # 🔴 КЛЮЧЕВОЙ DEBUG
                print("ENTRY ID:", entry_id)

                if not entry_id:
                    print("❌ entry_id is empty, skip")
                    continue

                attrs = entry.get("attributes", {})

                item, created = OrderItem.objects.get_or_create(
                    order=order,
                    external_id=entry_id,
                    defaults={
                        "quantity": attrs.get("quantity", 1),
                        "unit_price": attrs.get("price", 0),
                        "total_price": attrs.get("price", 0),
                    },
                )

                # если товар уже обогащён — не дёргаем API
                if not created and item.sku and item.name:
                    print("✓ Item already exists, skip product fetch")
                    continue

                # небольшая пауза — Kaspi это любит
                time.sleep(0.4)

                # ─────────────────────────────────────
                # 2️⃣ Получаем PRODUCT для entry
                # ─────────────────────────────────────
                product_url = (
                    f"{KASPI_BASE_URL}/orderentries/"
                    f"{entry_id}/product"
                )

                print("PRODUCT URL:", product_url)

                pr = fetch_with_retry(
                    product_url,
                    headers=headers,
                    timeout=45,
                    retries=3,
                )

                product_attrs = (
                    pr.json()
                    .get("data", {})
                    .get("attributes", {})
                )

                item.sku = product_attrs.get("code")
                item.name = product_attrs.get("name")
                item.save()

                print(
                    f"✓ Product saved: "
                    f"{item.sku} / {item.name}"
                )

        except Exception as exc:
            print(
                f"[Kaspi entries import] "
                f"Order {order.code} ERROR: {exc}"
            )
            continue
