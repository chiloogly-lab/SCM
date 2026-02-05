from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from orders.models import Order

@login_required
def orders_list(request):
    qs = Order.objects.all().select_related().prefetch_related("items")

    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    return render(request, "admin_ui/orders/list.html", {
        "orders": qs[:50],
    })
