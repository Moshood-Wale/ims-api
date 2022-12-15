from django.db import models
import uuid
from django.contrib.auth.models import User

class Base(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Label(Base):
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    description = models.TextField()
    is_primary = models.BooleanField(default=False)
    priority = models.IntegerField()
    
    class Meta:
        ordering = ('priority', '-created_at')
    
    def __str__(self):
        return f"{self.name} -- {self.value}"



class ProductInventory(Base):
    name = models.CharField(max_length=255)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2)
    default_quantity = models.IntegerField(default=0, verbose_name="quantity")
    current_quantity = models.IntegerField(default=0, verbose_name="available_quantity")
    minimum_stock_quantity = models.IntegerField(
        default=0, verbose_name="minimum_stock_quantity", blank=True, null=True
    )
    labels = models.ManyToManyField(Label)
    category = models.CharField(max_length=255)
    low_quantity = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="product_owner")
    
    class Meta:
        ordering = ("-created_at",)
        verbose_name_plural = "ProductInventories"
        unique_together = ("name", "created_by")
    
    def __str__(self):
        return f"{self.name} -- {self.category}"
    
    def restock(self, quantity):
        self.current_quantity = quantity
        self.default_quantity = quantity
        self.save()
        if self.current_quantity > self.minimum_stock_quantity:
            self.low_quantity = False
            self.save()
