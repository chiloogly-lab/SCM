from django.core.management.base import BaseCommand
from integrations.models import MarketplaceIntegration
from integrations.kaspi.service.orders import KaspiOrderImportService


class Command(BaseCommand):
    help = "Sync orders from Kaspi"

    def handle(self, *args, **kwargs):
        integrations = MarketplaceIntegration.objects.filter(
            marketplace="Kaspi", is_active=True
        )

        for integration in integrations:
            self.stdout.write(f"Sync: {integration}")
            KaspiOrderImportService(integration).sync()
