from django.urls import path
from admin_ui.view.dashboard import dashboard
from admin_ui.view.orders import orders_list

app_name = "admin_ui"

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("orders/", orders_list, name="orders"),
]
