from django.urls import path, include
from rest_framework.routers import DefaultRouter
# 👉 ВАЖНО: импорт именно из api.view
from api.views import OrderViewSet
# 👉 Web / admin view
from orders.serializers import OrderSerializer

from orders.views import generate_supply_view

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="orders")


urlpatterns = [
    # API
    path("api/", include(router.urls)),

    # Admin / service view
    path("generate-supply/", generate_supply_view, name="generate_supply"),
]
