// AI客服系统前端逻辑 - 优化版

// ==================== 全局变量 ====================
let sessionId = generateSessionId();
let isConnected = false;
let currentTicketId = null;
let isAITyping = false;
let messageQueue = [];

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
    setupEventListeners();
    updateCharCount();
});

// 生成会话ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// 初始化聊天
function initializeChat() {
    console.log('初始化AI客服系统');
    console.log('会话ID:', sessionId);
    isConnected = true;
    updateConnectionStatus('在线');
}

// 设置事件监听器
function setupEventListeners() {
    const messageInput = document.getElementById('messageInput');
    
    // 输入框回车发送
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 字符计数
    messageInput.addEventListener('input', function() {
        updateCharCount();
    });
}

// 更新字符计数
function updateCharCount() {
    const messageInput = document.getElementById('messageInput');
    const charCount = document.getElementById('charCount');
    const length = messageInput.value.length;
    
    charCount.textContent = `${length}/500`;
    charCount.style.color = length > 500 ? '#ff4757' : '#999';
}

// 更新连接状态
function updateConnectionStatus(status) {
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        statusElement.textContent = status;
    }
}

// ==================== 发送消息 ====================
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message || message.length > 500) {
        if (message.length > 500) {
            showToast('消息内容不能超过500字符');
        }
        return;
    }
    
    // 清空输入框
    messageInput.value = '';
    updateCharCount();
    
    // 隐藏快捷回复
    hideQuickReplies();
    
    // 显示用户消息
    const tempMessageId = displayMessage(message, 'user', 'sending');
    
    // 发送到后端
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: message
            })
        });
        
        const data = await response.json();
        
        // 更新消息状态为已发送
        updateMessageStatus(tempMessageId, 'sent');
        
        if (data.success) {
            // 显示AI响应（带打字机效果）
            await displayAITyping();
            await displayMessageWithTyping(data.response, 'ai');
            
            // 检查是否需要显示转人工建议
            if (data.transfer_suggestion) {
                // 显示转人工建议消息
                setTimeout(() => {
                    displayTransferSuggestion(data.transfer_suggestion);
                }, 500);
            }
            
            // 检查用户是否主动要求转人工
            if (data.user_requested_transfer) {
                setTimeout(() => {
                    displayMessage('好的，正在为您转接人工客服...', 'system');
                }, 1000);
            }
        } else {
            updateMessageStatus(tempMessageId, 'failed');
            displayMessage('抱歉，我暂时无法回答您的问题。', 'ai');
        }
        
    } catch (error) {
        console.error('发送消息失败:', error);
        updateMessageStatus(tempMessageId, 'failed');
        displayMessage('网络连接失败，请稍后再试。', 'system');
    }
}

// 显示用户消息
function displayMessage(message, type, status = 'sent') {
    const chatMessages = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const messageP = document.createElement('p');
    messageP.textContent = message;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = getCurrentTime();
    
    // 状态指示器（仅用户消息）
    if (type === 'user') {
        const statusDiv = document.createElement('div');
        statusDiv.className = 'message-status';
        statusDiv.innerHTML = getStatusIcon(status);
        statusDiv.id = `status-${Date.now()}`;
        messageDiv.appendChild(statusDiv);
    }
    
    contentDiv.appendChild(messageP);
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    
    // 消息操作按钮
    const actionsDiv = createMessageActions(message);
    messageDiv.appendChild(actionsDiv);
    
    chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    scrollToBottom();
    
    // 返回状态元素ID
    return type === 'user' ? `status-${Date.now()}` : null;
}

