from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_shop, name='create_shop'),
    path('settings/', views.shop_settings, name='shop_settings'),
    path('payment-guide/', views.payment_guide, name='payment_guide'),
    path('<slug:slug>/', views.shop_detail, name='shop_detail'),
]