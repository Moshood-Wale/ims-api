from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet, CustomerViewSet, OrdersViewSet, NotificationViewSet


app_name = "order"

router = DefaultRouter()
router.register("cart", CartViewSet)
router.register("cart", CustomerViewSet)
router.register("cart", NotificationViewSet)
router.register("", OrdersViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
