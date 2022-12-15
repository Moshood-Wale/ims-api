from rest_framework.response import Response
from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser
from sentry_sdk import capture_exception
from drf_spectacular.utils import extend_schema
from django.db.models import Sum
from .models import ProductInventory
from order.models import OrderItem
from django.db.models import Count, Sum
from order.serializers import OrderCustomerSerializer
from .serializers import (
    ProductInventorySerializer,
    ProductListInventorySerializer,
    RestockProductSerializer,
)
from django.db.models import F


class ProductInventoryViewSet(viewsets.ModelViewSet):
    queryset = ProductInventory.objects.all()
    serializer_class = ProductInventorySerializer
    http_method_names = ["get", "post", "patch", "delete"]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    permission_classes = [IsAuthenticated]
    search_fields = [
        "name",
        "cost_price",
        "selling_price",
        "current_quantity",
        "default_quantity",
        "minimum_stock_quantity",
    ]
    ordering_fields = ["name", "quantity", "selling_price", "cost_price"]
    
    def get_queryset(self):
        user = self.request.user
        queryset = ProductInventory.objects.filter(created_by=user)
        if self.action == "customers":
            return OrderItem.objects.filter(created_by=user)
        return queryset
    
    def get_response_data(self, queryset):
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(queryset, many=True)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return result
        return serializer
    
    @extend_schema(
        responses={200: ProductInventorySerializer(many=True)}
    )
    def list(self, request):
        try:
            data = self.get_queryset()
            serializer = ProductListInventorySerializer(data, many=True)
            data = self.filter_queryset(data)
            page = self.paginate_queryset(data)
            if page is not None:
                serializer = ProductListInventorySerializer(page, many=True)
                results = self.get_paginated_response(serializer.data)
                return Response(
                    {"success": True, "result": results.data}, status=status.HTTP_200_OK
                )
            return Response(
                {"success": False, "error": serializer.errors},
                status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            capture_exception(e)
            return Response(
                {"success": False, "message": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def retrieve(self, request, *args, **kwargs):
        try:
            pk = kwargs.get("pk")
            user = request.user
            item = ProductInventory.objects.get(pk=pk, created_by=user)
            serializer = ProductListInventorySerializer(item, many=False)
            if serializer.data:
                return Response(
                    {"success": True, "result": serializer.data, "errors": {}},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"success": False, "error": serializer.errors},
                status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            capture_exception(e)
            return Response(
                {"success": False, "message": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @action(methods=["GET"], detail=False, url_path="summary")
    def get_summary(self, request):
        try:
            data = self.get_queryset()
            if data:
                results = data.aggregate(
                    items=Sum("current_quantity"), values=Sum("selling_price")
                )
                return Response(results, status=status.HTTP_200_OK)
            return Response(
                {"success": False, "error": "Product not found"},
                status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            capture_exception(e)
            return Response(
                {"success": False, "message": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        methods=["PATCH"],
        detail=True,
        serializer_class=RestockProductSerializer,
        url_path="restock",
    )
    def restock(self, request, pk=None):
        try:
            user = request.user
            data = request.data
            product_obj = ProductInventory.objects.get(id=pk, created_by=user)
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                restock_quantity = data.get("quantity", 0)
                product_obj.restock(int(restock_quantity))
                product_obj.save()
                return Response(
                    {"success": True, "result": serializer.data, "errors": {}},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"success": False, "error": serializer.errors},
                status.HTTP_400_BAD_REQUEST,
            )
        except serializers.ValidationError as e:
            return Response(
                {"success": False, "error": e.detail[0]}, status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            capture_exception(e)
            return Response(
                {"success": False, "message": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @extend_schema(responses={200: OrderCustomerSerializer(many=True)})
    @action(
        methods=["GET"],
        detail=True,
        serializer_class=OrderCustomerSerializer,
        permission_classes=[IsAuthenticated],
        filter_backends=[DjangoFilterBackend, filters.SearchFilter],
        search_fields=[
            "order__customer__customer_name",
            "order__customer__customer_email",
            "order__customer__customer_phone",
            "product__name",
        ],
        queryset=OrderItem.objects.all(),
    )
    def customers(self, request, pk=None):
        """This endpoint to gets all cutomers that ordered a particular product and the quantity"""
        try:
            qs = (
                self.get_queryset()
                .filter(product=pk)
                .values("order__customer")
                .annotate(
                    num_customer=Count("order"),
                    total_amount=Sum("total_price"),
                    product_quantity=Sum("quantity"),
                )
            )
            customers = self.filter_queryset(qs)
            return self.get_response_data(customers)
        except Exception as e:
            capture_exception(e)
            return Response(
                {"success": False, "message": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
