from django.urls import path
from . import views

urlpatterns = [
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('cart/', views.cart_view, name='cart'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('manage/', views.manage_products, name='manage_products'),
    path('add/', views.add_product, name='add_product'),
    path('edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('api/cart-count/', views.cart_count_api, name='cart_count_api'),
    path('update-cart/<int:product_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('rate-product/<int:product_id>/', views.rate_product, name='rate_product'),
    path('rate-shop/<int:shop_id>/', views.rate_shop, name='rate_shop'),
    path('add-images/<int:product_id>/', views.add_product_images, name='add_product_images'),
    path('delete-image/<int:image_id>/', views.delete_product_image, name='delete_product_image'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
]