from django.db import models


class Stock(models.Model):
    product = models.OneToOneField(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="stock",
        verbose_name="Товар",
    )

    quantity = models.IntegerField(
        default=0,
        verbose_name="Остаток на складе",
    )

    min_quantity = models.IntegerField(
        default=0,
        verbose_name="Минимальный остаток",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Складской остаток"
        verbose_name_plural = "Складские остатки"

    def __str__(self):
        return f"{self.product} → {self.quantity}"
