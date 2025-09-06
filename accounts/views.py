from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.http import JsonResponse
from .models import User, SupportMessage
from shops.models import Shop
from orders.models import Order, Notification
from products.models import Product
import uuid
import requests
import os

def send_brevo_email(to_email, subject, html_content):
    """Helper function to send emails via Brevo API"""
    try:
        api_url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": os.environ.get('BREVO_API_KEY', 'your-brevo-api-key'),
            "content-type": "application/json"
        }
        
        payload = {
            "sender": {"name": "Livriha", "email": "protechdza@gmail.com"},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        return response.status_code == 201
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def register(request):
    upgrade_mode = request.GET.get('upgrade') == 'seller'
    
    if request.method == 'POST':
        if upgrade_mode and request.user.is_authenticated:
            # Upgrade existing user to seller
            request.user.is_seller = True
            request.user.save()
            messages.success(request, 'Account upgraded to seller! You can now create your shop.')
            return redirect('create_shop')
        
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'accounts/register.html')
        
        # Create inactive user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_seller=True,
            is_active=False
        )
        
        # Generate verification token
        token = str(uuid.uuid4())
        user.verification_token = token
        user.save()
        
        # Send email using Brevo API
        verification_url = request.build_absolute_uri(reverse('verify_email', args=[token]))
        email_sent = False
        
        # Send verification email
        html_content = f"<p>Welcome to Livriha!</p><p>Please click the link below to verify your email and activate your account:</p><p><a href='{verification_url}'>Verify Email</a></p><p>Thank you!</p>"
        email_sent = send_brevo_email(email, "Verify your email - Livriha", html_content)
        
        if email_sent:
            print(f"Email sent successfully to {email}")
        else:
            print(f"Email sending failed for {email}")
            
        if not email_sent:
            print(f"Email failed, activating user {email} immediately")
            # Activate user immediately if email fails
            user.is_active = True
            user.email_verified = True
            user.save()
        
        if email_sent:
            messages.success(request, 'Registration successful! Please check your email to verify your account.')
        else:
            messages.success(request, 'Registration successful! Email verification failed, but your account is active. You can log in now.')
        

        return redirect('login')
    
    return render(request, 'accounts/register.html', {'upgrade_mode': upgrade_mode})

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        # Try to find user by email first
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user and user.is_active:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials or account not activated')
    
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
            
            # Send password reset email
            html_content = f"<p>Click the link below to reset your password:</p><p><a href='{reset_url}'>Reset Password</a></p><p>If you did not request this, please ignore this email.</p>"
            send_brevo_email(email, "Reset your password - Livriha", html_content)
            messages.success(request, 'Password reset link sent to your email.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'accounts/forgot_password.html')

def check_username(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        username = data.get('username')
        exists = User.objects.filter(username=username).exists()
        return JsonResponse({'exists': exists})
    return JsonResponse({'error': 'Invalid request'})

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
        notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
        
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
            'notifications': notifications[:5],
        }
    else:
        # User without shop - show customer orders
        orders = Order.objects.filter(customer=request.user).order_by('-created_at')
        notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
        
        context = {
            'orders': orders,
            'notifications': notifications,
            'shop': None
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
    if prev_revenue > 0:
        revenue_growth = ((total_revenue - prev_revenue) / prev_revenue * 100)
    else:
        revenue_growth = 100 if total_revenue > 0 else 0
    
    if prev_order_count > 0:
        order_growth = ((total_orders - prev_order_count) / prev_order_count * 100)
    else:
        order_growth = 100 if total_orders > 0 else 0
    
    if prev_aov > 0:
        aov_growth = ((avg_order_value - prev_aov) / prev_aov * 100)
    else:
        aov_growth = 100 if avg_order_value > 0 else 0
    
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

@login_required
def support_messages(request):
    if request.user.email != 'protechdza@gmail.com':
        messages.error(request, 'Access denied')
        return redirect('dashboard')
    
    messages = SupportMessage.objects.all().order_by('-created_at')
    
    # Mark as read when viewed
    if request.GET.get('mark_read'):
        msg_id = request.GET.get('mark_read')
        try:
            msg = SupportMessage.objects.get(id=msg_id)
            msg.is_read = True
            msg.save()
        except SupportMessage.DoesNotExist:
            pass
    
    return render(request, 'accounts/support_messages.html', {'support_messages': messages})

@login_required
def reply_support(request):
    if request.user.email != 'protechdza@gmail.com':
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        reply_text = request.POST.get('reply')
        
        try:
            original_message = SupportMessage.objects.get(id=message_id)
            if original_message.user:
                # Create notification for the user
                from orders.models import Notification
                Notification.objects.create(
                    user=original_message.user,
                    title='Support Reply',
                    message=f'Admin replied to your message "{original_message.subject}": {reply_text[:100]}...'
                )
                return JsonResponse({'success': True, 'message': 'Reply sent as notification'})
            else:
                return JsonResponse({'success': False, 'message': 'Cannot reply to anonymous user'})
        except SupportMessage.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Message not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': 'Error sending reply'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def contact_support(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Save to database (for guests only)
        support_msg = SupportMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message,
            user=None  # Always None for guest messages
        )
        
        # Send email to admin
        admin_email = 'protechdza@gmail.com'
        email_subject = f'Support Request: {subject}'
        email_body = f'''
        New support message from {name} ({email}):
        
        Subject: {subject}
        Message: {message}
        
        Time: {support_msg.created_at}
        '''
        
        try:
            send_mail(email_subject, email_body, 'noreply@livriha.store', [admin_email])
        except:
            pass
        
        return JsonResponse({'success': True, 'message': 'Message sent successfully!'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def get_or_create_chat(request):
    if request.method == 'POST':
        # Get or create a support message for live chat
        support_msg, created = SupportMessage.objects.get_or_create(
            user=request.user,
            subject='Live Chat Session',
            defaults={
                'name': request.user.username,
                'email': request.user.email,
                'message': 'Live chat session started'
            }
        )
        
        # Notify admin of new chat session
        if created:
            try:
                admin_user = User.objects.get(email='protechdza@gmail.com')
                from orders.models import Notification
                Notification.objects.create(
                    user=admin_user,
                    title='New Live Chat',
                    message=f'{request.user.username} started a live chat session'
                )
            except (User.DoesNotExist, ImportError, TypeError):
                pass
        
        return JsonResponse({'success': True, 'support_id': support_msg.id})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def send_chat_message(request):
    if request.method == 'POST':
        support_id = request.POST.get('support_id')
        message = request.POST.get('message')
        
        try:
            support_msg = SupportMessage.objects.get(id=support_id)
            from .models import ChatMessage
            
            if request.user == support_msg.user or request.user.email == 'protechdza@gmail.com':
                ChatMessage.objects.create(
                    support_message=support_msg,
                    sender=request.user,
                    message=message,
                    is_admin=(request.user.email == 'protechdza@gmail.com')
                )
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': 'Access denied'})
        except SupportMessage.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Support message not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def get_chat_messages(request):
    support_id = request.GET.get('support_id')
    
    try:
        support_msg = SupportMessage.objects.get(id=support_id)
        from .models import ChatMessage
        
        if request.user == support_msg.user or request.user.email == 'protechdza@gmail.com':
            messages = ChatMessage.objects.filter(support_message=support_msg)
            chat_data = []
            
            for msg in messages:
                chat_data.append({
                    'sender': 'Support' if msg.is_admin else msg.sender.username,
                    'message': msg.message,
                    'time': msg.created_at.strftime('%H:%M'),
                    'is_admin': msg.is_admin
                })
            
            return JsonResponse({'messages': chat_data})
        else:
            return JsonResponse({'messages': []})
    except SupportMessage.DoesNotExist:
        return JsonResponse({'messages': []})

@login_required
def get_support_chats(request):
    if request.user.email != 'protechdza@gmail.com':
        return JsonResponse({'chats': [], 'unread_count': 0})
    
    # Get all active chat sessions
    from .models import ChatMessage
    support_messages = SupportMessage.objects.filter(
        user__isnull=False,
        subject='Live Chat Session'
    ).order_by('-created_at')
    
    chats = []
    total_unread = 0
    
    for support_msg in support_messages:
        last_message = ChatMessage.objects.filter(
            support_message=support_msg
        ).order_by('-created_at').first()
        
        if last_message:
            unread_count = ChatMessage.objects.filter(
                support_message=support_msg,
                is_admin=False,
                created_at__gt=last_message.created_at if last_message.is_admin else last_message.created_at
            ).count()
            
            chats.append({
                'id': support_msg.id,
                'user': support_msg.user.username,
                'last_message': last_message.message[:50] + '...' if len(last_message.message) > 50 else last_message.message,
                'unread_count': unread_count
            })
            
            total_unread += unread_count
    
    return JsonResponse({
        'chats': chats[:10],  # Limit to 10 recent chats
        'unread_count': total_unread
    })

@login_required
def send_broadcast(request):
    print(f"BROADCAST VIEW CALLED - Method: {request.method}, User: {request.user.email}")
    
    if request.user.email != 'protechdza@gmail.com':
        print("ACCESS DENIED - Not admin user")
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    if request.method == 'POST':
        broadcast_type = request.POST.get('broadcast_type')
        title = request.POST.get('title')
        message = request.POST.get('message')
        target = request.POST.get('target')
        
        print(f"Broadcast request: type={broadcast_type}, title={title}, target={target}")
        
        # Filter users based on target
        if target == 'sellers':
            users = User.objects.filter(is_seller=True)
        elif target == 'buyers':
            users = User.objects.filter(is_seller=False)
        else:  # all
            users = User.objects.all()
        
        print(f"Found {users.count()} users to notify")
        count = 0
        
        if broadcast_type == 'notification':
            # Send in-app notifications
            from orders.models import Notification
            for user in users:
                try:
                    notification = Notification.objects.create(
                        user=user,
                        type='order_update',
                        title=title,
                        message=message
                    )
                    print(f"Created notification {notification.id} for user {user.username}")
                    count += 1
                except Exception as e:
                    print(f"Error creating notification for user {user.username}: {e}")
                    continue
        else:  # email
            # Send emails
            from django.core.mail import send_mail
            email_list = [user.email for user in users if user.email]
            
            try:
                send_mail(
                    title,
                    message,
                    'noreply@livriha.store',
                    email_list,
                    fail_silently=False
                )
                count = len(email_list)
            except Exception as e:
                print(f"Email sending failed: {e}")
                return JsonResponse({'success': False, 'message': 'Email sending failed'})
        
        print(f"Broadcast completed. Sent to {count} users.")
        return JsonResponse({'success': True, 'count': count})
    
    print("Invalid request method")
    return JsonResponse({'success': False, 'message': 'Invalid request'})