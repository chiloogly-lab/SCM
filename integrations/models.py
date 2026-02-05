from django.db import models

from integrations.kaspi.client import KaspiClient
from organizations.models import Store


class MarketplaceIntegration(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    marketplace = models.CharField(max_length=50)

    api_token = models.CharField(max_length=512)

    last_sync_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.store} → {self.marketplace}"

    def get_client(self):
        if self.marketplace == "kaspi":
            return KaspiClient(token=self.api_token)
        raise ValueError("Unsupported marketplace")


class IntegrationSyncState(models.Model):
    integration = models.OneToOneField(
        "integrations.MarketplaceIntegration",
        on_delete=models.CASCADE,
        related_name="sync_state",
    )
    last_success_sync = models.DateTimeField(null=True, blank=True)
    last_attempt = models.DateTimeField(auto_now=True)
    last_error = models.TextField(blank=True)

    def __str__(self):
        return f"IntegrationSyncState<{self.integration_id}>"


