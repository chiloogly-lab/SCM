from celery import shared_task
from analytics.management.commands.build_sales import Command as BuildSales
from analytics.management.commands.build_daily_stats import Command as BuildStats
from analytics.services.auto_supply import generate_supply_order
from orders.models import Supplier


@shared_task
def rebuild_analytics():
    """
    Перестраивает аналитику из заказов
    """
    BuildSales().handle()
    BuildStats().handle()
    return "analytics updated"


@shared_task
def auto_supply():
    """
    Автоматически формирует заказы поставщикам
    """
    created = []
    for supplier in Supplier.objects.all():
        order = generate_supply_order(supplier)
        if order:
            created.append(order.id)
    return created
