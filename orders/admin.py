from django.contrib import admin
from django.utils.html import format_html
from django.contrib.admin import site
from finance.models import OrderFinanceSnapshot


from .models import (
    Order,
    OrderItem,
    CustomerSnapshot,
    DeliverySnapshot,
    OrderStatusHistory,
    Product,
    WarehouseStock,
    Supplier,
    SupplyOrder,
    SupplyItem,
    OrderFinanceSnapshot,
)

from orders.finance_dashboard import finance_dashboard_stats
from orders.warehouse_dashboard import warehouse_dashboard_stats
from orders.sales_forecast import sales_forecast
from orders.cashflow_dashboard import cashflow_stats


# ======================== Warehouse ========================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category')
    search_fields = ('sku', 'name', 'category')


@admin.register(WarehouseStock)
class WarehouseStockAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'updated_at')
    search_fields = ('product__sku', 'product__name')


# ======================== Supply ========================

class SupplyItemInline(admin.TabularInline):
    model = SupplyItem
    extra = 0


@admin.register(SupplyOrder)
class SupplyOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'status', 'created_at')
    inlines = (SupplyItemInline,)
    list_filter = ('status', 'supplier')
    date_hierarchy = 'created_at'


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact')
    search_fields = ('name',)


# ======================== Order Inlines ========================

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    min_num = 0
    can_delete = True


class CustomerInline(admin.StackedInline):
    model = CustomerSnapshot
    extra = 0
    can_delete = False


class DeliveryInline(admin.StackedInline):
    model = DeliverySnapshot
    extra = 0
    can_delete = False


class StatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('status', 'source', 'changed_at')
    ordering = ('-changed_at',)


class FinanceInline(admin.StackedInline):
    model = OrderFinanceSnapshot
    extra = 0
    can_delete = False
    readonly_fields = (
        'purchase_cost',
        'marketplace_fee',
        'factoring_fee',
        'delivery_cost',
        'gross_profit',
        'net_profit',
        'margin',
    )


# ======================== Order Admin ========================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'source',
        'code',
        'colored_status',
        'total_price',
        'delivery_cost',
        'created_at_source',
    )

    list_filter = (
        'source',
        'status',
        'created_at_source',
    )

    search_fields = (
        'external_id',
        'code',
        'marketplace_status',
        'marketplace_state',
        'customer__first_name',
        'customer__last_name',
        'customer__phone',
    )

    readonly_fields = (
        'external_id',
        'created_at',
        'updated_at',
        'marketplace_status',
        'marketplace_state',
    )

    date_hierarchy = 'created_at_source'

    list_per_page = 50

    inlines = (
        CustomerInline,
        DeliveryInline,
        OrderItemInline,
        StatusHistoryInline,
        FinanceInline,
    )

    def colored_status(self, obj):
        colors = {
            'new': '#6c757d',
            'approved': '#0d6efd',
            'packing': '#fd7e14',
            'shipped': '#6f42c1',
            'in_transit': '#20c997',
            'delivered': '#198754',
            'completed': '#14532d',
            'cancelled': '#dc3545',
            'returned': '#a94442',
        }
        color = colors.get(obj.status, '#000')
        return format_html(
            '<b style="color:{}">{}</b>',
            color,
            obj.get_status_display()
        )

    colored_status.short_description = 'Статус'


# ======================== Order Item Admin ========================

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'sku',
        'name',
        'quantity',
        'unit_price',
        'total_price',
    )
    search_fields = ('sku', 'name')
    list_filter = ('category',)


# ======================== Status History ========================

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'source', 'changed_at')
    list_filter = ('status', 'source')
    ordering = ('-changed_at',)


# ======================== Admin Dashboard ========================

old_each_context = site.each_context


def custom_each_context(request):
    ctx = old_each_context(request)

    stats, top_products, worst_orders = finance_dashboard_stats()
    warehouse_rows = warehouse_dashboard_stats()
    forecast = sales_forecast()

    ctx["cashflow"] = cashflow_stats()
    ctx["sales_forecast"] = forecast
    ctx["warehouse_rows"] = warehouse_rows
    ctx["finance_stats"] = stats
    ctx["top_products"] = top_products
    ctx["worst_orders"] = worst_orders

    return ctx


site.each_context = custom_each_context
