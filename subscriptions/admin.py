from django.contrib import admin
from .models import SubscriptionPlan, Subscription, PaymentConfirmation

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'plan']

@admin.register(PaymentConfirmation)
class PaymentConfirmationAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'amount', 'created_at', 'is_confirmed']
    list_filter = ['is_confirmed', 'plan']