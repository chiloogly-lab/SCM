from django.db import models


class OrderFinanceSnapshot(models.Model):
    order = models.OneToOneField(
        "orders.Order",
        related_name="finance",
        on_delete=models.CASCADE,
    )

    purchase_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    marketplace_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    factoring_fee = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    delivery_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )

    gross_profit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    net_profit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    margin = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Finance #{self.order.code}"
