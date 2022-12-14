from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductInventoryViewSet


app_name = "inventory"

router = DefaultRouter()
router.register("", ProductInventoryViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
