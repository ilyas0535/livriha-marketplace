from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Shop
from products.models import Product

@login_required
def create_shop(request):
    if hasattr(request.user, 'shop'):
        messages.info(request, 'You already have a shop')
        return redirect('dashboard')
    
    # Check if user has active subscription
    try:
        subscription = getattr(request.user, 'subscription', None)
        if not subscription or subscription.is_expired:
            messages.error(request, 'You need an active subscription to create a shop.')
            return redirect('subscription_plans')
    except:
        messages.error(request, 'You need an active subscription to create a shop.')
        return redirect('subscription_plans')
    
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        logo = request.FILES.get('logo')
        checkout_methods = request.POST.getlist('checkout_methods')
        
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
            checkout_methods=checkout_methods
        )
        
        messages.success(request, f'Shop created! Your shop URL: {shop.get_absolute_url()}')
        return redirect('dashboard')
    
    return render(request, 'shops/create.html')

def shop_detail(request, slug):
    shop = get_object_or_404(Shop, slug=slug)
    products = Product.objects.filter(shop=shop)
    
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
        
        shop.save()
        
        messages.success(request, 'Shop settings updated successfully')
        return redirect('shop_settings')
    
    return render(request, 'shops/settings.html', {'shop': shop})

def payment_guide(request):
    return render(request, 'shops/payment_setup_guide.html')