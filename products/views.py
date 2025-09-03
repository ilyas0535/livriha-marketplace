from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Product, Cart, CartItem, Wishlist, ProductImage, Category, ProductRating, ShopRating
from shops.models import Shop
import json

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Check if user is product owner
    if request.user.is_authenticated and hasattr(request.user, 'shop') and product.shop == request.user.shop:
        messages.info(request, 'You cannot buy your own product. You can edit it instead.')
        return redirect('edit_product', product_id=product.id)
    
    if product.is_out_of_stock:
        messages.error(request, 'Product is out of stock')
        return redirect('home')
    
    if request.user.is_authenticated:
        # Logged in user - use database cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': 1}
        )
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    else:
        # Guest user - use session cart
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        if product_id_str in cart:
            cart[product_id_str] += 1
        else:
            cart[product_id_str] = 1
        request.session['cart'] = cart
    
    messages.success(request, 'Product added to cart')
    return redirect('home')

@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        messages.success(request, 'Product added to wishlist')
    else:
        messages.info(request, 'Product already in wishlist')
    
    return redirect('home')

def cart_view(request):
    items = []
    total = 0
    
    if request.user.is_authenticated:
        # Logged in user
        try:
            cart = Cart.objects.get(user=request.user)
            items = cart.items.all()
            total = sum(item.product.price * item.quantity for item in items)
        except Cart.DoesNotExist:
            items = []
    else:
        # Guest user
        cart = request.session.get('cart', {})
        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                items.append({
                    'product': product,
                    'quantity': quantity,
                    'total': product.price * quantity
                })
                total += product.price * quantity
            except Product.DoesNotExist:
                pass
    
    return render(request, 'products/cart.html', {'items': items, 'total': total})

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'products/wishlist.html', {'items': wishlist_items})

@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, 'Product removed from wishlist')
    return redirect('wishlist')

@login_required
def manage_products(request):
    if not hasattr(request.user, 'shop'):
        messages.error(request, 'You need to create a shop first')
        return redirect('create_shop')
    
    products = Product.objects.filter(shop=request.user.shop)
    return render(request, 'products/manage.html', {'products': products})

@login_required
def add_product(request):
    if not hasattr(request.user, 'shop'):
        messages.error(request, 'You need to create a shop first')
        return redirect('create_shop')
    
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        price = request.POST['price']
        old_price = request.POST.get('old_price') or None
        quantity = request.POST['quantity']
        
        product = Product.objects.create(
            shop=request.user.shop,
            name=name,
            description=description,
            price=price,
            old_price=old_price,
            quantity=quantity
        )
        
        # Handle multiple image uploads
        images = request.FILES.getlist('images')
        for i, image in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(i == 0)  # First image is primary
            )
        
        messages.success(request, 'Product added successfully')
        return redirect('manage_products')
    
    categories = Category.objects.all()
    return render(request, 'products/add.html', {'categories': categories})

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, shop=request.user.shop)
    
    if request.method == 'POST':
        old_quantity = product.quantity
        product.name = request.POST['name']
        product.description = request.POST['description']
        product.price = request.POST['price']
        product.old_price = request.POST.get('old_price') or None
        product.quantity = int(request.POST['quantity'])
        product.save()
        
        # Check for low stock and create notification
        if product.is_low_stock and old_quantity != product.quantity:
            from orders.models import Notification
            # Check if notification already exists for this product
            existing_notification = Notification.objects.filter(
                user=request.user,
                type='low_stock',
                message__contains=f'Product "{product.name}"',
                is_read=False
            ).first()
            
            if not existing_notification:
                Notification.objects.create(
                    user=request.user,
                    type='low_stock',
                    title='Low Stock Alert',
                    message=f'Product "{product.name}" is running low on stock ({product.quantity} remaining)'
                )
        
        messages.success(request, 'Product updated successfully')
        return redirect('manage_products')
    
    return render(request, 'products/edit.html', {'product': product})

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, shop=request.user.shop)
    product.delete()
    messages.success(request, 'Product deleted successfully')
    return redirect('manage_products')

def cart_count_api(request):
    count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = sum(item.quantity for item in cart.items.all())
        except Cart.DoesNotExist:
            count = 0
    else:
        # Guest user session cart
        cart = request.session.get('cart', {})
        count = sum(int(quantity) for quantity in cart.values())
    
    return JsonResponse({'count': count})

def update_cart_quantity(request, product_id):
    if request.method == 'POST':
        action = request.POST.get('action')
        product = get_object_or_404(Product, id=product_id)
        
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
            
            if action == 'increase':
                cart_item.quantity += 1
                cart_item.save()
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                else:
                    cart_item.delete()
                    messages.success(request, 'Product removed from cart')
        else:
            # Guest user - update session cart
            cart = request.session.get('cart', {})
            current_qty = int(cart.get(str(product_id), 1))
            
            if action == 'increase':
                cart[str(product_id)] = current_qty + 1
            elif action == 'decrease':
                if current_qty > 1:
                    cart[str(product_id)] = current_qty - 1
                else:
                    cart.pop(str(product_id), None)
                    messages.success(request, 'Product removed from cart')
            
            request.session['cart'] = cart
    
    return redirect('cart')

@login_required
def rate_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        rating = int(request.POST['rating'])
        comment = request.POST.get('comment', '')
        
        ProductRating.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={'rating': rating, 'comment': comment}
        )
        
        messages.success(request, 'Product rating submitted successfully')
    
    return redirect('home')

@login_required
def rate_shop(request, shop_id):
    from shops.models import Shop
    shop = get_object_or_404(Shop, id=shop_id)
    
    if request.method == 'POST':
        rating = int(request.POST['rating'])
        comment = request.POST.get('comment', '')
        
        ShopRating.objects.update_or_create(
            user=request.user,
            shop=shop,
            defaults={'rating': rating, 'comment': comment}
        )
        
        messages.success(request, 'Shop rating submitted successfully')
    
    return redirect('shop_detail', slug=shop.slug)

@login_required
def add_product_images(request, product_id):
    product = get_object_or_404(Product, id=product_id, shop=request.user.shop)
    
    if request.method == 'POST':
        images = request.FILES.getlist('images')
        for image in images:
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=False
            )
        messages.success(request, f'{len(images)} image(s) added successfully')
    
    return redirect('edit_product', product_id=product.id)

@login_required
def delete_product_image(request, image_id):
    image = get_object_or_404(ProductImage, id=image_id, product__shop=request.user.shop)
    image.delete()
    messages.success(request, 'Image deleted successfully')
    return redirect('edit_product', product_id=image.product.id)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = ProductRating.objects.filter(product=product).order_by('-created_at')
    
    context = {
        'product': product,
        'reviews': reviews,
    }
    return render(request, 'products/detail.html', context)