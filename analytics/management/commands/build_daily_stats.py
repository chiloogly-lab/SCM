from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate

from analytics.models import Sale, DailyStat


class Command(BaseCommand):
    help = "Build daily aggregated stats"

    def handle(self, *args, **options):
        data = (
            Sale.objects
            .annotate(
                day=TruncDate("created_at")  # 🔥 КЛЮЧЕВОЙ ФИКС
            )
            .values("day")
            .annotate(
                qty=Sum("qty"),
                revenue=Sum("revenue"),
                orders=Count("order_id", distinct=True),
            )
            .order_by("day")
        )

        for row in data:
            DailyStat.objects.update_or_create(
                date=row["day"],
                defaults={
                    "qty": row["qty"] or 0,
                    "revenue": row["revenue"] or 0,
                    "orders": row["orders"] or 0,
                },
            )

        self.stdout.write(
            self.style.SUCCESS("Daily stats updated")
        )
