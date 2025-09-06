from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('check-username/', views.check_username, name='check_username'),
    path('contact-support/', views.contact_support, name='contact_support'),
    path('support-messages/', views.support_messages, name='support_messages'),
    path('reply-support/', views.reply_support, name='reply_support'),
    path('send-chat-message/', views.send_chat_message, name='send_chat_message'),
    path('get-chat-messages/', views.get_chat_messages, name='get_chat_messages'),
    path('get-or-create-chat/', views.get_or_create_chat, name='get_or_create_chat'),
    path('get-support-chats/', views.get_support_chats, name='get_support_chats'),
    path('send-broadcast/', views.send_broadcast, name='send_broadcast'),
    path('start-user-chat/', views.start_user_chat, name='start_user_chat'),
    path('send-user-message/', views.send_user_message, name='send_user_message'),
    path('get-user-messages/', views.get_user_messages, name='get_user_messages'),
    path('user-messages/', views.user_messages, name='user_messages'),
    path('api/seller-messages/', views.get_seller_messages, name='get_seller_messages'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('statistics/', views.shop_statistics, name='shop_statistics'),
]