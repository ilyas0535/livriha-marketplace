from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from orders.models import Order, Notification
from orders.notifications import send_email_notification

class Command(BaseCommand):
    help = 'Send reminder emails for confirmed orders that haven\'t been sent'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Get all confirmed orders
        confirmed_orders = Order.objects.filter(status='confirmed')
        
        for order in confirmed_orders:
            shop = order.shop
            reminder_period = shop.order_reminder_period
            
            # Calculate reminder time based on shop setting
            if reminder_period == '8h':
                reminder_time = timedelta(hours=8)
            elif reminder_period == '12h':
                reminder_time = timedelta(hours=12)
            elif reminder_period == '1d':
                reminder_time = timedelta(days=1)
            elif reminder_period == '2d':
                reminder_time = timedelta(days=2)
            elif reminder_period == '3d':
                reminder_time = timedelta(days=3)
            else:
                reminder_time = timedelta(days=1)
            
            # Check if reminder time has passed
            if now - order.updated_at >= reminder_time:
                # Send reminder email
                subject = f'Reminder: Order #{order.order_number} needs to be sent'
                message = f'''
Dear {shop.owner.username},

This is a reminder that Order #{order.order_number} has been confirmed for {reminder_period} but hasn't been sent yet.

Order Details:
- Customer: {order.customer_name}
- Total: ${order.total_amount}
- Status: {order.get_status_display()}

Please update the order status to "Sent" once you've shipped it.

Best regards,
À la livraison
'''
                
                send_email_notification(shop.owner.email, subject, message)
                
                # Create notification
                Notification.objects.create(
                    user=shop.owner,
                    type='order_update',
                    title=f'Reminder: Order #{order.order_number}',
                    message=f'Order #{order.order_number} needs to be sent (confirmed {reminder_period} ago)'
                )
                
                self.stdout.write(f'Sent reminder for order #{order.order_number}')