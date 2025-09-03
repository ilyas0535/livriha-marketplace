from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class SubscriptionPlan(models.Model):
    PLAN_CHOICES = [
        ('monthly', 'Monthly - $5'),
        ('6months', '6 Months - $20 (Save $10)'),
        ('yearly', 'Yearly - $50 (Save $20)'),
    ]
    
    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    
    def __str__(self):
        return dict(self.PLAN_CHOICES)[self.name]

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    binance_user = models.CharField(max_length=100)
    binance_email = models.EmailField()
    
    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.end_date
    
    @property
    def days_until_expiry(self):
        return (self.end_date - timezone.now()).days
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

class PaymentConfirmation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    binance_user = models.CharField(max_length=100)
    binance_email = models.EmailField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    is_confirmed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Payment {self.user.username} - ${self.amount}"