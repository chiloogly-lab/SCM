from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "purchase_price", "is_active")
    search_fields = ("sku", "name")
    list_filter = ("category", "is_active")
