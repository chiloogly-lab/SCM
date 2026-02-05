from django.db import models
from django.utils import timezone


class Sale(models.Model):
    objects = None
    date = models.DateField(db_index=True)
    marketplace = models.CharField(max_length=32, default="kaspi", db_index=True)
    order_id = models.CharField(max_length=64, db_index=True)

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales"
    )

    sku = models.CharField(max_length=128, db_index=True)
    name = models.CharField(max_length=512)

    category = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        db_index=True
    )

    qty = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    revenue = models.DecimalField(max_digits=14, decimal_places=2)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["product"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["category"]),
        ]
        unique_together = ("order_id", "sku")

    def __str__(self):
        return f"{self.date} | {self.sku} | {self.qty}"


class DailyStat(models.Model):
    date = models.DateField(unique=True, db_index=True)
    orders = models.PositiveIntegerField(default=0)
    qty = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return str(self.date)
