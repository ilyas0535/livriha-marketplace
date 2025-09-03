from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import SubscriptionPlan, Subscription, PaymentConfirmation
from .forms import PaymentForm

@login_required
def subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    user_subscription = getattr(request.user, 'subscription', None)
    return render(request, 'subscriptions/plans.html', {
        'plans': plans,
        'user_subscription': user_subscription
    })

@login_required
def purchase_plan(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            # Create payment confirmation
            payment = PaymentConfirmation.objects.create(
                user=request.user,
                plan=plan,
                binance_user=form.cleaned_data['binance_user'],
                binance_email=form.cleaned_data['binance_email'],
                amount=plan.price
            )
            
            # Send email to admin
            send_mail(
                subject=f'New Payment Confirmation - {request.user.username}',
                message=f'''
Payment Details:
- User: {request.user.username} ({request.user.email})
- Plan: {plan.get_name_display()}
- Amount: ${plan.price}
- Binance User: {form.cleaned_data['binance_user']}
- Binance Email: {form.cleaned_data['binance_email']}
- Date: {payment.created_at}

Please verify the payment and activate the subscription.
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['protechdza@gmail.com'],
                fail_silently=False,
            )
            
            messages.success(request, 'Payment confirmation sent! We will activate your subscription once payment is verified.')
            return redirect('subscription_plans')
    else:
        form = PaymentForm()
    
    return render(request, 'subscriptions/purchase.html', {
        'plan': plan,
        'form': form
    })

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