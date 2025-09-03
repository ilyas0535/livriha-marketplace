# Livriha - Multi-Vendor E-commerce Platform

A Django-based marketplace where users can create their own online shops and sell products.

## Features

- **Multi-vendor marketplace**: Users can create their own shops
- **Product management**: Upload photos, set prices, manage variants and inventory
- **Shopping cart & wishlist**: Customers can add products to cart or wishlist
- **Order management**: Track orders with statuses (draft, confirmed, sent, cancelled)
- **Seller dashboard**: Analytics showing income, orders, and business metrics
- **Notification system**: Alerts for new orders and low stock
- **Email verification**: Confirm user registration via email
- **Discount system**: Show old and new prices for sales
- **Custom shop URLs**: Each shop gets a unique URL with shop name

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Create superuser:
```bash
python manage.py createsuperuser
```

4. Run the development server:
```bash
python manage.py runserver
```

## Usage

1. Register as a user (check "I want to sell products" to become a seller)
2. Verify your email (check console for verification link in development)
3. Create your shop from the dashboard
4. Add products through Django admin
5. Share your shop URL: `/shop/your-shop-name/`

## Email Configuration

The app is configured to use Gmail SMTP with the provided credentials. For production, update the email settings in `settings.py`.

## Project Structure

- `accounts/` - User authentication and dashboard
- `shops/` - Shop creation and management
- `products/` - Product catalog, cart, and wishlist
- `orders/` - Order processing and notifications
- `templates/` - HTML templates
- `static/` - CSS, JS, and static files
- `media/` - User uploaded files