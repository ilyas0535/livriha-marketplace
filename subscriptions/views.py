from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPlan, Subscription, PaymentConfirmation
from .forms import PaymentForm

@login_required
def subscription_plans(request):
    try:
        plans = SubscriptionPlan.objects.all()
        user_subscription = getattr(request.user, 'subscription', None)
    except:
        # Tables don't exist yet, create default plans
        plans = []
        user_subscription = None
        
    return render(request, 'subscriptions/plans.html', {
        'plans': plans,
        'user_subscription': user_subscription
    })

@login_required
def purchase_plan(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    if request.method == 'POST':
        # Create payment confirmation without form
        payment = PaymentConfirmation.objects.create(
            user=request.user,
            plan=plan,
            binance_user=request.user.username,
            binance_email=request.user.email,
            amount=plan.price
        )
        
        # Send email to admin
        try:
            send_mail(
                subject=f'New Payment Confirmation - {request.user.username}',
                message=f'''
Payment Details:
- User: {request.user.username} ({request.user.email})
- Plan: {plan.get_name_display()}
- Amount: ${plan.price}
- User Email: {request.user.email}
- Date: {payment.created_at}

Please verify the payment and activate the subscription.
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['protechdza@gmail.com'],
                fail_silently=True,
            )
        except:
            pass
        
        messages.success(request, 'Payment confirmation sent! We will activate your subscription once payment is verified.')
        return redirect('subscription_plans')
    
    return render(request, 'subscriptions/purchase.html', {'plan': plan})

@login_required
def admin_dashboard(request):
    if request.user.email != 'protechdza@gmail.com':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    pending_payments = PaymentConfirmation.objects.filter(is_confirmed=False)
    all_subscriptions = Subscription.objects.all().order_by('-start_date')
    
    return render(request, 'subscriptions/admin_dashboard.html', {
        'pending_payments': pending_payments,
        'subscriptions': all_subscriptions
    })

@login_required
def activate_subscription(request, payment_id):
    if request.user.email != 'protechdza@gmail.com':
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    payment = get_object_or_404(PaymentConfirmation, id=payment_id)
    
    # Create or update subscription
    subscription, created = Subscription.objects.get_or_create(
        user=payment.user,
        defaults={
            'plan': payment.plan,
            'binance_user': payment.binance_user,
            'binance_email': payment.binance_email
        }
    )
    
    if not created:
        # Extend existing subscription
        subscription.plan = payment.plan
        subscription.end_date = subscription.end_date + timedelta(days=payment.plan.duration_days)
        subscription.is_active = True
        subscription.save()
    
    payment.is_confirmed = True
    payment.save()
    
    messages.success(request, f'Subscription activated for {payment.user.username}')
    return redirect('admin_dashboard')

@login_required
def confirm_payment(request, plan_id):
    if request.method == 'POST':
        # Handle fallback plans
        plan_names = {1: 'Monthly - $5', 2: '6 Months - $20', 3: 'Yearly - $50'}
        plan_prices = {1: 5, 2: 20, 3: 50}
        
        plan_name = plan_names.get(plan_id, 'Unknown Plan')
        plan_price = plan_prices.get(plan_id, 0)
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            plan_name = plan.get_name_display()
            plan_price = plan.price
            
            # Create payment confirmation
            PaymentConfirmation.objects.create(
                user=request.user,
                plan=plan,
                binance_user=request.user.username,
                binance_email=request.user.email,
                amount=plan.price
            )
        except:
            pass
        
        # Send email to admin
        try:
            send_mail(
                subject=f'Payment Complete - {request.user.username}',
                message=f'''
Payment Confirmation:
- User: {request.user.username}
- Email: {request.user.email}
- Plan: {plan_name}
- Amount: ${plan_price}
- Date: {timezone.now()}

Please verify payment and activate subscription.
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['protechdza@gmail.com'],
                fail_silently=True,
            )
        except:
            pass
        
        messages.success(request, 'Payment confirmation sent! Your subscription will be activated once verified.')
    
    return redirect('subscription_plans')