// 创建消息操作按钮
function createMessageActions(message) {
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'message-actions';
    
    // 复制按钮
    const copyBtn = document.createElement('button');
    copyBtn.innerHTML = '📋';
    copyBtn.title = '复制消息';
    copyBtn.onclick = function() {
        copyToClipboard(message);
        showToast('已复制到剪贴板');
    };
    
    // 重发按钮（仅失败消息）
    const retryBtn = document.createElement('button');
    retryBtn.innerHTML = '🔄';
    retryBtn.title = '重发消息';
    retryBtn.onclick = function() {
        // 删除当前消息并重发
        const messageDiv = retryBtn.closest('.message');
        messageDiv.remove();
        // 注意：实际重发逻辑需要消息内容，这里简化处理
        showToast('请点击输入框重新发送');
    };
    
    actionsDiv.appendChild(copyBtn);
    actionsDiv.appendChild(retryBtn);
    
    return actionsDiv;
}

// 获取状态图标
function getStatusIcon(status) {
    switch (status) {
        case 'sending':
            return '<span class="status-icon">⏳</span> 发送中';
        case 'sent':
            return '<span class="status-icon">✓</span> 已发送';
        case 'delivered':
            return '<span class="status-icon">✓✓</span> 已读';
        case 'failed':
            return '<span class="status-icon" style="color:#ff4757">✗</span> 发送失败';
        default:
            return '';
    }
}

// 更新消息状态
function updateMessageStatus(statusId, status) {
    const statusElement = document.getElementById(statusId);
    if (statusElement) {
        statusElement.innerHTML = getStatusIcon(status);
    }
}

// 显示AI打字指示器
function displayAITyping() {
    return new Promise((resolve) => {
        const chatMessages = document.getElementById('chatMessages');
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai';
        typingDiv.id = 'typingIndicator';
        
        const typingContent = document.createElement('div');
        typingContent.className = 'typing-indicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            typingContent.appendChild(dot);
        }
        
        typingDiv.appendChild(typingContent);
        chatMessages.appendChild(typingDiv);
        
        scrollToBottom();
        isAITyping = true;
        
        resolve();
    });
}

// 移除打字指示器
function removeTypingIndicator() {
    const typingDiv = document.getElementById('typingIndicator');
    if (typingDiv) {
        typingDiv.remove();
    }
    isAITyping = false;
}

// 带打字机效果显示AI消息
async function displayMessageWithTyping(message, type) {
    removeTypingIndicator();
    
    const chatMessages = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const messageP = document.createElement('p');
    messageP.textContent = '';
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = getCurrentTime();
    
    contentDiv.appendChild(messageP);
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    
    chatMessages.appendChild(messageDiv);
    
    // 打字机效果
    await typeWriter(messageP, message, 20);
    
    scrollToBottom();
}

// 打字机效果
function typeWriter(element, text, speed = 30) {
    return new Promise((resolve) => {
        let i = 0;
        
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                scrollToBottom();
                setTimeout(type, speed);
            } else {
                resolve();
            }
        }
        
        type();
    });
}

// 获取当前时间
function getCurrentTime() {
    const now = new Date();
    return now.getHours().toString().padStart(2, '0') + ':' + 
           now.getMinutes().toString().padStart(2, '0');
}

// 滚动到底部
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ==================== 快捷回复 ====================
function sendQuickReply(message) {
    const messageInput = document.getElementById('messageInput');
    messageInput.value = message;
    updateCharCount();
    sendMessage();
}

function hideQuickReplies() {
    const quickReplies = document.getElementById('quickReplies');
    if (quickReplies) {
        quickReplies.style.display = 'none';
    }
}

// ==================== 转人工客服 ====================
function showTransferSuggestion() {
    displayMessage('看起来您可能需要更专业的帮助，建议您转人工客服。', 'system');
}

