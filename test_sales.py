#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monmagasin.settings')
django.setup()

from orders.models import OrderItem
from products.models import Product
from django.db.models import Sum

# Get total platform sales
total = OrderItem.objects.aggregate(total=Sum('quantity'))['total'] or 0
print(f'Total platform sales: {total} items')

print('\nProduct sales and ratings:')
for p in Product.objects.all()[:10]:
    sales = OrderItem.objects.filter(product=p).aggregate(total=Sum('quantity'))['total'] or 0
    rating = p.sales_rating
    print(f'- {p.name}: {sales} sold, {rating} stars')