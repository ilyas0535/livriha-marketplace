from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_shop, name='create_shop'),
    path('settings/', views.shop_settings, name='shop_settings'),
    path('payment-guide/', views.payment_guide, name='payment_guide'),
    path('admin/', views.admin_shops, name='admin_shops'),
    path('admin/<int:shop_id>/', views.admin_shop_dashboard, name='admin_shop_dashboard'),
    path('toggle/<int:shop_id>/', views.toggle_shop_status, name='toggle_shop_status'),
    path('<slug:slug>/', views.shop_detail, name='shop_detail'),
]