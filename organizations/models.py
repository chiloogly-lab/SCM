from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Organization(models.Model):
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True, null=True)
    bin = models.CharField(max_length=20, blank=True, null=True)

    timezone = models.CharField(max_length=64, default="Asia/Almaty")
    currency = models.CharField(max_length=10, default="KZT")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Store(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="stores"
    )

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)

    city = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organization.name} — {self.name}"
