#orders/models.py
from django.db import models
from django.utils import timezone
from django.apps import AppConfig
from django.dispatch import receiver
from django.db.models.signals import post_save
from finance.models import OrderFinanceSnapshot
import uuid






class Order(models.Model):
    class Source(models.TextChoices):
        KASPI = "kaspi", "Kaspi"
        OZON = "ozon", "Ozon"
        WB = "wb", "Wildberries"

    class Status(models.TextChoices):
        NEW = "new", "Новый"
        APPROVED = "approved", "Подтверждён"
        PACKING = "packing", "Сборка"
        SHIPPED = "shipped", "Отгружен"
        IN_TRANSIT = "in_transit", "В пути"
        DELIVERED = "delivered", "Доставлен"
        COMPLETED = "completed", "Завершён"
        CANCELLED = "cancelled", "Отменён"
        RETURNED = "returned", "Возврат"

    external_id = models.CharField(
        max_length=64,
        unique=True,
        default=uuid.uuid4,
        editable=False,
    )

    source = models.CharField(max_length=16, choices=Source.choices)

    code = models.CharField(max_length=64, db_index=True)

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
    )

    marketplace_status = models.CharField(
        max_length=64, db_index=True, default="unknown"
    )
    marketplace_state = models.CharField(
        max_length=64, db_index=True, default="unknown"
    )

    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    payment_mode = models.CharField(max_length=64, blank=True, null=True)
    delivery_mode = models.CharField(max_length=64, blank=True, null=True)

    is_express = models.BooleanField(default=False)
    is_preorder = models.BooleanField(default=False)
    signature_required = models.BooleanField(default=False)

    created_at_source = models.DateTimeField(default=timezone.now)
    approved_at_source = models.DateTimeField(blank=True, null=True)
    planned_delivery_at = models.DateTimeField(blank=True, null=True)

    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    raw_data = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["source", "external_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at_source"]),
        ]

    def __str__(self):
        return f"{self.source.upper()} #{self.code}"

    @property
    def is_new(self):
        return (
                self.marketplace_state == "NEW"
                and self.marketplace_status == "APPROVED_BY_BANK"
        )

    @property
    def is_active(self):
        return self.marketplace_state in [
            "NEW",
            "SIGN_REQUIRED",
            "PICKUP",
        ]

    @property
    def is_in_delivery(self):
        return self.marketplace_state in [
            "DELIVERY",
            "KASPI_DELIVERY",
        ]

    @property
    def is_analytics_ready(self):
        return self.status in [
            self.Status.DELIVERED,
            self.Status.COMPLETED,
        ]

    @property
    def is_closed(self):
        return self.status in {
            self.Status.DELIVERED,
            self.Status.COMPLETED,
            self.Status.CANCELLED,
            self.Status.RETURNED,
        }


# ============================================================
# ======================= ORDER ITEMS ========================
# ============================================================

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE
    )

    external_id = models.CharField(max_length=64, db_index=True)

    sku = models.CharField(
        max_length=128,
        db_index=True,
        blank=True,
        null=True,
    )

    name = models.CharField(
        max_length=512,
        blank=True,
        null=True,
    )

    quantity = models.PositiveIntegerField(default=1)

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )

    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Закупочная цена",
    )

    category = models.CharField(
        max_length=256,
        blank=True,
        null=True,
    )

    raw_data = models.JSONField(
        blank=True,
        null=True,
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="Товар"
    )

    class Meta:
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["external_id"]),
        ]

    def __str__(self):
        return f"{self.name or self.external_id} × {self.quantity}"



# ============================================================
# ======================= SNAPSHOTS ==========================
# ============================================================

class CustomerSnapshot(models.Model):
    order = models.OneToOneField(
        Order, related_name="customer", on_delete=models.CASCADE
    )

    external_id = models.CharField(max_length=64)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128, blank=True, null=True)
    phone = models.CharField(max_length=64)

    raw_data = models.JSONField()

    def __str__(self):
        return f"{self.first_name} {self.last_name or ''}".strip()


class DeliverySnapshot(models.Model):
    order = models.OneToOneField(
        Order, related_name="delivery", on_delete=models.CASCADE
    )

    city = models.CharField(max_length=128, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    pickup_point = models.CharField(max_length=128, blank=True, null=True)

    raw_data = models.JSONField()

    def __str__(self):
        return self.address or self.pickup_point or "Delivery"


# ============================================================
# ======================= STATUS HISTORY =====================
# ============================================================

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order, related_name="status_history", on_delete=models.CASCADE
    )

    status = models.CharField(max_length=32, choices=Order.Status.choices)
    source = models.CharField(max_length=32)  # kaspi / system / manual

    changed_at = models.DateTimeField(auto_now_add=True)

    raw_data = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["changed_at"]),
        ]

    def __str__(self):
        return f"{self.order} → {self.status}"


# ============================================================
# ======================= FINANCE MODEL ======================
# ============================================================


# ======================== Warehouse ========================

# catalog/models.py (или где у тебя Product)

class Product(models.Model):
    sku = models.CharField(max_length=128, unique=True)
    name = models.CharField(max_length=512)
    category = models.CharField(max_length=256, blank=True, null=True)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Цена продажи"
    )

    # === Kaspi ===
    kaspi_enabled = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Выгружать в Kaspi"
    )
    kaspi_category = models.CharField(
        max_length=256,
        blank=True,
        null=True,
        verbose_name="Категория Kaspi"
    )
    brand = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name="Бренд"
    )

    def __str__(self):
        return f"{self.sku} — {self.name}"


class WarehouseStock(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="stock")
    quantity = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product} → {self.quantity} шт"


class Supplier(models.Model):
    name = models.CharField(max_length=256)
    contact = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.name


class SupplyOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        ORDERED = "ordered", "Заказан"
        SHIPPED = "shipped", "Отгружен"
        RECEIVED = "received", "Получен"

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)

    created_at = models.DateTimeField(auto_now_add=True)
    expected_at = models.DateTimeField(blank=True, null=True)
    is_stock_applied = models.BooleanField(default=False)


    def __str__(self):
        return f"Supply #{self.id} → {self.supplier}"


class SupplyItem(models.Model):
    supply = models.ForeignKey(SupplyOrder, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="supply_items",
        verbose_name="Товар"
    )

    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product} × {self.quantity}"


@receiver(post_save, sender=SupplyOrder)
def increase_stock_on_supply(sender, instance, **kwargs):
    if instance.status != SupplyOrder.Status.RECEIVED:
        return

    if instance.is_stock_applied:
        return

    for item in instance.items.all():
        stock, _ = WarehouseStock.objects.get_or_create(
            product=item.product,
            defaults={"quantity": 0}
        )

        stock.quantity += item.quantity
        stock.save()

    instance.is_stock_applied = True
    instance.save(update_fields=["is_stock_applied"])


# ======================== Cashflow ========================

class FinanceEvent(models.Model):
    class Type(models.TextChoices):
        INFLOW = "in", "Поступление"
        OUTFLOW = "out", "Выплата"

    order = models.ForeignKey(
        Order, on_delete=models.SET_NULL, blank=True, null=True
    )

    event_type = models.CharField(max_length=8, choices=Type.choices)

    amount = models.DecimalField(max_digits=14, decimal_places=2)

    planned_at = models.DateTimeField()
    actual_at = models.DateTimeField(blank=True, null=True)

    description = models.CharField(max_length=256)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_event_type_display()} {self.amount} ₸"

@receiver(post_save, sender=Order)
def create_finance_snapshot(sender, instance, created, **kwargs):
    if created:
        OrderFinanceSnapshot.objects.create(order=instance)
