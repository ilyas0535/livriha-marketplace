from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from .models import User
from shops.models import Shop
from orders.models import Order, Notification
from products.models import Product
import uuid
import requests
import os

def register(request):
    if request.method == 'POST':
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        is_seller = request.POST.get('is_seller') == 'on'
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'accounts/register.html')
        
        # Create inactive user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_seller=is_seller,
            is_active=False
        )
        
        # Generate verification token
        token = str(uuid.uuid4())
        user.verification_token = token
        user.save()
        
        # Send email using Brevo API
        verification_url = request.build_absolute_uri(reverse('verify_email', args=[token]))
        email_sent = False
        
        try:
            # Use Brevo API instead of SMTP
            api_url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "accept": "application/json",
                "api-key": os.environ.get('BREVO_API_KEY', 'your-brevo-api-key'),
                "content-type": "application/json"
            }
            
            payload = {
                "sender": {"name": "Livriha", "email": "noreply@livriha.store"},
                "to": [{"email": email}],
                "subject": "Verify your email - Livriha",
                "htmlContent": f"<p>Welcome to Livriha!</p><p>Please click the link below to verify your email and activate your account:</p><p><a href='{verification_url}'>Verify Email</a></p><p>Thank you!</p>"
            }
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            if response.status_code == 201:
                email_sent = True
            else:
                print(f"Brevo API failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Email API failed: {e}")
            
        if not email_sent:
            # Activate user immediately if email fails
            user.is_active = True
            user.email_verified = True
            user.save()
        
        if email_sent:
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
        else:
            messages.success(request, 'Registration successful! Email verification temporarily disabled. You can log in now.')
        

        return redirect('login')
    
    return render(request, 'accounts/register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def verify_email(request, token):
    try:
        user = User.objects.get(verification_token=token, is_active=False)
        user.is_active = True
        user.email_verified = True
        user.verification_token = ''
        user.save()
        messages.success(request, 'Email verified successfully! You can now log in.')
    except User.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
    
    return redirect('login')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)
            token = str(uuid.uuid4())
            user.verification_token = token
            user.save()
            
            reset_url = request.build_absolute_uri(reverse('reset_password', args=[token]))
            send_mail(
                'Reset your password - Livriha',
                f'Click the link below to reset your password:\n{reset_url}\n\nIf you did not request this, please ignore this email.',
                settings.DEFAULT_FROM_EMAIL,
                [email]
            )
            messages.success(request, 'Password reset link sent to your email.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'accounts/forgot_password.html')

def reset_password(request, token):
    try:
        user = User.objects.get(verification_token=token)
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired reset link.')
        return redirect('login')
    
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
        else:
            user.set_password(password)
            user.verification_token = ''
            user.save()
            messages.success(request, 'Password reset successfully. You can now log in.')
            return redirect('login')
    
    return render(request, 'accounts/reset_password.html', {'token': token})

@login_required
def dashboard(request):
    if request.user.is_seller:
        try:
            shop = request.user.shop
        except Shop.DoesNotExist:
            shop = None
        
        if shop:
            orders = Order.objects.filter(shop=shop).order_by('-created_at')
            
            # Search functionality
            search_query = request.GET.get('search', '')
            if search_query:
                orders = orders.filter(
                    Q(order_number__icontains=search_query) |
                    Q(customer_name__icontains=search_query)
                )
            
            # Status filter
            status_filter = request.GET.get('status', '')
            if status_filter:
                orders = orders.filter(status=status_filter)
            
            # Pagination
            offset = int(request.GET.get('offset', 0))
            limit = 10
            displayed_orders = orders[offset:offset + limit]
            has_more = orders.count() > offset + limit
            
            # Calculate income by status
            draft_income = sum(order.total_amount for order in orders if order.status == 'draft')
            confirmed_income = sum(order.total_amount for order in orders if order.status == 'confirmed')
            sent_income = sum(order.total_amount for order in orders if order.status == 'sent')
            
            products = Product.objects.filter(shop=shop)
            notifications = Notification.objects.filter(user=request.user, is_read=False)
            
            context = {
                'shop': shop,
                'orders': displayed_orders,
                'search_query': search_query,
                'status_filter': status_filter,
                'offset': offset,
                'has_more': has_more,
                'draft_income': draft_income,
                'confirmed_income': confirmed_income,
                'sent_income': sent_income,
                'total_orders': orders.count(),
                'products': products,
                'notifications': notifications,
            }
        else:
            context = {'shop': None}
    else:
        # Buyer dashboard
        orders = Order.objects.filter(customer=request.user).order_by('-created_at')
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        
        context = {
            'orders': orders,
            'notifications': notifications,
            'is_buyer': True
        }
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def shop_statistics(request):
    try:
        shop = request.user.shop
    except Shop.DoesNotExist:
        messages.error(request, 'You need to create a shop first')
        return redirect('create_shop')
    
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count, Avg
    import json
    
    # Get period filter
    period = request.GET.get('period', '30')
    
    if period == 'custom':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            start_date = datetime.now().date() - timedelta(days=30)
            end_date = datetime.now().date()
    else:
        days = int(period)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
    
    # Filter orders for the period
    orders = Order.objects.filter(shop=shop, created_at__date__range=[start_date, end_date])
    
    # Calculate metrics
    total_revenue = orders.filter(status__in=['confirmed', 'sent']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_orders = orders.count()
    avg_order_value = orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
    
    # Previous period comparison
    prev_start = start_date - timedelta(days=(end_date - start_date).days)
    prev_end = start_date
    prev_orders = Order.objects.filter(shop=shop, created_at__date__range=[prev_start, prev_end])
    prev_revenue = prev_orders.filter(status__in=['confirmed', 'sent']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    prev_order_count = prev_orders.count()
    prev_aov = prev_orders.aggregate(Avg('total_amount'))['total_amount__avg'] or 0
    
    # Growth calculations
    revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
    order_growth = ((total_orders - prev_order_count) / prev_order_count * 100) if prev_order_count > 0 else 0
    aov_growth = ((avg_order_value - prev_aov) / prev_aov * 100) if prev_aov > 0 else 0
    
    # Chart data
    chart_labels = []
    revenue_data = []
    current_date = start_date
    while current_date <= end_date:
        chart_labels.append(current_date.strftime('%m/%d'))
        day_revenue = orders.filter(
            created_at__date=current_date,
            status__in=['confirmed', 'sent']
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        revenue_data.append(float(day_revenue))
        current_date += timedelta(days=1)
    
    # Status distribution
    status_data = []
    status_labels = []
    for status, label in Order.STATUS_CHOICES:
        count = orders.filter(status=status).count()
        if count > 0:
            status_data.append(count)
            status_labels.append(label)
    
    # Top products
    from django.db.models import F
    top_products = Product.objects.filter(
        shop=shop,
        orderitem__order__in=orders
    ).annotate(
        total_sold=Sum('orderitem__quantity'),
        total_revenue=Sum(F('orderitem__quantity') * F('orderitem__price'))
    ).order_by('-total_revenue')[:5]
    
    # Customer insights
    total_customers = orders.values('customer_email').distinct().count()
    repeat_customers = orders.values('customer_email').annotate(
        order_count=Count('id')
    ).filter(order_count__gt=1).count()
    new_customers = orders.filter(
        customer_email__in=orders.values('customer_email')
    ).values('customer_email').annotate(
        first_order=Count('id')
    ).filter(first_order=1).count()
    
    customer_retention = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
    conversion_rate = 15.5  # Placeholder - would need view tracking
    
    context = {
        'shop': shop,
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'revenue_growth': revenue_growth,
        'order_growth': order_growth,
        'aov_growth': aov_growth,
        'conversion_rate': conversion_rate,
        'chart_labels': json.dumps(chart_labels),
        'revenue_data': json.dumps(revenue_data),
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
        'top_products': top_products,
        'total_customers': total_customers,
        'repeat_customers': repeat_customers,
        'new_customers': new_customers,
        'customer_retention': customer_retention,
    }
    
    return render(request, 'accounts/statistics.html', context)