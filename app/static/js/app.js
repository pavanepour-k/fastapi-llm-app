// Modern JavaScript for enhanced UI functionality
// Following vanilla JS best practices for maintainability

class ChatApplication {
    constructor() {
        this.initializeEventListeners();
        this.setupAutoResize();
        this.setupNotifications();
    }
    
    initializeEventListeners() {
        // Handle file upload with progress indication
        this.setupFileUpload();
        
        // Handle message form enhancements
        this.setupMessageForm();
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
    }
    
    setupFileUpload() {
        const uploadForm = document.querySelector('.upload-form');
        if (!uploadForm) return;
        
        uploadForm.addEventListener('submit', async (e) => {
            const submitBtn = uploadForm.querySelector('button[type="submit"]');
            const statusDiv = document.getElementById('upload-status');
            
            // Show loading state
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Uploading...';
            submitBtn.disabled = true;
            
            // Update status
            statusDiv.innerHTML = '<div class="loading">Processing upload...</div>';
        });
        
        // Handle upload response
        document.addEventListener('htmx:afterRequest', (e) => {
            if (e.target.matches('.upload-form')) {
                const submitBtn = e.target.querySelector('button[type="submit"]');
                const statusDiv = document.getElementById('upload-status');
                
                // Reset button
                submitBtn.textContent = 'Upload';
                submitBtn.disabled = false;
                
                // Show result
                if (e.detail.xhr.status === 200) {
                    statusDiv.innerHTML = '<div class="upload-status success">Document uploaded successfully!</div>';
                    // Refresh knowledge base stats
                    htmx.trigger('#kb-stats', 'refresh');
                } else {
                    statusDiv.innerHTML = '<div class="upload-status error">Upload failed. Please try again.</div>';
                }
                
                // Clear file input
                const fileInput = e.target.querySelector('input[type="file"]');
                fileInput.value = '';
                
                // Auto-hide status after 5 seconds
                setTimeout(() => {
                    statusDiv.innerHTML = '';
                }, 5000);
            }
        });
    }
    
    setupMessageForm() {
        const messageTextarea = document.querySelector('textarea[name="message"]');
        if (!messageTextarea) return;
        
        // Auto-resize textarea
        messageTextarea.addEventListener('input', (e) => {
            e.target.style.height = 'auto';
            e.target.style.height = e.target.scrollHeight + 'px';
        });
        
        // Clear on successful send
        document.addEventListener('htmx:wsBeforeMessage', (e) => {
            if (e.detail.message.type === 'message') {
                messageTextarea.value = '';
                messageTextarea.style.height = 'auto';
            }
        });
    }
    
    setupAutoResize() {
        // Auto-resize message container
        const resizeObserver = new ResizeObserver(() => {
            const container = document.getElementById('chat-messages');
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        });
        
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            resizeObserver.observe(messagesContainer);
        }
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Enter to send message
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const form = document.querySelector('.message-form');
                if (form) {
                    form.dispatchEvent(new Event('submit'));
                }
            }
            
            // Escape to clear message
            if (e.key === 'Escape') {
                const textarea = document.querySelector('textarea[name="message"]');
                if (textarea && document.activeElement === textarea) {
                    textarea.value = '';
                    textarea.style.height = 'auto';
                }
            }
        });
    }
    
    setupNotifications() {
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
        
        // Show notification for new messages when tab is not visible
        document.addEventListener('htmx:wsAfterMessage', (e) => {
            if (document.hidden && 'Notification' in window && Notification.permission === 'granted') {
                // Parse message to check if it's from assistant
                const messageHtml = e.detail.message;
                if (messageHtml.includes('assistant-message')) {
                    new Notification('New message from AI Assistant', {
                        icon: '/static/images/bot-avatar.png',
                        badge: '/static/images/bot-avatar.png'
                    });
                }
            }
        });
    }
}

// Theme management
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.applyTheme();
    }
    
    applyTheme() {
        document.documentElement.setAttribute('data-theme', this.currentTheme);
    }
    
    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.currentTheme);
        this.applyTheme();
    }
}

// Connection status manager
class ConnectionManager {
    constructor() {
        this.setupConnectionHandlers();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    setupConnectionHandlers() {
        document.addEventListener('htmx:wsOpen', (e) => {
            this.onConnect();
        });
        
        document.addEventListener('htmx:wsClose', (e) => {
            this.onDisconnect();
        });
        
        document.addEventListener('htmx:wsError', (e) => {
            this.onError();
        });
    }
    
    onConnect() {
        this.reconnectAttempts = 0;
        this.updateStatus('Connected', 'connected');
        this.showToast('Connected to chat server', 'success');
    }
    
    onDisconnect() {
        this.updateStatus('Disconnected', 'disconnected');
        this.attemptReconnect();
    }
    
    onError() {
        this.updateStatus('Connection Error', 'error');
        this.showToast('Connection error occurred', 'error');
    }
    
    updateStatus(text, className) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = text;
            statusElement.className = `status-indicator ${className}`;
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.updateStatus(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`, 'reconnecting');
            
            setTimeout(() => {
                // Trigger HTMX to reconnect
                const wsElement = document.querySelector('[hx-ext="ws"]');
                if (wsElement) {
                    htmx.trigger(wsElement, 'htmx:ws-connect');
                }
            }, 2000 * this.reconnectAttempts);
        } else {
            this.updateStatus('Connection Failed', 'failed');
            this.showToast('Unable to reconnect. Please refresh the page.', 'error');
        }
    }
    
    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        // Add to page
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        
        toastContainer.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatApplication();
    new ThemeManager();
    new ConnectionManager();
});

// Global utility functions
window.chatApp = {
    scrollToBottom: () => {
        const container = document.getElementById('chat-messages');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    },
    
    formatMessage: (text) => {
        // Simple text formatting for better display
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    },
    
    copyToClipboard: async (text) => {
        try {
            await navigator.clipboard.writeText(text);
            connectionManager.showToast('Copied to clipboard', 'success');
        } catch (err) {
            console.error('Failed to copy: ', err);
        }
    }
};
