from django.urls import path, include
from rest_framework.routers import DefaultRouter
from catalog.serializers.kaspi_product import KaspiProductViewSet
from catalog.view.kaspi_feed import kaspi_feed

router = DefaultRouter()
router.register(
    r"api/kaspi/products",
    KaspiProductViewSet,
    basename="kaspi-products"
)

urlpatterns = [
    path("", include(router.urls)),
    path("kaspi/feed.xml", kaspi_feed, name="kaspi-feed"),
]
