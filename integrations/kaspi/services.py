import logging
from datetime import timedelta
from django.utils import timezone

from integrations.kaspi.client import KaspiClient
from integrations.kaspi.importer import KaspiOrderImporter
from integrations.kaspi.constants import (
    ORDERS_PAGE_SIZE,
    SYNC_LOOKBACK_MINUTES,
)
from system.models import Event


logger = logging.getLogger(__name__)


class KaspiOrderImportService:
    def __init__(self, integration):
        self.integration = integration
        self.client = KaspiClient(integration.api_token)
        self.importer = KaspiOrderImporter()

    def sync(self):
        date_to = timezone.now()
        date_from = date_to - timedelta(minutes=SYNC_LOOKBACK_MINUTES)

        logger.warning(
            f"[KASPI SYNC] {date_from.isoformat()} → {date_to.isoformat()}"
        )

        params = {
            "page[number]": 0,
            "page[size]": ORDERS_PAGE_SIZE,
            "filter[orders][creationDate][$ge]": int(date_from.timestamp() * 1000),
            "filter[orders][creationDate][$le]": int(date_to.timestamp() * 1000),
        }

        page = 0

        while True:
            params["page[number]"] = page

            data = self.client.get_orders(params=params)
            orders = data.get("data", [])

            logger.warning(f"[KASPI] Page {page}, orders: {len(orders)}")

            if not orders:
                break

            for raw_order in orders:
                self._process_order(raw_order)

            page += 1

    def _process_order(self, raw_order):
        event, _ = Event.objects.get_or_create(
            organization=self.integration.store.organization,
            type="kaspi.order.import",
            payload={
                "store_id": self.integration.store_id,
                "order": raw_order,
            },
        )

        self.importer.import_order(raw_order)
