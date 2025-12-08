// ============================================
// BotFactory AI - Main JavaScript
// ============================================

// API Configuration
const API_BASE = '/api/v1';

// Auth Token Management
const Auth = {
    getToken() {
        return localStorage.getItem('access_token');
    },

    setTokens(accessToken, refreshToken) {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', refreshToken);
    },

    clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    },

    isLoggedIn() {
        return !!this.getToken();
    },

    async logout() {
        this.clearTokens();
        window.location.href = '/login';
    }
};

// API Helper
const api = {
    async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        const token = Auth.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                Auth.clearTokens();
                window.location.href = '/login';
                return null;
            }

            const data = await response.json();
            return { ok: response.ok, data, status: response.status };
        } catch (error) {
            console.error('API Error:', error);
            return { ok: false, error: error.message };
        }
    },

    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    },

    patch(endpoint, body) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(body)
        });
    },

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// UI Helpers
const UI = {
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    },

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    },

    showAlert(message, type = 'success') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} fade-in`;
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '80px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '300';
        alertDiv.style.minWidth = '300px';
        alertDiv.textContent = message;

        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    },

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        }
        if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    },

    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('uz-UZ', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }
};

// Mobile sidebar toggle
document.addEventListener('DOMContentLoaded', () => {
    // Add mobile menu button
    const navbar = document.querySelector('.navbar-content');
    if (navbar && window.innerWidth < 1024) {
        const menuBtn = document.createElement('button');
        menuBtn.className = 'btn btn-secondary btn-sm';
        menuBtn.innerHTML = '☰';
        menuBtn.onclick = () => {
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) {
                sidebar.classList.toggle('open');
            }
        };
        navbar.prepend(menuBtn);
    }

    // Close modal on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('active');
            }
        });
    });
});

// Export for use in templates
window.Auth = Auth;
window.api = api;
window.UI = UI;
