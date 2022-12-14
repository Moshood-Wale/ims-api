from django.contrib import admin
from .models import Cart, Customer, Order, OrderItem, Notification


admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Notification)
