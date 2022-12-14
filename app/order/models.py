import uuid
from django.db import models
from decimal import Decimal
from django.contrib.auth.models import User


NOTIFICATION_STATUS = (
    ("READ", "READ"),
    ("UNREAD", "UNREAD"),
)


class Base(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class CartManager(models.Manager):
    def create_cart(self, product, selling_price, created_by):
        item = self.create(
            product=product, selling_price=selling_price, created_by=created_by
        )
        product = item.product
        item.total_price = item.selling_price
        qty = product.current_quantity
        if qty < 1:
            self.delete()
            raise ValueError("Inventory is low")
        product.current_quantity = product.current_quantity - 1
        product.save()
        item.save()
        return item


class Cart(Base):
    product = models.ForeignKey(
        "inventory.ProductInventory", on_delete=models.DO_NOTHING
    )
    quantity = models.PositiveIntegerField(default=1)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")
    
    objects = CartManager()
    
    class Meta:
        ordering = ("-created_at",)
        verbose_name_plural = "Carts"
        unique_together = ("product", "created_by",)
        
    def __str__(self):
        return self.product.name
    
    def get_total_price(self):
        total_price = self.product.selling_price * self.quantity
        self.save()
        return float("%.2f" % total_price)
    
    def add_to_cart(self):
        product = self.product
        if product.current_quantity > 0:
            self.quantity = self.quantity + 1
            product.current_quantity = product.current_quantity - 1
            self.total_price = self.selling_price * self.quantity
            product.save()
            self.save()
        if product.current_quantity <= product.minimum_stock_quantity:
            product.low_quantity = True
        else:
            product.low_quantity = False
        product.save()
        self.save()
    
    def __str__(self):
        return f"{self.product.name} -- ({self.created_by})"


class Customer(Base):
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_phone = models.CharField(max_length=17, blank=True, null=True)
    customer_email = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, 
        related_name="customer_creator", 
        blank=True, 
        null=True
        )

    class Meta:
        ordering = ("customer_name",)
    
    def __str__(self):
        return f"{self.customer_name} -- {self.created_by}"


class Order(Base):
    customer = models.ForeignKey(
        "order.customer",
        on_delete=models.CASCADE,
        related_name="customer_order",
        blank=True,
        null=True,
    )
    amount_payment = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_date = models.DateTimeField(blank=True, null=True)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="order_creator", 
        blank=True, 
        null=True
        )

    class Meta:
        ordering = ("-created_at",)
    
    def __str__(self):
        return f"{self.customer.customer_name} {self.created_by}"


class OrderItem(Base):
    product = models.ForeignKey(
        "inventory.ProductInventory",
        on_delete=models.CASCADE,
        related_name="orderItem_product",
        blank=True,
        null=True,
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="orderItem_order",
        blank=True,
        null=True,
    )
    quantity = models.PositiveIntegerField(default=1)
    product_cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="orderItem_creator", 
        blank=True, 
        null=True
        )


    class Meta:
        ordering = ("-created_at",)
    
    def __str__(self):
        return f"{self.product.name} -- {self.order.customer.customer_name} -- {self.created_by}"


class Notification(Base):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notification_receiver",
        blank=True,
        null=True,
    )
    text = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    product = models.ForeignKey(
        "inventory.ProductInventory",
        on_delete=models.CASCADE,
        related_name="notification_product",
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=50, choices=NOTIFICATION_STATUS, default="UNREAD"
    )
    
    class Meta:
        ordering = ("-created_at",)
    
    def __str__(self):
        return f"{self.receiver}"
