from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order, OrderItem, Notification
from products.models import Cart, Product
from accounts.models import User

def payment_gateway(request, order_id, payment_method):
    order = get_object_or_404(Order, id=order_id)
    shop = order.shop
    
    context = {
        'order': order,
        'shop': shop,
        'payment_method': payment_method,
        'total_amount': order.total_amount,
        'order_id': order_id
    }
    
    return render(request, 'orders/payment_gateway.html', context)

def upload_payment_proof(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST' and request.FILES.get('payment_proof'):
        order.payment_proof = request.FILES['payment_proof']
        order.save()
        
        messages.success(request, 'Payment proof uploaded successfully! Your order is pending verification.')
        return redirect('payment_success', order_id=order.id)
    
    return redirect('payment_gateway', order_id=order.id, payment_method=order.payment_method)

def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = 'waiting'
    order.save()
    
    messages.success(request, f'Payment successful! Order #{order.order_number} has been confirmed.')
    return redirect('home')

def create_order(request):
    shops_items = {}
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            if not cart.items.exists():
                messages.error(request, 'Your cart is empty')
                return redirect('cart')
            
            # Group items by shop
            for item in cart.items.all():
                shop = item.product.shop
                if shop not in shops_items:
                    shops_items[shop] = []
                shops_items[shop].append(item)
        except Cart.DoesNotExist:
            messages.error(request, 'No cart found')
            return redirect('home')
    else:
        # Guest user - get from session
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, 'Your cart is empty')
            return redirect('cart')
        
        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                shop = product.shop
                if shop not in shops_items:
                    shops_items[shop] = []
                shops_items[shop].append({
                    'product': product,
                    'quantity': quantity
                })
            except Product.DoesNotExist:
                pass
        
    # Get payment methods from session
    payment_methods = request.session.get('payment_methods', {})
    
    # Create separate orders for each shop
    orders_to_pay = []
    for shop, items in shops_items.items():
        if request.user.is_authenticated:
            total = sum(item.product.price * item.quantity for item in items)
        else:
            total = sum(item['product'].price * item['quantity'] for item in items)
        
        order_data = {
            'shop': shop,
            'total_amount': total
        }
        
        if request.user.is_authenticated:
            order_data['customer'] = request.user
        
        order = Order.objects.create(**order_data)
        
        # Add customer info from checkout form
        order.customer_name = request.session.get('customer_name', '')
        order.customer_email = request.session.get('customer_email', '')
        order.customer_phone = request.session.get('customer_phone', '')
        order.customer_address = request.session.get('customer_address', '')
        order.save()
        
        for item in items:
            if request.user.is_authenticated:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=getattr(item, 'variant', None),
                    quantity=item.quantity,
                    price=item.unit_price
                )
                # Update product quantity
                item.product.quantity -= item.quantity
                item.product.save()
                
                # Check for low stock
                if item.product.is_low_stock:
                    existing_notification = Notification.objects.filter(
                        user=shop.owner,
                        type='low_stock',
                        message__contains=f'Product "{item.product.name}"',
                        is_read=False
                    ).first()
                    
                    if not existing_notification:
                        Notification.objects.create(
                            user=shop.owner,
                            type='low_stock',
                            title='Low Stock Alert',
                            message=f'Product "{item.product.name}" is running low on stock ({item.product.quantity} remaining)'
                        )
            else:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['product'].price
                )
                # Update product quantity
                item['product'].quantity -= item['quantity']
                item['product'].save()
                
                # Check for low stock
                if item['product'].is_low_stock:
                    existing_notification = Notification.objects.filter(
                        user=shop.owner,
                        type='low_stock',
                        message__contains=f'Product "{item["product"].name}"',
                        is_read=False
                    ).first()
                    
                    if not existing_notification:
                        Notification.objects.create(
                            user=shop.owner,
                            type='low_stock',
                            title='Low Stock Alert',
                            message=f'Product "{item["product"].name}" is running low on stock ({item["product"].quantity} remaining)'
                        )
        
        # Send notifications
        from .notifications import notify_seller_new_order, notify_buyer_order_placed
        notify_seller_new_order(order)
        notify_buyer_order_placed(order)
        
        # Create notification for seller
        Notification.objects.create(
            user=shop.owner,
            type='new_order',
            title=f'New Order #{order.order_number}',
            message=f'You received a new order worth ${order.total_amount} from {order.customer_name or "Guest"}'
        )
        
        # Check payment method
        payment_method = payment_methods.get(str(shop.id))
        if payment_method and payment_method != 'cash_on_delivery':
            orders_to_pay.append((order.id, payment_method))
    
    # Clear cart
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart.items.all().delete()
        except Cart.DoesNotExist:
            pass
    else:
        request.session['cart'] = {}
    
    # Redirect to payment if needed
    if orders_to_pay:
        order_id, payment_method = orders_to_pay[0]
        return redirect('payment_gateway', order_id=order_id, payment_method=payment_method)
    else:
        messages.success(request, 'Orders created successfully!')
        return redirect('home')


@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, shop__owner=request.user)
    
    if request.method == 'POST':
        old_status = order.status
        new_status = request.POST['status']
        
        if old_status != new_status:
            order.status = new_status
            order.save()
            
            # Restore inventory for cancelled or returned orders
            if new_status in ['cancelled', 'returned']:
                for item in order.items.all():
                    item.product.quantity += item.quantity
                    item.product.save()
            
            # Save status history
            from .models import OrderStatusHistory
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                changed_by=request.user
            )
            
            # Send notification to customer
            from .notifications import notify_customer_order_update
            notify_customer_order_update(order, old_status, new_status)
            
            # Create notification for buyer if they have an account
            if order.customer:
                Notification.objects.create(
                    user=order.customer,
                    type='order_update',
                    title=f'Order #{order.order_number} Updated',
                    message=f'Your order status has been changed to {new_status.title()}'
                )
            
            messages.success(request, f'Order status updated to {new_status}')
    
    return redirect('dashboard')

