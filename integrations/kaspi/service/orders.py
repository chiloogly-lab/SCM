import logging
from datetime import timedelta, datetime

from django.utils import timezone

from integrations.kaspi.client import KaspiClient
from integrations.kaspi.constants import ORDERS_PAGE_SIZE
from integrations.kaspi.importer import KaspiOrderImporter
from integrations.models import IntegrationSyncState

logger = logging.getLogger(__name__)


class KaspiOrderImportService:
    """
    Надёжный delta-sync заказов Kaspi.
    С перекрытием временного окна, защитой от потерь и дубликатов.
    """

    OVERLAP_MINUTES = 5

    def __init__(self, integration):
        self.integration = integration
        self.client = KaspiClient(integration.api_token)
        self.importer = KaspiOrderImporter()

    def sync(self):
        state, _ = IntegrationSyncState.objects.get_or_create(
            integration=self.integration
        )

        # ✅ ТОЛЬКО Django timezone
        date_to = timezone.now()

        if state.last_success_sync:
            date_from = state.last_success_sync - timedelta(
                minutes=self.OVERLAP_MINUTES
            )
        else:
            date_from = date_to - timedelta(days=1)

        logger.warning(
            f"KASPI SYNC → {date_from.isoformat()} → {date_to.isoformat()}"
        )

        params = {
            "page[number]": 0,
            "page[size]": ORDERS_PAGE_SIZE,
            "filter[orders][creationDate][$ge]": ts(date_from),
            "filter[orders][creationDate][$le]": ts(date_to),
        }

        total = 0
        page = 0

        try:
            while True:
                params["page[number]"] = page

                data = self.client.get(
                    "/orders",
                    params=params,
                    timeout=20,
                )

                orders = data.get("data", [])

                if not orders:
                    break

                for payload in orders:
                    self.importer.import_order(payload)
                    total += 1

                page += 1

            state.last_success_sync = date_to
            state.last_error = ""
            state.last_attempt = timezone.now()
            state.save(
                update_fields=[
                    "last_success_sync",
                    "last_error",
                    "last_attempt",
                ]
            )

            logger.warning(f"KASPI SYNC DONE → imported: {total}")

        except Exception as e:
            state.last_error = str(e)
            state.last_attempt = timezone.now()
            state.save(update_fields=["last_error", "last_attempt"])
            logger.exception("KASPI SYNC ERROR")
            raise


# ============================================================
# ====================== HELPERS ==============================
# ============================================================

def ts(dt: datetime) -> int:
    """
    Преобразует datetime → timestamp (ms) для Kaspi API.
    Работает корректно с Django timezone.
    """
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)

    return int(dt.timestamp() * 1000)


def iter_orders(client, start, end):
    """
    Итератор заказов Kaspi с пагинацией.
    """
    page = 1

    while True:
        payload = client.get(
            "/orders",
            params={
                "filter[orders][creationDate][$ge]": ts(start),
                "filter[orders][creationDate][$le]": ts(end),
                "page[number]": page,
                "page[size]": 5,
            },
            timeout=20,
        )

        orders = payload.get("data", [])
        if not orders:
            break

        yield from orders
        page += 1
