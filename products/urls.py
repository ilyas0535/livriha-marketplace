from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('add/', views.add_product, name='add_product'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('cart/', views.cart_view, name='cart'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
]