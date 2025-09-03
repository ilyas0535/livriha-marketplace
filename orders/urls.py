from django.urls import path
from . import views
from . import notification_views

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),
    path('create/', views.create_order, name='create_order'),
    path('payment/<int:order_id>/<str:payment_method>/', views.payment_gateway, name='payment_gateway'),
    path('upload-proof/<int:order_id>/', views.upload_payment_proof, name='upload_payment_proof'),
    path('payment-success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('update-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('api/notifications/', notification_views.get_notifications, name='get_notifications'),
    path('api/mark-read/<int:notification_id>/', notification_views.mark_notification_read, name='mark_notification_read'),
    path('api/mark-all-read/', notification_views.mark_all_notifications_read, name='mark_all_notifications_read'),
]