from django.contrib import admin
from .models import Stock


@admin.register(Stock)
class WarehouseStockAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "min_quantity", "updated_at")
    search_fields = ("product__sku", "product__name")
