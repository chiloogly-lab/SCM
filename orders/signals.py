from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order, OrderItem
from .service import calculate_order_finance
from .cashflow_services import create_cashflow_events
from stock.services import deduct_stock_for_order


# 1️⃣ Создание заказа → финансы + cashflow
@receiver(post_save, sender=Order)
def on_order_created(sender, instance, created, **kwargs):
    if created:
        calculate_order_finance(instance)
        create_cashflow_events(instance)


# 2️⃣ Обновление заказа → только финансы
@receiver(post_save, sender=Order)
def on_order_updated(sender, instance, created, **kwargs):
    if not created:
        calculate_order_finance(instance)


# 3️⃣ Создание позиции → списание + финансы
@receiver(post_save, sender=OrderItem)
def on_order_item_created(sender, instance, created, **kwargs):
    if created:
        deduct_stock_for_order(instance.order)
        calculate_order_finance(instance.order)


# 4️⃣ Обновление позиции → только финансы
@receiver(post_save, sender=OrderItem)
def on_order_item_updated(sender, instance, created, **kwargs):
    if not created:
        calculate_order_finance(instance.order)
