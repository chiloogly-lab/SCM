from django.db import models
from organizations.models import Organization


class Event(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="events"
    )

    type = models.CharField(max_length=100)
    payload = models.JSONField()

    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        default="pending",
    )

    error = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.type} ({self.status})"
