from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Product, Category, Wishlist, Cart, CartItem, ProductImage
from .forms import ProductForm
from shops.models import Shop

def product_list(request):
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Search
    search = request.GET.get('search')
    if search:
        products = products.filter(name__icontains=search)
    
    return render(request, 'products/list.html', {
        'products': products,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None,
        'search_query': search or ''
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'products/detail.html', {'product': product})

@login_required
def add_product(request):
    if not hasattr(request.user, 'shop'):
        messages.error(request, 'You need to create a shop first')
        return redirect('create_shop')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.shop = request.user.shop
            product.save()
            
            # Handle multiple images
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=(i == 0)  # First image is primary
                )
            
            messages.success(request, 'Product added successfully!')
            return redirect('dashboard')
    else:
        form = ProductForm()
    
    return render(request, 'products/add.html', {'form': form})

@login_required
@require_POST
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        return JsonResponse({'status': 'added', 'message': 'Added to wishlist'})
    else:
        wishlist_item.delete()
        return JsonResponse({'status': 'removed', 'message': 'Removed from wishlist'})

@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'products/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    return JsonResponse({'status': 'success', 'message': 'Added to cart'})

@login_required
def cart_view(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
    except Cart.DoesNotExist:
        cart_items = []
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return render(request, 'products/cart.html', {
        'cart_items': cart_items,
        'total': total
    })

@login_required
@require_POST
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    elif action == 'remove':
        cart_item.delete()
    
    return redirect('cart')

def shop_products(request, shop_slug):
    shop = get_object_or_404(Shop, slug=shop_slug)
    products = Product.objects.filter(shop=shop)
    
    return render(request, 'products/shop_products.html', {
        'shop': shop,
        'products': products
    })