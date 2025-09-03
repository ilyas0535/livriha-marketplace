from django.urls import path
from . import views

urlpatterns = [
    path('plans/', views.subscription_plans, name='subscription_plans'),
    path('purchase/<int:plan_id>/', views.purchase_plan, name='purchase_plan'),
    path('confirm/<int:plan_id>/', views.confirm_payment, name='confirm_payment'),
    path('admin/', views.admin_dashboard, name='subscription_admin'),
    path('activate/<int:payment_id>/', views.activate_subscription, name='activate_subscription'),
]