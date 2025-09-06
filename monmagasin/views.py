from django.shortcuts import render
from products.models import Product
from django.db.models import Q, Count
from orders.models import OrderItem
import random

def home(request):
    # Only show products from active shops
    products = Product.objects.select_related('shop').filter(shop__is_active=True)
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(shop__name__icontains=search)
        )
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sort functionality
    sort_by = request.GET.get('sort', 'random')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'most_selling':
        products = products.annotate(
            sales_count=Count('orderitem')
        ).order_by('-sales_count')
    else:  # random
        products = list(products)
        random.shuffle(products)
        products = products[:12]
    
    if sort_by != 'random':
        products = products[:12]
    
    context = {
        'products': products,
        'search': search or '',
        'min_price': min_price or '',
        'max_price': max_price or '',
        'sort_by': sort_by,
    }
    
    return render(request, 'home.html', context)