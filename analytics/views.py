from datetime import timedelta
from django.shortcuts import render
from django.utils.timezone import now
from django.db.models import Sum

from analytics.models import Sale, DailyStat
from analytics.services.forecast import forecast_total, purchase_recommendation
from catalog.models import Product


def dashboard(request):
    today = now().date()

    sales_today = Sale.objects.filter(date=today).aggregate(
        qty=Sum("qty"),
        revenue=Sum("revenue")
    )

    sales_7d = Sale.objects.filter(
        date__gte=today - timedelta(days=7)
    ).aggregate(qty=Sum("qty"), revenue=Sum("revenue"))

    sales_30d = Sale.objects.filter(
        date__gte=today - timedelta(days=30)
    ).aggregate(qty=Sum("qty"), revenue=Sum("revenue"))

    forecast_30 = forecast_total(30)
    forecast_90 = forecast_total(90)

    products = []
    for product in Product.objects.all():
        rec = purchase_recommendation(product)
        if rec > 0:
            products.append({
                "product": product,
                "recommendation": rec
            })

    context = {
        "sales_today": sales_today,
        "sales_7d": sales_7d,
        "sales_30d": sales_30d,
        "forecast_30": forecast_30,
        "forecast_90": forecast_90,
        "products": products,
    }

    return render(request, "analytics/dashboard.html", context)
