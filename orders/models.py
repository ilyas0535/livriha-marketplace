from django.db import models
from django.contrib.auth import get_user_model
from shops.models import Shop
from products.models import Product

User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Customer information for guest users
    customer_name = models.CharField(max_length=100, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_address = models.TextField(blank=True)
    
    # Payment information
    payment_method = models.CharField(max_length=50, blank=True)
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Get the highest ID and add to base number
            last_order = Order.objects.order_by('-id').first()
            if last_order:
                self.order_number = str(535000 + last_order.id + 1)
            else:
                self.order_number = '0535001'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order #{self.order_number} - {self.shop.name}"

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-changed_at']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_order', 'New Order'),
        ('low_stock', 'Low Stock'),
        ('order_update', 'Order Update'),
        ('support_reply', 'Support Reply'),
        ('general', 'General'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Link to related objects
    related_order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    related_product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    related_url = models.CharField(max_length=500, blank=True)  # Custom URL for other objects
    
    def get_redirect_url(self):
        if self.related_order:
            return f'/accounts/dashboard/?order={self.related_order.id}'
        elif self.related_product:
            return f'/products/{self.related_product.id}/'
        elif self.related_url:
            if self.related_url.startswith('javascript:'):
                return '/accounts/dashboard/?open_support=1'
            return self.related_url
        else:
            return '/accounts/dashboard/'

    def __str__(self):
        return f"{self.title} - {self.user.username}"