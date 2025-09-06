from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()

class Shop(models.Model):
    CHECKOUT_METHODS = [
        ('cash_on_delivery', 'Cash on Delivery'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('credit_card', 'Credit Card'),
    ]
    
    REMINDER_PERIODS = [
        ('8h', '8 Hours'),
        ('12h', '12 Hours'),
        ('1d', '1 Day'),
        ('2d', '2 Days'),
        ('3d', '3 Days'),
    ]
    
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='shop_logos/', blank=True)
    checkout_methods = models.JSONField(default=list, blank=True)
    
    # Payment gateway configurations
    paypal_client_id = models.CharField(max_length=200, blank=True)
    paypal_client_secret = models.CharField(max_length=200, blank=True)
    stripe_public_key = models.CharField(max_length=200, blank=True)
    stripe_secret_key = models.CharField(max_length=200, blank=True)
    bank_account_info = models.TextField(blank=True)
    order_reminder_period = models.CharField(max_length=3, choices=REMINDER_PERIODS, default='1d')
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Shop.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return f'/shop/{self.slug}/'
    
    @property
    def sales_rating(self):
        from orders.models import OrderItem
        from django.db.models import Sum
        
        # Get all shops with their sales, ordered by sales descending
        all_shops = Shop.objects.annotate(
            total_sales=Sum('product__orderitem__quantity')
        ).order_by('-total_sales')
        
        total_shops = all_shops.count()
        if total_shops == 0:
            return 1
        
        # Find this shop's rank (1-based)
        shop_rank = 1
        for i, shop in enumerate(all_shops, 1):
            if shop.id == self.id:
                shop_rank = i
                break
        
        # Convert rank to 5-star rating (rank 1 = best = 5 stars)
        # Calculate which quintile this shop falls into
        quintile_size = max(1, total_shops // 5)
        
        if shop_rank <= quintile_size:  # Top quintile
            return 5
        elif shop_rank <= quintile_size * 2:  # Second quintile
            return 4
        elif shop_rank <= quintile_size * 3:  # Third quintile
            return 3
        elif shop_rank <= quintile_size * 4:  # Fourth quintile
            return 2
        else:  # Bottom quintile
            return 1
    
    @property
    def sales_count(self):
        from orders.models import OrderItem
        from django.db.models import Sum
        return OrderItem.objects.filter(product__shop=self).aggregate(total=Sum('quantity'))['total'] or 0