def checkout(request):
    items = []
    shops_items = {}
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()
            for item in cart_items:
                shop = item.product.shop
                if shop not in shops_items:
                    shops_items[shop] = []
                shops_items[shop].append(item)
        except Cart.DoesNotExist:
            pass
    else:
        # Guest user
        cart = request.session.get('cart', {})
        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                shop = product.shop
                if shop not in shops_items:
                    shops_items[shop] = []
                shops_items[shop].append({
                    'product': product,
                    'quantity': quantity
                })
            except Product.DoesNotExist:
                pass
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            email = request.POST.get('email')
            if not email:
                messages.error(request, 'Email is required for checkout')
                return render(request, 'orders/checkout.html', {'shops_items': shops_items})
        
        # Store customer info in session for all users
        request.session['customer_name'] = request.POST.get('full_name', '')
        request.session['customer_email'] = request.POST.get('email', '')
        request.session['customer_phone'] = request.POST.get('phone', '')
        request.session['customer_address'] = request.POST.get('address', '')
        
        # Get selected payment methods for each shop
        payment_methods = {}
        for shop in shops_items.keys():
            method_key = f'payment_method_{shop.id}'
            payment_methods[shop.id] = request.POST.get(method_key)
        
        # Store payment methods in session for create_order
        request.session['payment_methods'] = payment_methods
        
        return redirect('create_order')
    
    return render(request, 'orders/checkout.html', {'shops_items': shops_items})

def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variant_id = request.POST.get('variant_id') if request.method == 'POST' else None
    variant = None
    
    # Check if user is product owner
    if request.user.is_authenticated and hasattr(request.user, 'shop') and product.shop == request.user.shop:
        messages.info(request, 'You cannot buy your own product.')
        return redirect('edit_product', product_id=product.id)
    
    # Handle variant selection
    if variant_id:
        from products.models import ProductVariant
        variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
        if variant.is_out_of_stock:
            messages.error(request, f'{variant.name} is out of stock')
            return redirect('product_detail', product_id=product_id)
        effective_price = variant.effective_price
    elif product.has_variants and request.method == 'POST':
        messages.error(request, 'Please select a variant!')
        return redirect('product_detail', product_id=product_id)
    elif not product.has_variants:
        if product.is_out_of_stock:
            messages.error(request, 'Product is out of stock')
            return redirect('home')
        effective_price = product.price
        variant = None
    else:
        # GET request - show buy now form
        effective_price = product.price
        variant = None
    
    # Create single item checkout
    shops_items = {
        product.shop: [{
            'product': product,
            'variant': variant,
            'quantity': 1,
            'price': effective_price
        }]
    }
    
    # Only process order if coming from buy_now form with customer details
    if request.method == 'POST' and request.POST.get('full_name'):
        if not request.user.is_authenticated:
            email = request.POST.get('email')
            if not email:
                messages.error(request, 'Email is required for checkout')
                return render(request, 'orders/buy_now.html', {'shops_items': shops_items, 'product': product})
        
        payment_method = request.POST.get('payment_method', 'cash_on_delivery')
        
        # Create order directly
        order_data = {
            'shop': product.shop,
            'total_amount': effective_price,
            'customer_name': request.POST.get('full_name', ''),
            'customer_email': request.POST.get('email', ''),
            'customer_phone': request.POST.get('phone', ''),
            'customer_address': request.POST.get('address', ''),
            'payment_method': payment_method
        }
        
        if request.user.is_authenticated:
            order_data['customer'] = request.user
        
        order = Order.objects.create(**order_data)
        
        OrderItem.objects.create(
            order=order,
            product=product,
            product_variant=variant,
            quantity=1,
            price=effective_price
        )
        
        # Update stock (handled automatically by OrderItem.save())
        
        # Check for low stock
        if product.is_low_stock:
            existing_notification = Notification.objects.filter(
                user=product.shop.owner,
                type='low_stock',
                message__contains=f'Product "{product.name}"',
                is_read=False
            ).first()
            
            if not existing_notification:
                Notification.objects.create(
                    user=product.shop.owner,
                    type='low_stock',
                    title='Low Stock Alert',
                    message=f'Product "{product.name}" is running low on stock ({product.quantity} remaining)'
                )
        
        # Send notifications
        from .notifications import notify_seller_new_order, notify_buyer_order_placed
        notify_seller_new_order(order)
        notify_buyer_order_placed(order)
        
        # Create notification for seller
        Notification.objects.create(
            user=product.shop.owner,
            type='new_order',
            title=f'New Order #{order.order_number}',
            message=f'You received a new order worth ${order.total_amount} from {order.customer_name or "Guest"}'
        )
        
        # Redirect to payment gateway or success based on payment method
        if payment_method == 'cash_on_delivery':
            messages.success(request, 'Order placed successfully! You will receive a confirmation email.')
            return redirect('payment_success', order_id=order.id)
        else:
            return redirect('payment_gateway', order_id=order.id, payment_method=payment_method)
    
    return render(request, 'orders/buy_now.html', {
        'shops_items': shops_items, 
        'product': product, 
        'selected_variant': variant,
        'effective_price': effective_price
    })