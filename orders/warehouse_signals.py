from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SupplyOrder, SupplyItem


from .models import OrderItem, Product, WarehouseStock


@receiver(post_save, sender=OrderItem)
def decrease_stock_on_sale(sender, instance, created, **kwargs):
    """
    Автоматически списывает остаток со склада при продаже товара
    """
    if not created:
        return

    product, _ = Product.objects.get_or_create(
        sku=instance.sku,
        defaults={
            "name": instance.name,
            "category": instance.category,
        }
    )


    stock, _ = WarehouseStock.objects.get_or_create(
        product=product,
        defaults={"quantity": 0}
    )

    stock.quantity -= instance.quantity
    stock.save()



@receiver(post_save, sender=SupplyOrder)
def increase_stock_on_supply(sender, instance, **kwargs):
    """
    Автоматически приходует товар при получении поставки
    """
    if instance.status != SupplyOrder.Status.RECEIVED:
        return

    for item in instance.items.all():
        stock, _ = WarehouseStock.objects.get_or_create(
            product=item.product,
            defaults={"quantity": 0}
        )

        stock.quantity += item.quantity
        stock.save()
