from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from orders.models import Notification
from products.models import Product
import random

class Command(BaseCommand):
    help = 'Send promotional notifications to buyers'

    def handle(self, *args, **options):
        buyers = User.objects.filter(is_seller=False, is_active=True)
        
        # Get trending products (most ordered in last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        trending_products = Product.objects.filter(
            orderitem__order__created_at__gte=week_ago
        ).distinct()[:5]
        
        # Get products on sale
        sale_products = Product.objects.filter(old_price__isnull=False)[:5]
        
        notifications_sent = 0
        
        for buyer in buyers:
            # Send different types of notifications randomly
            notification_type = random.choice(['trending', 'sale', 'welcome_back'])
            
            if notification_type == 'trending' and trending_products:
                product = random.choice(trending_products)
                Notification.objects.create(
                    user=buyer,
                    type='order_update',
                    title='🔥 Trending Now!',
                    message=f'Check out "{product.name}" - everyone\'s buying it! Starting at ${product.price}'
                )
                notifications_sent += 1
                
            elif notification_type == 'sale' and sale_products:
                product = random.choice(sale_products)
                discount = int(((product.old_price - product.price) / product.old_price) * 100)
                Notification.objects.create(
                    user=buyer,
                    type='order_update',
                    title='💰 Special Discount!',
                    message=f'Save {discount}% on "{product.name}" - Was ${product.old_price}, now ${product.price}!'
                )
                notifications_sent += 1
                
            elif notification_type == 'welcome_back':
                Notification.objects.create(
                    user=buyer,
                    type='order_update',
                    title='👋 Welcome back!',
                    message='Discover new products and amazing deals. Check out what\'s new in our marketplace!'
                )
                notifications_sent += 1
        
        self.stdout.write(f'Sent {notifications_sent} promotional notifications to buyers')