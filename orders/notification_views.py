from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification

@login_required
def get_notifications(request):
    all_notifications = Notification.objects.filter(user=request.user)
    unread_count = all_notifications.filter(is_read=False).count()
    notifications = all_notifications.order_by('-created_at')[:10]
    
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%b %d, %Y %H:%M'),
            'type': notification.type
        })
    
    return JsonResponse({
        'notifications': notification_data,
        'unread_count': unread_count
    })

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})

@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})