from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import json
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

def send_browser_notification(user, title, message, order_id=None):
    """Send browser push notification"""
    # This would integrate with a service like Firebase Cloud Messaging
    # For now, we'll simulate with a simple implementation
    notification_data = {
        'title': title,
        'message': message,
        'order_id': order_id,
        'timestamp': str(timezone.now())
    }
    
    # In production, you would send this to FCM or similar service
    print(f"Browser notification sent to {user.email}: {title} - {message}")

def send_email_notification(to_email, subject, message):
    """Send email notification using Brevo API"""
    # Convert plain text to HTML
    html_content = message.replace('\n', '<br>')
    return send_brevo_email(to_email, subject, html_content)

def notify_seller_new_order(order):
    """Notify seller about new order"""
    seller = order.shop.owner
    
    # Browser notification
    title = "New Order Received!"
    message = f"Order #{order.id} for ${order.total_amount} from {order.customer_name}"
    send_browser_notification(seller, title, message, order.id)
    
    # Email notification
    email_subject = f"New Order #{order.order_number} - {order.shop.name}"
    email_message = f"""
Dear {seller.username},

You have received a new order!

Order Details:
- Order ID: #{order.order_number}
- Customer: {order.customer_name}
- Email: {order.customer_email}
- Phone: {order.customer_phone}
- Address: {order.customer_address}
- Total Amount: ${order.total_amount}

Items:
"""
    for item in order.items.all():
        email_message += f"- {item.product.name} x{item.quantity} - ${item.price}\n"
    
    email_message += f"""
Please log in to your dashboard to manage this order.

Cordialement,
Livriha
"""
    
    send_email_notification(seller.email, email_subject, email_message)

def notify_buyer_order_placed(order):
    """Notify buyer about order placement"""
    customer_email = order.customer_email or (order.customer.email if order.customer else None)
    customer_name = order.customer_name or (order.customer.username if order.customer else "Client")
    
    if not customer_email:
        return
    
    email_subject = f"Order #{order.order_number} Confirmed - {order.shop.name}"
    email_message = f"""
Hello {customer_name},

Your order has been placed successfully!

Order Details:
- Order Number: #{order.order_number}
- Shop: {order.shop.name}
- Total Amount: ${order.total_amount}
- Payment Method: Cash on Delivery

Ordered Items:
"""
    for item in order.items.all():
        email_message += f"- {item.product.name} x{item.quantity} - ${item.price}\n"
    
    email_message += f"""

You will receive confirmation emails and updates on your order status.

Thank you for your trust!

Best regards,
{order.shop.name}
"""
    
    send_email_notification(customer_email, email_subject, email_message)

def notify_customer_order_update(order, old_status, new_status):
    """Notify customer about order status update"""
    customer_email = order.customer_email or (order.customer.email if order.customer else None)
    customer_name = order.customer_name or (order.customer.username if order.customer else "Customer")
    
    if not customer_email:
        return
    
    # Email notification
    status_messages = {
        'confirmed': 'Your order has been confirmed and is being prepared.',
        'sent': 'Your order has been shipped and is on its way!',
        'cancelled': 'Your order has been cancelled.',
        'returned': 'Your order return has been processed.'
    }
    
    email_subject = f"Order #{order.order_number} Status Update - {new_status.title()}"
    email_message = f"""
Dear {customer_name},

Your order status has been updated.

Order Details:
- Order ID: #{order.order_number}
- Shop: {order.shop.name}
- Status: {new_status.title()}
- Total: ${order.total_amount}

{status_messages.get(new_status, 'Your order status has been updated.')}

Thank you for shopping with us!

Cordialement,
{order.shop.name}
"""
    
    send_email_notification(customer_email, email_subject, email_message)