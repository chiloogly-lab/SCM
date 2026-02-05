from django.db import models

class Product(models.Model):
    sku = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        verbose_name="SKU / Артикул"
    )

    name = models.CharField(
        max_length=512,
        verbose_name="Название товара"
    )

    category = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="Категория"
    )

    supplier = models.ForeignKey(
        "orders.Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Поставщик"
    )

    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Закупочная цена"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )

    sale_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Цена продажи"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return f"{self.sku} — {self.name}"


    kaspi_enabled = models.BooleanField(default=False)
    kaspi_category = models.CharField(max_length=256, blank=True, null=True)
    brand = models.CharField(max_length=128, blank=True, null=True)