function displayTransferSuggestion(suggestion) {
    const chatMessages = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = `<p>${suggestion}</p>`;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = getCurrentTime();
    
    // 添加快捷操作按钮
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'transfer-actions';
    actionsDiv.innerHTML = `
        <button class="btn-continue" onclick="dismissTransferSuggestion(this)">继续咨询</button>
        <button class="btn-confirm-transfer" onclick="requestHumanService()">转人工</button>
    `;
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(actionsDiv);
    messageDiv.appendChild(timeDiv);
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function dismissTransferSuggestion(btn) {
    const messageDiv = btn.closest('.message');
    messageDiv.remove();
    showToast('继续为您服务');
}

function requestHumanService() {
    const transferModal = document.getElementById('transferModal');
    transferModal.classList.add('active');
}

function cancelTransfer() {
    const transferModal = document.getElementById('transferModal');
    transferModal.classList.remove('active');
    
    const transferReason = document.getElementById('transferReason');
    transferReason.value = '';
}

async function confirmTransfer() {
    const transferReason = document.getElementById('transferReason').value.trim();
    
    // 关闭模态框
    cancelTransfer();
    
    // 显示转人工消息
    displayMessage('正在为您转接人工客服...', 'system');
    
    // 创建工单
    try {
        const response = await fetch('/api/request-human', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                customer_id: 'customer_' + sessionId,
                reason: transferReason || '客户主动要求转人工'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentTicketId = data.ticket_id;
            
            // 显示工单状态
            showTicketStatus(data.ticket_id);
            
            // 显示工单创建消息
            displayMessage('工单已创建，等待客服接入...', 'system');
            
        } else {
            displayMessage('转人工失败，请稍后再试。', 'system');
        }
        
    } catch (error) {
        console.error('转人工失败:', error);
        displayMessage('网络连接失败，无法转人工。', 'system');
    }
}

// 显示工单状态
function showTicketStatus(ticketId) {
    const ticketStatus = document.getElementById('ticketStatus');
    const ticketIdDisplay = document.getElementById('ticketIdDisplay');
    
    ticketIdDisplay.textContent = ticketId;
    ticketStatus.classList.add('active');
    
    // 定时检查工单状态
    checkTicketStatus(ticketId);
}

// 检查工单状态
async function checkTicketStatus(ticketId) {
    try {
        const response = await fetch(`/api/tickets/${ticketId}`, {
            method: 'GET'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const ticketInfo = data.ticket_info;
            
            if (ticketInfo.status === 'accepted') {
                // 客服已接入
                hideTicketStatus();
                displayMessage(`客服已接入，开始为您服务。`, 'system');
                
                // 更新会话ID
                sessionId = ticketInfo.session_id;
                
            } else if (ticketInfo.status === 'closed') {
                // 工单已关闭
                hideTicketStatus();
                displayMessage('服务已完成，工单已关闭。', 'system');
                
            } else {
                // 继续等待
                setTimeout(() => checkTicketStatus(ticketId), 5000);
            }
        }
        
    } catch (error) {
        console.error('检查工单状态失败:', error);
        setTimeout(() => checkTicketStatus(ticketId), 5000);
    }
}

// 隐藏工单状态
function hideTicketStatus() {
    const ticketStatus = document.getElementById('ticketStatus');
    ticketStatus.classList.remove('active');
}

// ==================== 清空对话 ====================
function clearChat() {
    const chatMessages = document.getElementById('chatMessages');
    
    // 保留系统欢迎消息
    const welcomeMessage = chatMessages.querySelector('.message.system');
    const quickReplies = document.getElementById('quickReplies');
    
    chatMessages.innerHTML = '';
    
    if (welcomeMessage) {
        chatMessages.appendChild(welcomeMessage);
    }
    
    if (quickReplies) {
        chatMessages.appendChild(quickReplies);
        quickReplies.style.display = 'flex';
    }
    
    // 生成新会话ID
    sessionId = generateSessionId();
    console.log('新会话ID:', sessionId);
    
    showToast('对话已清空');
}

// ==================== 工具函数 ====================

// 复制到剪贴板
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
    } catch (err) {
        // 降级方案
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }
}

// 显示Toast通知
function showToast(message, duration = 2000) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

// 格式化时间戳
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 显示通知（已废弃，使用showToast代替）
function showNotification(message) {
    showToast(message);
}

// ==================== 网络状态监控 ====================
window.addEventListener('online', function() {
    updateConnectionStatus('在线');
    showToast('网络已连接');
});

window.addEventListener('offline', function() {
    updateConnectionStatus('离线');
    showToast('网络已断开', 3000);
});
