// Notification management functions
function loadNotifications() {
    fetch('/orders/api/notifications/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Check for new notifications
            if (data.unread_count > previousNotificationCount && previousNotificationCount > 0) {
                // Find new notifications
                const newNotifications = data.notifications.filter(n => !n.is_read).slice(0, data.unread_count - previousNotificationCount);
                newNotifications.forEach(notification => {
                    showBrowserNotification(notification.title, notification.message);
                });
            }
            
            previousNotificationCount = data.unread_count;
            updateNotificationCount(data.unread_count);
            displayNotifications(data.notifications);
        })
        .catch(error => {
            console.error('Error loading notifications:', error);
            // Hide notification count if there's an error
            const notificationCount = document.getElementById('notification-count');
            if (notificationCount) {
                notificationCount.style.display = 'none';
            }
        });
}

function updateNotificationCount(count) {
    const notificationCount = document.getElementById('notification-count');
    if (notificationCount) {
        notificationCount.textContent = count;
        if (count > 0) {
            notificationCount.style.display = 'inline-block';
        } else {
            notificationCount.style.display = 'none';
        }
    }
}

function displayNotifications(notifications) {
    const notificationList = document.getElementById('notification-list');
    if (!notificationList) return;
    
    if (notifications.length === 0) {
        notificationList.innerHTML = '<li><span class="dropdown-item-text text-muted">No notifications</span></li>';
        return;
    }
    
    let html = '';
    notifications.forEach(notification => {
        const readClass = notification.is_read ? 'text-muted' : 'fw-bold';
        const bgClass = notification.is_read ? '' : 'bg-light';
        
        html += `
            <li>
                <a class="dropdown-item ${bgClass} ${readClass}" href="#" onclick="markAsRead(${notification.id})">
                    <div class="d-flex justify-content-between">
                        <div>
                            <div class="fw-bold">${notification.title}</div>
                            <div class="small">${notification.message}</div>
                            <div class="small text-muted">${notification.created_at}</div>
                        </div>
                    </div>
                </a>
            </li>
        `;
    });
    
    notificationList.innerHTML = html;
}

function markAsRead(notificationId) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        console.error('CSRF token not found');
        return;
    }
    
    fetch(`/orders/api/mark-read/${notificationId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken.value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadNotifications();
        }
    })
    .catch(error => console.error('Error marking notification as read:', error));
}

function markAllAsRead() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        console.error('CSRF token not found');
        return;
    }
    
    fetch('/orders/api/mark-all-read/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken.value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadNotifications();
        }
    })
    .catch(error => console.error('Error marking all notifications as read:', error));
}

// Request notification permission
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Show browser notification
function showBrowserNotification(title, message) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body: message,
            icon: '/static/favicon.ico',
            badge: '/static/favicon.ico'
        });
    }
}

// Track previous notification count
let previousNotificationCount = 0;

// Load notifications on page load
document.addEventListener('DOMContentLoaded', function() {
    // Only load notifications if user is authenticated and notification elements exist
    if (document.getElementById('notification-count') && document.getElementById('notification-list')) {
        requestNotificationPermission();
        loadNotifications();
        
        // Refresh notifications every 30 seconds
        setInterval(loadNotifications, 30000);
    }
});