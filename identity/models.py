from django.conf import settings
from django.db import models
from organizations.models import Organization


class UserOrganization(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    role = models.CharField(max_length=50, default="admin")

    class Meta:
        unique_together = ("user", "organization")
