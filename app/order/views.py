from rest_framework.response import Response
from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from drf_spectacular.utils import extend_schema
from django.db.models import Count, Sum, F
from sentry_sdk import capture_exception
from django.db import transaction
from inventory.models import ProductInventory
from .models import Cart, Customer, OrderItem, Order, Notification
from .serializers import (
    CartSerializer,
    CustomerDetailSerializer,
    CustomerListSerializer,
    OrderItemListSerializer,
    OrderSerializer,
    OrderListSerializer,
    OrderItemListSerializer,
    OrderCustomerSerializer,
    NotificationListSerializer,
    MarkASReadSerializer,
    ProductCartSerializer,
    ProductCartSerializer,
)
from order.models import Customer


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    filterset_fields = ["quantity"]
    search_fields = [
        "quantity",
        "product__name",
        "selling_price",
    ]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Cart.objects.filter(created_by=self.request.user)
        return queryset

    def get_response_data(self, queryset):
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(queryset, many=True)
        if page is not None:
            result = self.get_paginated_response(serializer.data)
            return result
        return serializer

    def create(self, request, *args, **kwargs):
        """Endpoint to create cart. To create a cart, add the product_id of the product you wish 
        to add to cart into the products list as demonstrated below.
        request body:
        {
            products=["3fa85f64-5717-4562-b3fc-2c963f66afa6"]
        }
        """
        try:
            user = request.user
            data = request.data
            products = data.get("products", None)
            with transaction.atomic():
                for product in products:
                    product_instance = ProductInventory.objects.get(pk=product)
                    # Product exists in cart
                    product_cart = Cart.objects.filter(product=product_instance).first()
                    if product_cart:
                        product_cart.add_to_cart()
                    # New Product
                    if product_cart is None:
                        if product_instance.current_quantity > 0:
                            Cart.objects.create_cart(
                                product=product_instance,
                                created_by=user,
                                selling_price=product_instance.selling_price,
                            )
            return Response(
                {
                    "success": True,
                    "message": "Successfully added to cart",
                    "errors": {},
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            capture_exception(e)
            return Response(
                {"success": False, "message": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, *args, **kwargs):
        try:
            pk = kwargs.get("pk")
            user = request.user
            item = Cart.objects.filter(pk=pk, created_by=user).first()
            if item is None:
                return Response(
                    {"message": "Item not in cart"}, status=status.HTTP_404_NOT_FOUND
                )
            product = item.product
            product.current_quantity = product.current_quantity + item.quantity
            product.save()
            item.delete()

            return Response(
                {"success": True, "message": "Item successfully removed"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            capture_exception(e)
            return Response(
                {"success": False, "message": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        try:
            user = request.user
            data = request.data
            pk = kwargs.get("pk", None)
            item = Cart.objects.get(id=pk, created_by=user)
            serializer = self.get_serializer(instance=item, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                
                return Response(
                    {"success": True, "message": "Quantity updated"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"success": False, "message": serializer.errors},
                status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            capture_exception(e)
            return Response(
                {"success": False, "message": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
   
    @action(methods=["GET"], detail=False, url_path="cart-details")
    def get_summary(self, request):
        try:
            data = self.get_queryset()
            if data:
                results = data.aggregate(
                    values=Sum("total_price"), items=Sum("quantity")
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


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerListSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    filterset_fields = [
        "customer_name",
    ]
    search_fields = ["customer_name", "customer_email", "customer_phone"]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Customer.objects.filter(created_by=self.request.user)
    
    def get_serializer_context(self):
        return {"request": self.request}
    
    def get_response_data(self, queryset):
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(queryset, many=True)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return result
        return serializer
    
    def create(self, request):
        """This endpoint for RETAILERS to create customers"""
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save(serializer.validated_data)
                
                return Response(
                    {"success": True, "message": "Customer created successfully"},
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
    
    def partial_update(self, request, pk=None):
        """This endpoint for RETAILERS to updates customers detail"""
        try:
            customer = Customer.objects.filter(created_by=request.user, pk=pk).first()
            serializer = CustomerDetailSerializer(
                customer,
                data=request.data,
                context={"request": request, "customer": self.kwargs.get("pk")},
            )
            if serializer.is_valid():
                serializer.update(customer, serializer.validated_data)
                
                return Response(
                    {
                        "success": True,
                        "message": "Customer details updated successfully",
                    },
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


class OrdersViewSet(viewsets.GenericViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderListSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    # filterset_class = OrderFilter
    search_fields = [
        "product__name",
    ]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Order.objects.filter(created_by=self.request.user)
        if self.action == "get_products" or self.action == "get_customers":
            return OrderItem.objects.filter(created_by=self.request.user)
        return queryset
    
    def get_serializer_context(self):
        return {"request": self.request}
    
    def get_response_data(self, queryset):
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(queryset, many=True)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            result = self.get_paginated_response(serializer.data)
            return result
        return serializer
    
    def get_serializer_class(self):
        if self.action == "create":
            return OrderSerializer
        return super().get_serializer_class()        
    
    def create(self, request):
        """This endpoint creates order items"""
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save(serializer.validated_data)
                return Response(
                    {"success": True, "message": "Order created successfully"},
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

    @extend_schema(responses={200: OrderItemListSerializer(many=True)})
    @action(
        methods=["GET"],
        detail=False,
        url_path="products",
        serializer_class=OrderItemListSerializer,
        permission_classes=[IsAuthenticated],
        filter_backends=[DjangoFilterBackend, filters.SearchFilter],
        search_fields=["product__name", "product__cost_price"],
        queryset=OrderItem.objects.all(),
    )
    def get_products(self, request):
        """This endpoint to get items sold"""
        try:
            qs = (
                self.get_queryset()
                .values("product_id", "selling_price")
                .annotate(
                    products=Count("product_id"),
                    qty=Sum("quantity"),
                    total_amount=Sum("total_price"),
                )
            )
            sales = self.filter_queryset(qs)
            return self.get_response_data(sales)
        except Exception as e:
            capture_exception(e)
            return Response(
                {"success": False, "message": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    @extend_schema(
        responses={200: OrderCustomerSerializer(many=True)}
    )
    @action(
        methods=["GET"],
        detail=False,
        url_path="customers/order-items",
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
    
    def get_customers(self, request):
        """This endpoint to get all cutomers and their product count and grand total"""
        try:
            qs = (
                self.get_queryset()
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


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationListSerializer
    http_method_names = ["get", "post"]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "text",
    ]
    search_fields = [
        "text",
    ]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(receiver=self.request.user)
        if self.action == "restock_notice":
            queryset = ProductInventory.objects.filter(created_by=self.request.user)
        return queryset
    
    def get_response_data(self, queryset):
        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(queryset, many=True)
        if page is not None:
            result = self.get_paginated_response(serializer.data)
            return result
        return serializer
    
    def get_serializer_class(self):
        return super().get_serializer_class()
    
    @action(
        methods=["POST"],
        detail=False,
        serializer_class=MarkASReadSerializer,
        url_path="(?P<id>[^/.]+)/mark-read",
        permission_classes=[IsAuthenticated],
    )
    def mark_read(self, request, pk=None):
        """This endpoint to mark as read notification"""
        try:
            notification = Notification.objects.filter(
                receiver=request.user, pk=pk
            ).first()
            serializer = NotificationListSerializer(
                instance=notification, data={"status": "READ"}, partial=True
            )
            if serializer.is_valid():
                serializer.update(notification, {"status": "READ"})
                return Response(
                    {"success": True, "message": "Notification updated successfully"},
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
    
    @extend_schema(responses={200: ProductCartSerializer(many=True)})
    @action(
        methods=["GET"],
        detail=False,
        serializer_class=ProductCartSerializer,
        url_path="restock-notice",
        permission_classes=[IsAuthenticated],
        filter_backends=[DjangoFilterBackend, filters.SearchFilter],
        search_fields=[
            "name",
        ],
        filterset_fields=[
            "name",
        ],
        queryset=ProductInventory.objects.all(),
    )
    def restock_notice(self, request, pk=None):
        """This endpoint to  get a list of paginated  restock notice product"""
        try:
            qs = self.get_queryset().filter(created_by=request.user, low_quantity=True)
            product = self.filter_queryset(qs)
            return self.get_response_data(product)
        
        except Exception as e:
            capture_exception(e)
            return Response(
                {"success": False, "message": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
