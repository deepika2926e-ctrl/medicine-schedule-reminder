// ===================================================================
// MEDICINE SCHEDULE REMINDER SYSTEM - API CLIENT & CORE HELPERS
// ===================================================================

const API_BASE = (window.location.protocol.startsWith('http') && window.location.port === '8000')
    ? window.location.origin + '/api'
    : 'http://127.0.0.1:8000/api';

// ----------------- Auth State Management -----------------
function getToken() {
    return localStorage.getItem('med_token');
}

function getUser() {
    const raw = localStorage.getItem('med_user');
    try {
        return raw ? JSON.parse(raw) : null;
    } catch (e) {
        return null;
    }
}

function saveAuth(token, user) {
    localStorage.setItem('med_token', token);
    localStorage.setItem('med_user', JSON.stringify(user));
}

function clearAuth() {
    localStorage.removeItem('med_token');
    localStorage.removeItem('med_user');
}

function requireAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

function redirectIfLoggedIn() {
    const token = getToken();
    if (token) {
        window.location.href = 'dashboard.html';
    }
}

// ----------------- API Request Wrapper -----------------
async function apiRequest(endpoint, options = {}) {
    const method = options.method || 'GET';
    const body = options.body ? JSON.stringify(options.body) : null;
    const token = getToken();

    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method,
            headers,
            body
        });

        if (response.status === 401) {
            clearAuth();
            if (!window.location.pathname.endsWith('login.html') &&
                !window.location.pathname.endsWith('register.html') &&
                !window.location.pathname.endsWith('index.html')) {
                window.location.href = 'login.html';
            }
            throw new Error('Session expired or unauthorized.');
        }

        const data = await response.json();

        if (!response.ok) {
            const errorMsg = data.detail || data.message || 'An error occurred.';
            throw new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
        }

        return data;
    } catch (err) {
        console.error('API Error:', err);
        throw err;
    }
}

// ----------------- UI Toast Notifications -----------------
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = '🔔';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';

    toast.innerHTML = `<span>${icon}</span><div>${message}</div>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ----------------- Audio Chime Generator (Web Audio API) -----------------
function playReminderSound() {
    try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();

        // High pleasant medical chime (two-tone chime: 880Hz then 1174Hz)
        const osc1 = ctx.createOscillator();
        const gain1 = ctx.createGain();
        osc1.type = 'sine';
        osc1.frequency.setValueAtTime(880, ctx.currentTime); // A5
        gain1.gain.setValueAtTime(0.3, ctx.currentTime);
        gain1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
        osc1.connect(gain1);
        gain1.connect(ctx.destination);
        osc1.start(ctx.currentTime);
        osc1.stop(ctx.currentTime + 0.6);

        const osc2 = ctx.createOscillator();
        const gain2 = ctx.createGain();
        osc2.type = 'sine';
        osc2.frequency.setValueAtTime(1174.66, ctx.currentTime + 0.25); // D6
        gain2.gain.setValueAtTime(0.35, ctx.currentTime + 0.25);
        gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.9);
        osc2.connect(gain2);
        gain2.connect(ctx.destination);
        osc2.start(ctx.currentTime + 0.25);
        osc2.stop(ctx.currentTime + 0.9);
    } catch (e) {
        console.warn('Audio playback error:', e);
    }
}

// ----------------- Browser Push Notifications -----------------
async function requestNotificationPermission() {
    if (!('Notification' in window)) {
        showToast('Your browser does not support desktop notifications.', 'error');
        return false;
    }
    if (Notification.permission === 'granted') return true;
    if (Notification.permission !== 'denied') {
        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }
    return false;
}

function sendDesktopNotification(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
        const notif = new Notification(title, {
            body,
            icon: 'assets/medicine-icon.png',
            tag: title + body,
            renotify: false
        });
        notif.onclick = function() {
            window.focus();
            window.location.href = 'reminders.html';
        };
    }
}

// ----------------- Populate UI User Info & Date -----------------
function setupAppShell() {
    const user = getUser();
    if (user) {
        document.querySelectorAll('.js-user-name').forEach(el => {
            el.textContent = user.full_name || 'User';
        });
        document.querySelectorAll('.js-user-email').forEach(el => {
            el.textContent = user.email || '';
        });
        document.querySelectorAll('.js-user-avatar').forEach(el => {
            el.textContent = (user.full_name || 'U').charAt(0).toUpperCase();
        });
    }

    // Set today's date pill
    const dateEls = document.querySelectorAll('.js-current-date');
    if (dateEls.length > 0) {
        const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
        const todayStr = new Date().toLocaleDateString('en-US', options);
        dateEls.forEach(el => el.textContent = `📅 ${todayStr}`);
    }

    // Highlight active link in sidebar
    const currentPath = window.location.pathname.split('/').pop() || 'dashboard.html';
    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && (href === currentPath || (currentPath === '' && href === 'dashboard.html'))) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    if (!window.location.pathname.endsWith('index.html') &&
        !window.location.pathname.endsWith('login.html') &&
        !window.location.pathname.endsWith('register.html')) {
        setupAppShell();
    }
});
