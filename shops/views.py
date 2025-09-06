from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Shop
from products.models import Product

@login_required
def create_shop(request):
    if hasattr(request.user, 'shop'):
        messages.info(request, 'You already have a shop')
        return redirect('dashboard')
    
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        logo = request.FILES.get('logo')
        
        # Check if shop name already exists
        from django.utils.text import slugify
        slug = slugify(name)
        if Shop.objects.filter(slug=slug).exists():
            messages.error(request, 'A shop with this name already exists. Please choose a different name.')
            return render(request, 'shops/create.html')
        
        shop = Shop.objects.create(
            owner=request.user,
            name=name,
            description=description,
            logo=logo,
            checkout_methods=['cash_on_delivery']
        )
        
        messages.success(request, f'Shop created! Your shop URL: {shop.get_absolute_url()}')
        return redirect('dashboard')
    
    return render(request, 'shops/create.html')

def shop_detail(request, slug):
    shop = get_object_or_404(Shop, slug=slug)
    
    # Show products based on user type and shop status
    if (request.user.is_authenticated and hasattr(request.user, 'shop') and request.user.shop == shop) or (request.user.is_authenticated and request.user.email == 'protechdza@gmail.com'):
        # Shop owner or admin sees all products regardless of shop status
        products = Product.objects.filter(shop=shop)
    elif shop.is_active:
        # Others see products only if shop is active
        products = Product.objects.filter(shop=shop)
    else:
        # Shop is inactive, show no products to non-owners
        products = Product.objects.none()
    
    return render(request, 'shops/detail.html', {
        'shop': shop,
        'products': products
    })

@login_required
def shop_settings(request):
    if not hasattr(request.user, 'shop'):
        messages.error(request, 'You need to create a shop first')
        return redirect('create_shop')
    
    shop = request.user.shop
    
    if request.method == 'POST':
        checkout_methods = request.POST.getlist('checkout_methods')
        shop.checkout_methods = checkout_methods
        shop.order_reminder_period = request.POST.get('order_reminder_period', '1d')
        shop.show_stock_to_customers = 'show_stock_to_customers' in request.POST
        
        shop.save()
        
        messages.success(request, 'Shop settings updated successfully')
        return redirect('shop_settings')
    
    return render(request, 'shops/settings.html', {'shop': shop})

@login_required
def admin_shops(request):
    if request.user.email != 'protechdza@gmail.com':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    from django.db.models import Count, Sum
    from orders.models import Order
    
    shops = Shop.objects.annotate(
        product_count=Count('product'),
        order_count=Count('product__orderitem__order', distinct=True),
        total_revenue=Sum('product__orderitem__price')
    ).order_by('-created_at')
    
    # Get all orders for admin view
    all_orders = Order.objects.all().order_by('-created_at')[:20]
    
    return render(request, 'shops/admin_shops.html', {
        'shops': shops,
        'all_orders': all_orders
    })

@login_required
def toggle_shop_status(request, shop_id):
    if request.user.email != 'protechdza@gmail.com':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    shop = get_object_or_404(Shop, id=shop_id)
    shop.is_active = not shop.is_active
    shop.save()
    
    status = 'activated' if shop.is_active else 'deactivated'
    messages.success(request, f'Shop {shop.name} has been {status}')
    return redirect('admin_shops')

@login_required
def admin_shop_dashboard(request, shop_id):
    if request.user.email != 'protechdza@gmail.com':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    from django.db.models import Sum, Count
    from orders.models import Order
    
    shop = get_object_or_404(Shop, id=shop_id)
    
    # Get shop orders and statistics
    orders = Order.objects.filter(shop=shop).order_by('-created_at')
    
    # Filter orders by status and search
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(customer_name__icontains=search_query)
        )
    
    orders = orders[:20]  # Limit to 20 orders
    
    return render(request, 'shops/admin_shop_dashboard.html', {
        'shop': shop,
        'orders': orders,
        'status_filter': status_filter,
        'search_query': search_query,
        'is_admin_view': True
    })

def check_shop_name(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        name = data.get('name')
        from django.utils.text import slugify
        slug = slugify(name)
        exists = Shop.objects.filter(slug=slug).exists()
        return JsonResponse({'exists': exists})
    return JsonResponse({'error': 'Invalid request'})

def payment_guide(request):
    return render(request, 'shops/payment_setup_guide.html')