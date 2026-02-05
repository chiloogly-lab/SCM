from math import ceil

from .models import Product, SupplyOrder, SupplyItem
from .warehouse_services import get_avg_daily_sales, get_days_left


def generate_auto_supply(supplier, target_days=14):
    """
    Формирует автоматический заказ поставщику,
    чтобы хватило товара на target_days вперёд
    """

    supply = SupplyOrder.objects.create(supplier=supplier)

    for product in Product.objects.all():
        avg_sales = get_avg_daily_sales(product)
        days_left = get_days_left(product)

        if days_left < target_days:
            need = ceil(avg_sales * (target_days - days_left))

            if need > 0:
                SupplyItem.objects.create(
                    supply=supply,
                    product=product,
                    quantity=need,
                    purchase_price=0
                )

    return supply
