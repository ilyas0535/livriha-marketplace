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
            console.log('Notifications loaded:', data);
            updateNotificationCount(data.unread_count);
            displayNotifications(data.notifications);
        })
        .catch(error => {
            console.error('Error loading notifications:', error);
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
                <a class="dropdown-item ${bgClass} ${readClass}" href="${notification.click_url}">
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

// Load notifications and messages on page load
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('notification-count') && document.getElementById('notification-list')) {
        console.log('Loading notifications...');
        loadNotifications();
        setInterval(loadNotifications, 5000);
    }
    
    if (document.getElementById('unified-chat-bubble')) {
        console.log('Loading unified chat bubble...');
        loadUnifiedChatBubble();
        setInterval(loadUnifiedChatBubble, 5000);
    }
});

// Load unified chat bubble for sellers
function loadUnifiedChatBubble() {
    fetch('/accounts/api/seller-messages/')
        .then(response => response.json())
        .then(data => {
            updateUnifiedChatBubble(data.unread_count, data.messages);
        })
        .catch(error => console.error('Error loading chat bubble:', error));
}

function updateUnifiedChatBubble(unreadCount, messages) {
    const bubble = document.getElementById('unified-chat-bubble');
    const countBadge = document.getElementById('unified-chat-count');
    
    if (bubble && countBadge) {
        // Show bubble if there are messages or active chats
        if (messages.length > 0) {
            bubble.style.display = 'flex';
            
            // Update count badge
            if (unreadCount > 0) {
                countBadge.textContent = unreadCount;
                countBadge.style.display = 'inline-block';
            } else {
                countBadge.style.display = 'none';
            }
        } else {
            bubble.style.display = 'none';
        }
    }
    
    // Store messages for modal
    window.currentChatMessages = messages;
}

function openChatListModal() {
    const modal = new bootstrap.Modal(document.getElementById('chatListModal'));
    const content = document.getElementById('chat-list-content');
    
    if (window.currentChatMessages && window.currentChatMessages.length > 0) {
        let html = '';
        window.currentChatMessages.forEach(message => {
            const unreadBadge = message.unread_count > 0 ? `<span class="badge bg-danger ms-2">${message.unread_count}</span>` : '';
            
            html += `
                <div class="d-flex align-items-center p-3 border-bottom hover-bg-light" style="cursor: pointer;" onclick="openChatFromModal(${message.chat_id}, '${message.user.replace(/'/g, "\\'")}')">>
                    <div class="bg-primary rounded-circle d-flex align-items-center justify-content-center me-3" style="width: 45px; height: 45px;">
                        <i class="fas fa-user text-white"></i>
                    </div>
                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <h6 class="mb-0 fw-bold">${message.user}${unreadBadge}</h6>
                            <small class="text-muted">${message.time}</small>
                        </div>
                        <p class="mb-0 text-muted small">${message.message}</p>
                    </div>
                </div>
            `;
        });
        content.innerHTML = html;
    } else {
        content.innerHTML = '<div class="text-center text-muted p-4">No messages yet</div>';
    }
    
    modal.show();
}

function openChatFromModal(chatId, userName) {
    // Close modal first
    bootstrap.Modal.getInstance(document.getElementById('chatListModal')).hide();
    
    // Open chat window
    openChatFromNotification(chatId, userName);
}

function openChatFromNotification(chatId, userName) {
    // Extract username without product context for chat window
    const cleanUserName = userName.split(' (re:')[0];
    
    // Open chat window directly with the chat ID
    openChatWindow(chatId, cleanUserName, 0);
}

