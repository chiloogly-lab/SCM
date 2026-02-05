from django.contrib import admin
from .models import MarketplaceIntegration


@admin.register(MarketplaceIntegration)
class MarketplaceIntegrationAdmin(admin.ModelAdmin):
    list_display = ("id", "store", "marketplace", "is_active", "last_sync_at")
    list_filter = ("marketplace", "is_active")
    search_fields = ("store__name", "marketplace")
from django.contrib import admin

# Register your models here.
