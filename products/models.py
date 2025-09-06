from django.db import models
from django.contrib.auth import get_user_model
from shops.models import Shop

User = get_user_model()

class Category(models.Model):
    CATEGORY_CHOICES = [
        ('Electronics', 'Electronics'),
        ('Clothing', 'Clothing'),
        ('Home & Garden', 'Home & Garden'),
        ('Sports', 'Sports'),
        ('Books', 'Books'),
        ('Beauty', 'Beauty'),
        ('Toys', 'Toys'),
        ('Food', 'Food'),
        ('Automotive', 'Automotive'),
        ('Health', 'Health'),
        ('Other', 'Other'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    
    @classmethod
    def get_all_categories(cls):
        return [{'id': i+1, 'name': choice[0]} for i, choice in enumerate(cls.CATEGORY_CHOICES)]
    
    def __str__(self):
        return self.name

class Product(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=Category.CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    @property
    def is_on_sale(self):
        return self.old_price and self.old_price > self.price
    
    @property
    def is_out_of_stock(self):
        return self.quantity == 0
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold
    
    @property
    def sales_rating(self):
        from orders.models import OrderItem
        from django.db.models import Sum
        
        # Get sales for this product
        product_sales = OrderItem.objects.filter(product=self).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Get all products with their sales, ordered by sales descending
        all_products = Product.objects.annotate(
            total_sales=Sum('orderitem__quantity')
        ).order_by('-total_sales')
        
        total_products = all_products.count()
        if total_products == 0:
            return 1
        
        # Find this product's rank (1-based)
        product_rank = 1
        for i, product in enumerate(all_products, 1):
            if product.id == self.id:
                product_rank = i
                break
        
        # Convert rank to 5-star rating (rank 1 = best = 5 stars)
        # Calculate which quintile this product falls into
        quintile_size = max(1, total_products // 5)
        
        if product_rank <= quintile_size:  # Top quintile
            return 5
        elif product_rank <= quintile_size * 2:  # Second quintile
            return 4
        elif product_rank <= quintile_size * 3:  # Third quintile
            return 3
        elif product_rank <= quintile_size * 4:  # Fourth quintile
            return 2
        else:  # Bottom quintile
            return 1
    
    @property
    def sales_count(self):
        from orders.models import OrderItem
        from django.db.models import Sum
        return OrderItem.objects.filter(product=self).aggregate(total=Sum('quantity'))['total'] or 0

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)  # e.g., "Size", "Color"
    value = models.CharField(max_length=100)  # e.g., "Large", "Red"
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=0)

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product')

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

