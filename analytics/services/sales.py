from datetime import timedelta

from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils.timezone import now
from collections import defaultdict
from datetime import timedelta

from django.utils.timezone import now

from analytics.models import Sale
from analytics.models import Sale


def sales_by_category(days=30):
    qs = (
        Sale.objects
        .values("category")
        .annotate(
            revenue=Sum("revenue"),
            qty=Sum("qty")
        )
        .order_by("-revenue")
    )

    return [
        {
            "category": row["category"] or "Без категории",
            "revenue": float(row["revenue"] or 0),
            "qty": row["qty"] or 0,
        }
        for row in qs
    ]


def sales_by_day(days: int = 30):
    date_from = now().date() - timedelta(days=days)

    qs = (
        Sale.objects
        .filter(date__gte=date_from)
        .values("date", "revenue")
        .order_by("date")
    )

    daily = defaultdict(float)

    for row in qs:
        if row["date"] is None:
            continue
        daily[row["date"]] += float(row["revenue"] or 0)

    return [
        {
            "date": d.strftime("%Y-%m-%d"),
            "revenue": round(revenue, 2),
        }
        for d, revenue in sorted(daily.items())
    ]
