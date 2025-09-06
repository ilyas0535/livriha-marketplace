#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monmagasin.settings')
django.setup()

from orders.models import OrderItem
from products.models import Product
from shops.models import Shop
from django.db.models import Sum

print("=== RATING VERIFICATION ===\n")

# Product ratings verification
print("PRODUCT RATINGS:")
print("-" * 50)

# Get all products with sales
products_with_sales = Product.objects.annotate(
    total_sales=Sum('orderitem__quantity')
).order_by('-total_sales')

total_products = products_with_sales.count()
print(f"Total products: {total_products}")

for i, product in enumerate(products_with_sales, 1):
    sales = product.total_sales or 0
    rating = product.sales_rating
    percentile = (i / total_products) * 100
    print(f"{i:2d}. {product.name[:30]:30} | Sales: {sales:3d} | Rating: {rating} stars | Percentile: {percentile:.1f}%")

print("\n" + "=" * 60)

# Shop ratings verification
print("SHOP RATINGS:")
print("-" * 50)

shops_with_sales = Shop.objects.annotate(
    total_sales=Sum('product__orderitem__quantity')
).order_by('-total_sales')

total_shops = shops_with_sales.count()
print(f"Total shops: {total_shops}")

for i, shop in enumerate(shops_with_sales, 1):
    sales = shop.total_sales or 0
    rating = shop.sales_rating
    percentile = (i / total_shops) * 100
    print(f"{i:2d}. {shop.name[:30]:30} | Sales: {sales:3d} | Rating: {rating} stars | Percentile: {percentile:.1f}%")

print("\n" + "=" * 60)
print("RATING DISTRIBUTION SHOULD BE:")
print("Top 20% (1-20th percentile) = 5 stars")
print("Next 20% (21-40th percentile) = 4 stars") 
print("Next 20% (41-60th percentile) = 3 stars")
print("Next 20% (61-80th percentile) = 2 stars")
print("Bottom 20% (81-100th percentile) = 1 star")