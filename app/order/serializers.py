from rest_framework import serializers
from .models import Cart, Customer, Order, OrderItem, Notification
from .utils import sanitize_phone_number
from email_validator import validate_email, EmailNotValidError
from django.db import transaction
from inventory.models import ProductInventory
from inventory.serializers import ProductInventorySerializer
from django.db.models import Sum
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
import datetime


class ProductCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInventory
        fields = "__all__"


class CartSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product.name")
    quantity = serializers.IntegerField(default=1)
    current_quantity = serializers.IntegerField(source="product.current_quantity")
    selling_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, source="product.selling_price"
    )
    cost_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, source="product.cost_price"
    )
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    product = serializers.SerializerMethodField("get_product", read_only=True)
    
    class Meta:
        model = Cart
        fields = (
            "id",
            "name",
            "selling_price",
            "cost_price",
            "total_price",
            "current_quantity",
            "quantity",
            "product",
        )
        extra_kwargs = {
            "id": {"read_only": True},
        }
    
    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)    
    
    def update(self, instance, validated_data):
        data = self.context["request"].data
        new_cart_quantity = data.get("quantity", None)
        product = instance.product
        
        if new_cart_quantity:
            current_cart_quantity = instance.quantity
            diff = new_cart_quantity - current_cart_quantity
            if (
                diff <= product.current_quantity
                and new_cart_quantity <= product.default_quantity
            ):
                instance.quantity = new_cart_quantity
                product.current_quantity = product.current_quantity - diff
                product.save()
            else:
                raise serializers.ValidationError("Quantity is low")
    
        if product.current_quantity <= product.minimum_stock_quantity:
            product.low_quantity = True
        else:
            product.low_quantity = False
        product.save()
        instance = super().update(instance, data)
        instance.refresh_from_db()
        return instance
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_product(self, obj):
        product = ProductInventory.objects.filter(id=obj.product_id).first()
        serializers = ProductCartSerializer(product)
        return serializers.data


class CustomerListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Customer
        exclude = ("created_by",)
        extra_kwargs = {
            "created_by": {"read_only": True},
        }
    
    def validate(self, attrs):
        email = attrs.get("customer_email", None)
        phone = attrs.get("customer_phone", None)
        name = attrs.get("customer_name", None)
        user = self.context["request"].user

        if not phone:
            attrs["customer_phone"] = "None"
        if not email:
            attrs["customer_email"] = "None"
        if not name:
            attrs["customer_name"] = "Anonymous"
        
        qs = Customer.objects.filter(created_by=user)
        if email:
            try:
                email = validate_email(email.lower().strip()).email
            except EmailNotValidError as e:
                raise serializers.ValidationError("Email not valid")
            if qs.filter(customer_email=email).exists():
                raise serializers.ValidationError("Customer with email already exists")
            if not name:
                raise serializers.ValidationError(
                    "Customer name is required"
                )
            attrs["customer_email"] = email
        
        if phone:
            phone_number = sanitize_phone_number(phone)
            if isinstance(phone_number, dict):
                raise serializers.ValidationError({"phone": phone_number["message"]})
            if qs.filter(customer_phone=phone_number).exists():
                raise serializers.ValidationError(
                    "Account with phone number already exists"
                )
            if qs.filter(customer_phone=phone_number).exists():
                raise serializers.ValidationError(
                    "Customer with phone number already exists"
                )
            if not name:
                raise serializers.ValidationError(
                    "Customer name is required")
            attrs["customer_phone"] = phone_number
        
        if name:
            attrs["customer_name"] = name.capitalize()
            if qs.filter(customer_name=name.capitalize()).exists():
                raise serializers.ValidationError("Customer with name already exists")
        return super().validate(attrs)
    
    def save(self, validated_data):
        user = self.context["request"].user
        customer = Customer.objects.get_or_create(
            **validated_data, defaults={"created_by": user}
        )
        return customer


class CustomerDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(required=False)
    customer_phone = serializers.CharField(required=False)
    customer_email = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    
    class Meta:
        model = Customer
        exclude = ("created_by",)
    
    def validate(self, attrs):
        email = attrs.get("customer_email", None)
        phone = attrs.get("customer_phone", None)
        name = attrs.get("customer_name", None)
        user = self.context["request"].user
        customer_id = self.context["customer"]
        qs = Customer.objects.filter(created_by=user)
        
        if email:
            try:
                email = validate_email(email.lower().strip()).email
            except EmailNotValidError as e:
                raise serializers.ValidationError("Email not valid")
            
            email_exist = qs.filter(customer_email=email, pk=customer_id).first()
            
            if email_exist is None and qs.filter(customer_email=email).exists():
                raise serializers.ValidationError("Customer with email already exists")
            attrs["customer_email"] = email

        if phone:
            phone_number = sanitize_phone_number(phone)
            
            if isinstance(phone_number, dict):
                raise serializers.ValidationError({"phone": phone_number["message"]})
            
            if qs.filter(phone=phone_number).exists():
                raise serializers.ValidationError(
                    "Account with phone number already exists"
                )
            
            phone_exist = qs.filter(customer_phone=phone, id=customer_id).first()
            if phone_exist is None and qs.filter(customer_phone=phone_number).exists():
                raise serializers.ValidationError(
                    "Customer with phone number already exists"
                )
            attrs["customer_phone"] = phone_number
        
        if name:
            attrs["customer_name"] = name.capitalize()
        return super().validate(attrs)


class OrderSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Order
        exclude = ("grand_total",)
        extra_kwargs = {"balance": {"read_only": True},
                        "payment_option": {"required": True}}
    
    def payment_validation(self, amount_paid):
        if amount_paid < 0:
            raise serializers.ValidationError({"amount_paid": "Enter a valid amount"})
        if isinstance(amount_paid, str):
            raise serializers.ValidationError({"amount_paid": "enter a valid amount"})
        
    def validate(self, attrs):
        amount_paid = attrs.get("amount_payment", None)
        payment_date = attrs.get("payment_date", None)
        total_price = attrs.get("total_price", None)
        
        if amount_paid > total_price:
            raise serializers.ValidationError({"amount_paid":"Amount paid higher than total price"})
        if amount_paid == total_price:
            raise serializers.ValidationError({"amount_paid":"Amount paid equal to total price"})
                
        self.payment_validation(amount_paid)
        if payment_date is not None:
            if payment_date is not datetime.date.today():
                attrs['payment_date'] = payment_date
        else:
            attrs['payment_date'] = datetime.datetime.now()
        return super().validate(attrs)
    
    def save(self, validated_data):
        user = self.context["request"].user
        cart_items = Cart.objects.filter(created_by=user)
        
        if cart_items:
            with transaction.atomic():
                order = Order.objects.create(**validated_data, created_by=user)
                orderItems_list = []
                order_item_name = []
                sum_total_price = 0
                
                for item in cart_items:
                    product = ProductInventory.objects.filter(
                        id=item.product_id
                    ).first()
                    orderItems = OrderItem(
                        product=product,
                        created_by=item.created_by,
                        order=order,
                        quantity=item.quantity,
                        product_cost_price=product.cost_price,
                        selling_price=item.selling_price,
                        total_price=item.total_price,
                    )
                    orderItems_list.append(orderItems)
                    order_item_name.append(product.name)
                    sum_total_price = sum_total_price + item.total_price
                    item.delete()

                OrderItem.objects.bulk_create(orderItems_list, batch_size=10)                
                order.save()

                # create notification for low stock products
                if product.current_quantity <= product.minimum_stock_quantity:
                    updated_values = {
                        "text": f"{product.name} is due for a restock",
                        "receiver": product.created_by,
                        "type": "MSQ",
                        "product": product,
                    }
                    Notification.objects.create(**updated_values)
                
                if product.current_quantity == 0:
                    updated_values = {
                        "text": f"{product.name} is out of stock",
                        "receiver": product.created_by,
                        "type": "MSQ",
                        "product": product,
                    }
                    Notification.objects.create(**updated_values)
                return
        raise Exception("Cart is empty")


