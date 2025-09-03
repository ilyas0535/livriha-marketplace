from django.contrib import admin
from .models import Order, OrderItem, Notification

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'shop', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at', 'shop']
    search_fields = ['customer__username', 'shop__name']
    inlines = [OrderItemInline]

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']