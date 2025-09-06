from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Category, Wishlist, Cart, CartItem, ProductImage, ProductVariant
from .forms import ProductForm
from shops.models import Shop

def product_list(request):
    if request.user.is_authenticated and request.user.email == 'protechdza@gmail.com':
        # Admin sees all products from all shops
        products = Product.objects.all().order_by('-created_at')
    elif request.user.is_authenticated and request.user.is_seller and hasattr(request.user, 'shop'):
        # Seller sees only their products (regardless of shop status)
        products = Product.objects.filter(shop=request.user.shop).order_by('-created_at')
    else:
        # Buyers see only products from active shops
        products = Product.objects.filter(shop__is_active=True).order_by('-created_at')
    
    categories = Category.get_all_categories()
    
    # Filter by category
    category_name = request.GET.get('category')
    if category_name:
        products = products.filter(category__name=category_name)
    
    # Search
    search = request.GET.get('search')
    if search:
        products = products.filter(name__icontains=search)
    
    return render(request, 'products/list.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_name,
        'search_query': search or ''
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user can view this product
    if not product.shop.is_active:
        # Only shop owner can view products from inactive shops
        if not (request.user.is_authenticated and hasattr(request.user, 'shop') and request.user.shop == product.shop):
            messages.error(request, 'This product is not available')
            return redirect('product_list')
    
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
            
            # Handle variants
            variant_index = 0
            while f'variant_name_{variant_index}' in request.POST:
                variant_name = request.POST.get(f'variant_name_{variant_index}')
                if variant_name:
                    variant = ProductVariant.objects.create(
                        product=product,
                        name=variant_name,
                        sku=request.POST.get(f'variant_sku_{variant_index}', ''),
                        price=request.POST.get(f'variant_price_{variant_index}') or None,
                        quantity=int(request.POST.get(f'variant_quantity_{variant_index}', 0))
                    )
                    
                    # Handle variant image
                    variant_image = request.FILES.get(f'variant_image_{variant_index}')
                    if variant_image:
                        variant.image = variant_image
                        variant.save()
                        
                variant_index += 1
            
            messages.success(request, 'Product added successfully!')
            return redirect('dashboard')
    else:
        form = ProductForm()
    
    return render(request, 'products/add.html', {'form': form})



def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, shop__is_active=True)
    variant_id = request.POST.get('variant_id') if request.method == 'POST' else None
    variant = None
    
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
        if variant.is_out_of_stock:
            messages.error(request, f'{variant.name} is out of stock!')
            return redirect('product_detail', product_id=product_id)
    elif product.has_variants:
        messages.error(request, 'Please select a variant!')
        return redirect('product_detail', product_id=product_id)
    
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        variant_name = f' - {variant.name}' if variant else ''
        messages.success(request, f'Added {product.name}{variant_name} to cart!')
    else:
        # Handle guest cart using session
        cart_key = f"{product_id}_{variant_id}" if variant_id else str(product_id)
        cart_items = request.session.get('cart', {})
        if cart_key in cart_items:
            cart_items[cart_key] += 1
        else:
            cart_items[cart_key] = 1
        request.session['cart'] = cart_items
        request.session.modified = True
        
        variant_name = f' - {variant.name}' if variant else ''
        messages.success(request, f'Added {product.name}{variant_name} to cart!')
    
    return redirect('home')

def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to add to wishlist')
        return redirect('login')
        
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        messages.success(request, f'Added {product.name} to wishlist!')
    else:
        wishlist_item.delete()
        messages.success(request, f'Removed {product.name} from wishlist!')
    
    return redirect('product_detail', product_id=product_id)

@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, 'products/wishlist.html', {'wishlist_items': wishlist_items})

def cart_view(request):
    cart_items = []
    total = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()
            total = sum(item.product.price * item.quantity for item in cart_items)
        except Cart.DoesNotExist:
            cart_items = []
    else:
        # Handle guest cart from session
        session_cart = request.session.get('cart', {})
        for product_id, quantity in session_cart.items():
            try:
                product = Product.objects.get(id=product_id)
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': product.price * quantity
                })
                total += product.price * quantity
            except Product.DoesNotExist:
                continue
    
    return render(request, 'products/cart.html', {
        'items': cart_items,
        'total': total,
        'is_guest': not request.user.is_authenticated
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

def update_session_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')
        cart_items = request.session.get('cart', {})
        
        if action == 'increase':
            cart_items[product_id] = cart_items.get(product_id, 0) + 1
        elif action == 'decrease':
            if product_id in cart_items:
                if cart_items[product_id] > 1:
                    cart_items[product_id] -= 1
                else:
                    del cart_items[product_id]
        elif action == 'remove':
            if product_id in cart_items:
                del cart_items[product_id]
        
        request.session['cart'] = cart_items
        request.session.modified = True
    
    return redirect('cart')

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, shop__owner=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            
            # Handle new images
            images = request.FILES.getlist('images')
            for image in images:
                ProductImage.objects.create(product=product, image=image)
            
            # Handle existing variant updates
            for variant in product.variants.all():
                variant_id = variant.id
                
                # Check if variant should be deleted
                if request.POST.get(f'delete_variant_{variant_id}'):
                    variant.delete()
                    continue
                
                # Update existing variant
                variant.name = request.POST.get(f'existing_variant_name_{variant_id}', variant.name)
                variant.sku = request.POST.get(f'existing_variant_sku_{variant_id}', variant.sku)
                variant.price = request.POST.get(f'existing_variant_price_{variant_id}') or None
                variant.quantity = int(request.POST.get(f'existing_variant_quantity_{variant_id}', variant.quantity))
                
                # Handle variant image update
                variant_image = request.FILES.get(f'existing_variant_image_{variant_id}')
                if variant_image:
                    variant.image = variant_image
                
                variant.save()
            
            # Handle new variants
            variant_index = 0
            while f'variant_name_{variant_index}' in request.POST:
                variant_name = request.POST.get(f'variant_name_{variant_index}')
                if variant_name:
                    variant = ProductVariant.objects.create(
                        product=product,
                        name=variant_name,
                        sku=request.POST.get(f'variant_sku_{variant_index}', ''),
                        price=request.POST.get(f'variant_price_{variant_index}') or None,
                        quantity=int(request.POST.get(f'variant_quantity_{variant_index}', 0))
                    )
                    
                    # Handle variant image
                    variant_image = request.FILES.get(f'variant_image_{variant_index}')
                    if variant_image:
                        variant.image = variant_image
                        variant.save()
                        
                variant_index += 1
            
            messages.success(request, 'Product updated successfully!')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'products/edit.html', {'form': form, 'product': product})

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, shop__owner=request.user)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('dashboard')
    
    return render(request, 'products/delete.html', {'product': product})

def shop_products(request, shop_slug):
    shop = get_object_or_404(Shop, slug=shop_slug)
    products = Product.objects.filter(shop=shop)
    
    return render(request, 'products/shop_products.html', {
        'shop': shop,
        'products': products
    })