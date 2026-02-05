from django.core.management.base import BaseCommand
from orders.models import Order
from orders.service import calculate_order_finance


class Command(BaseCommand):
    help = "Пересчитать финансовую аналитику по всем заказам"

    def handle(self, *args, **options):
        total = Order.objects.count()
        for i, order in enumerate(Order.objects.all(), start=1):
            calculate_order_finance(order)
            self.stdout.write(f"{i}/{total} пересчитан заказ {order.code}")
