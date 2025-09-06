#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monmagasin.settings')
django.setup()

from products.models import Product

product = Product.objects.first()
print(f"Product: {product.name}")
print(f"Rank calculation debug:")

# Simulate the calculation
all_products = Product.objects.annotate(
    total_sales=django.db.models.Sum('orderitem__quantity')
).order_by('-total_sales')

total_products = all_products.count()
print(f"Total products: {total_products}")

for i, p in enumerate(all_products, 1):
    sales = p.total_sales or 0
    percentile = (i / total_products) * 100
    print(f"Rank {i}: {p.name} - Sales: {sales} - Percentile: {percentile}%")
    
    if percentile <= 20:
        expected_rating = 5
    elif percentile <= 40:
        expected_rating = 4
    elif percentile <= 60:
        expected_rating = 3
    elif percentile <= 80:
        expected_rating = 2
    else:
        expected_rating = 1
        
    print(f"Expected rating: {expected_rating}")
    print(f"Actual rating: {p.sales_rating}")