class OrderListMainSerializer(serializers.ModelSerializer):
      class Meta:
        model = Order
        exclude = ("created_by",)


class OrderCustomerSerializer(serializers.Serializer):
    
    customer = serializers.SerializerMethodField("get_customers", read_only=True)
    total_product = serializers.SerializerMethodField(
        "get_total_product", read_only=True
    )
    total_amount = serializers.SerializerMethodField("get_amount", read_only=True)
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_customers(self, obj):
        qs = Customer.objects.filter(id=obj["order__customer"]).first()
        if qs:
            serializers = CustomerListSerializer(qs)
            return serializers.data
        return None
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_total_product(self, obj):
        qs = obj["product_quantity"]
        return qs
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_amount(self, obj):
        qs = str(obj["total_amount"])
        return qs


class OrderItemListSerializer(serializers.ModelSerializer):
    product_info = serializers.SerializerMethodField("get_products", read_only=True)
    cart_selling_price = serializers.SerializerMethodField(
        "get_selling_price", read_only=True
    )
    total_amount = serializers.SerializerMethodField("get_amount", read_only=True)
    in_stock = serializers.SerializerMethodField("get_stock", read_only=True)
    total_sold = serializers.SerializerMethodField("get_total_sold", read_only=True)
    
    class Meta:
        model = OrderItem
        exclude = ("created_by",)
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_products(self, obj):
        qs = ProductInventory.objects.filter(id=obj["product_id"]).first()
        if qs:
            serializers = ProductInventorySerializer(qs)
            return serializers.data
        return None
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_selling_price(self, obj):
        qs = str(obj["selling_price"])
        return qs
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_amount(self, obj):
        qs = str(obj["total_amount"])
        return qs
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_stock(self, obj):
        product = ProductInventory.objects.filter(id=obj["product_id"]).first()
        if product:
            return product.current_quantity
        return None

    @extend_schema_field(OpenApiTypes.STR)
    def get_total_sold(self, obj):
        quantity_sold = str(obj["qty"])
        return quantity_sold


class NotificationListSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField("get_product", read_only=True)
    
    class Meta:
        model = Notification
        exclude = ("receiver",)
    
    def save(self, validated_data):
        user = self.context["request"].user
        notification = Notification.objects.get_or_create(
            **validated_data, defaults={"receiver": user}
        )
        return notification
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_product(self, obj):
        if obj.product_id:
            product = ProductInventory.objects.filter(id=obj.product_id).first()
            serializers = ProductCartSerializer(product)
            return serializers.data
        return None


class MarkASReadSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)


class OrderListSerializer(serializers.Serializer):
    """gets each customer product details"""
    order = serializers.SerializerMethodField("get_orders", read_only=True)
    customer = serializers.SerializerMethodField("get_customers", read_only=True)
    product = serializers.SerializerMethodField("get_product_count", read_only=True)
    total_amount = serializers.SerializerMethodField("get_total_amount", read_only=True)
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_orders(self, obj):
        serializers = OrderSerializer(obj)
        return serializers.data
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_customers(self, obj):
        qs = Customer.objects.filter(id=obj.customer_id).first()
        if qs:
            serializers = CustomerListSerializer(qs)
            return serializers.data
        return None
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_total_product(self, obj):
        product_count = OrderItem.objects.filter(order=obj.id).count()
        return product_count
    
    @extend_schema_field(OpenApiTypes.STR)
    def get_total_amount(self, obj):
        orderItems = OrderItem.objects.filter(order=obj.id)
        amount = []
        for sale in orderItems:
            product = ProductInventory.objects.filter(id=sale.product_id).first()
            if product:
                cost = (
                    sale.quantity * product.selling_price
                ) - sale.discount_selling_price
                amount.append(int(cost))
        return sum(amount)