function openChatWindow(chatId, username, userId) {
    const existingWindow = document.getElementById(`chat-window-${chatId}`);
    if (existingWindow) {
        existingWindow.style.display = 'block';
        return;
    }
    
    const chatWindow = document.createElement('div');
    chatWindow.id = `chat-window-${chatId}`;
    chatWindow.className = 'position-fixed bg-white border rounded shadow';
    chatWindow.style.cssText = `
        bottom: 20px;
        right: 20px;
        width: 300px;
        height: 400px;
        z-index: 1060;
    `;
    
    chatWindow.innerHTML = `
        <div class="bg-primary text-white p-2 d-flex justify-content-between align-items-center">
            <span class="fw-bold">${username}</span>
            <div>
                <button class="btn btn-sm btn-outline-light me-1" onclick="collapseChatWindow('${chatId}', '${username}')">
                    <i class="fas fa-minus"></i>
                </button>
                <button class="btn btn-sm btn-outline-light" onclick="closeChatWindow('${chatId}')">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
        <div class="p-2" style="height: 300px; overflow-y: auto; background: #f8f9fa;" id="chatMessages-${chatId}">
        </div>
        <div class="p-2 border-top">
            <div class="input-group input-group-sm">
                <input type="text" class="form-control" id="chatInput-${chatId}" placeholder="Type message...">
                <button class="btn btn-primary" onclick="sendUserMessage('${chatId}')">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(chatWindow);
    loadUserChatMessages(chatId);
    
    // Auto-refresh messages every 3 seconds
    const refreshInterval = setInterval(() => {
        if (document.getElementById(`chat-window-${chatId}`) && document.getElementById(`chat-window-${chatId}`).style.display !== 'none') {
            loadUserChatMessages(chatId);
        } else {
            clearInterval(refreshInterval);
        }
    }, 3000);
    
    document.getElementById(`chatInput-${chatId}`).addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendUserMessage(chatId);
        }
    });
}

function closeChatWindow(chatId) {
    const window = document.getElementById(`chat-window-${chatId}`);
    const bubble = document.getElementById(`chat-bubble-${chatId}`);
    if (window) {
        window.remove();
    }
    if (bubble) {
        bubble.remove();
    }
}

function collapseChatWindow(chatId, username) {
    const window = document.getElementById(`chat-window-${chatId}`);
    if (window) {
        window.style.display = 'none';
        createChatBubble(chatId, username);
    }
}

function createChatBubble(chatId, username) {
    // Remove existing bubble if any
    const existingBubble = document.getElementById(`chat-bubble-${chatId}`);
    if (existingBubble) {
        existingBubble.remove();
    }
    
    // Count existing bubbles to position new one
    const existingBubbles = document.querySelectorAll('[id^="chat-bubble-"]');
    const bubbleIndex = existingBubbles.length;
    
    const bubble = document.createElement('div');
    bubble.id = `chat-bubble-${chatId}`;
    bubble.className = 'position-fixed bg-primary text-white rounded-circle d-flex align-items-center justify-content-center shadow';
    bubble.style.cssText = `
        bottom: 20px;
        right: ${90 + (bubbleIndex * 70)}px;
        width: 60px;
        height: 60px;
        z-index: 1050;
        cursor: pointer;
        transition: all 0.3s ease;
    `;
    
    bubble.innerHTML = `
        <div class="text-center">
            <i class="fas fa-comment fa-lg"></i>
            <div style="font-size: 10px; font-weight: bold;">${username.charAt(0).toUpperCase()}</div>
        </div>
    `;
    
    bubble.onclick = () => expandChatFromBubble(chatId, username);
    
    // Add hover effect
    bubble.onmouseenter = () => {
        bubble.style.transform = 'scale(1.1)';
        bubble.style.backgroundColor = '#0056b3';
    };
    
    bubble.onmouseleave = () => {
        bubble.style.transform = 'scale(1)';
        bubble.style.backgroundColor = '#007bff';
    };
    
    document.body.appendChild(bubble);
}

function expandChatFromBubble(chatId, username) {
    const bubble = document.getElementById(`chat-bubble-${chatId}`);
    if (bubble) {
        bubble.remove();
    }
    
    // Reopen the chat window
    openChatWindow(chatId, username, 0);
}

function sendUserMessage(chatId) {
    const input = document.getElementById(`chatInput-${chatId}`);
    const message = input.value.trim();
    if (!message) return;
    
    fetch('/accounts/send-user-message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: `chat_id=${chatId}&message=${encodeURIComponent(message)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            input.value = '';
            loadUserChatMessages(chatId);
        }
    });
}

function loadUserChatMessages(chatId) {
    fetch(`/accounts/get-user-messages/?chat_id=${chatId}`)
    .then(response => response.json())
    .then(data => {
        const chatDiv = document.getElementById(`chatMessages-${chatId}`);
        if (!chatDiv) return;
        
        chatDiv.innerHTML = '';
        
        data.messages.forEach(msg => {
            const msgDiv = document.createElement('div');
            msgDiv.className = `mb-2 ${msg.is_sender ? 'text-end' : 'text-start'}`;
            msgDiv.innerHTML = `
                <div class="d-inline-block p-3 ${msg.is_sender ? 'text-white' : 'bg-white'}" style="max-width: 75%; word-wrap: break-word; border-radius: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); ${msg.is_sender ? 'background: linear-gradient(135deg, #007bff 0%, #0056b3 100%) !important;' : 'color: #000 !important; border: 1px solid #e9ecef;'}">
                    <div style="${msg.is_sender ? 'color: #fff !important;' : 'color: #000 !important;'} font-size: 14px; line-height: 1.4;">${msg.message}</div>
                    <div style="${msg.is_sender ? 'color: rgba(255,255,255,0.8) !important;' : 'color: #6c757d !important;'} font-size: 11px; margin-top: 4px; text-align: right;">${msg.time}</div>
                </div>
            `;
            chatDiv.appendChild(msgDiv);
        });
        
        chatDiv.scrollTop = chatDiv.scrollHeight;
    })
    .catch(error => {
        console.error('Error loading messages:', error);
    });
}