/**
 * SafeDoc - JavaScript Stabilisé et Robuste
 * Gestion d'erreurs, cache, et performance
 */

// Configuration globale
const SafeDoc = {
    config: {
        apiBaseUrl: '/api',
        cacheTimeout: 5 * 60 * 1000, // 5 minutes
        retryAttempts: 3,
        retryDelay: 1000,
        animationDuration: 300
    },

    // Cache local
    cache: new Map(),

    // État de l'application
    state: {
        userData: null,
        isAuthenticated: false,
        isLoading: false,
        isInitializing: true,
        lastError: null
    },

    // Compteurs de retry
    retryCounters: new Map()
};

// Gestionnaire de cache
class CacheManager {
    static set(key, data, timeout = SafeDoc.config.cacheTimeout) {
        const item = {
            data,
            timestamp: Date.now(),
            timeout
        };
        SafeDoc.cache.set(key, item);
    }

    static get(key) {
        const item = SafeDoc.cache.get(key);
        if (!item) return null;

        if (Date.now() - item.timestamp > item.timeout) {
            SafeDoc.cache.delete(key);
            return null;
        }

        return item.data;
    }

    static clear() {
        SafeDoc.cache.clear();
    }

    static size() {
        return SafeDoc.cache.size;
    }
}

// Gestionnaire d'erreurs
class ErrorHandler {
    static log(error, context = 'Unknown') {
        console.error(`[SafeDoc Error] ${context}:`, error);

        // Envoyer les erreurs au serveur en production
        if (window.location.hostname !== 'localhost') {
            this.reportToServer(error, context);
        }
    }

    static reportToServer(error, context) {
        fetch('/api/errors', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                error: error.message,
                stack: error.stack,
                context,
                url: window.location.href,
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString()
            })
        }).catch(e => console.error('Failed to report error to server:', e));
    }

    static handle(error, context = 'Unknown') {
        const type = this.getErrorType(error);

        // Hardening: Ignore non-critical background errors that pollute the UI
        if (context === 'Global Error' && (type === 'default' || !error)) {
            console.warn(`[SafeDoc Silence] Suppressed minor global issue:`, error);
            return;
        }

        // Hardening: Ignore script errors without stack (often cross-origin issues)
        if (error && error.message === 'Script error.') {
            return;
        }

        this.log(error, context);
        SafeDoc.state.lastError = error;

        // Afficher une notification à l'utilisateur seulement si critique ou explicite
        if (!SafeDoc.state.isInitializing || type !== 'default') {
            this.showUserNotification(error, context);
        }
    }

    static showUserNotification(error, context) {
        const message = this.getUserMessage(error, context);
        const type = this.getNotificationType(error);

        // Don't show generic notifications during initial load
        if (SafeDoc.state.isInitializing) return;

        if (window.SafeDoc && window.SafeDoc.showNotification) {
            window.SafeDoc.showNotification(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    static getUserMessage(error, context) {
        const messages = {
            'NetworkError': 'Erreur de connexion. Vérifiez votre internet.',
            'AuthenticationError': 'Session expirée. Veuillez vous reconnecter.',
            'ValidationError': 'Données invalides. Veuillez vérifier votre saisie.',
            'ServerError': 'Erreur serveur. Veuillez réessayer plus tard.',
            'default': 'Une erreur est survenue. Veuillez réessayer.'
        };

        const errorType = this.getErrorType(error);
        return messages[errorType] || messages.default;
    }

    static getNotificationType(error) {
        const errorType = this.getErrorType(error);
        const types = {
            'NetworkError': 'warning',
            'AuthenticationError': 'error',
            'ValidationError': 'warning',
            'ServerError': 'error'
        };

        return types[errorType] || 'info';
    }

    static getErrorType(error) {
        if (!error) return 'default';
        const msg = error.message || String(error);

        if (msg.includes('fetch') || msg.includes('NetworkError')) {
            return 'NetworkError';
        }
        if (msg.includes('401') || msg.includes('auth')) {
            return 'AuthenticationError';
        }
        if (msg.includes('400') || msg.includes('validation')) {
            return 'ValidationError';
        }
        if (msg.includes('500') || msg.includes('server')) {
            return 'ServerError';
        }
        return 'default';
    }
}

// Gestionnaire de requêtes API
class APIManager {
    static async request(url, options = {}) {
        const cacheKey = `${url}:${JSON.stringify(options)}`;

        // Vérifier le cache d'abord
        if (options.method !== 'POST' && !options.skipCache) {
            const cached = CacheManager.get(cacheKey);
            if (cached) {
                console.log(`Cache hit for ${url}`);
                return cached;
            }
        }

        // Configuration par défaut
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            timeout: 10000
        };

        const finalOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        let lastError;

        // Retry logic
        for (let attempt = 1; attempt <= SafeDoc.config.retryAttempts; attempt++) {
            try {
                SafeDoc.state.isLoading = true;

                const response = await fetch(url, finalOptions);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();

                // Mettre en cache seulement si la requête a réussi
                if (options.method !== 'POST' && !options.skipCache) {
                    CacheManager.set(cacheKey, data);
                }

                SafeDoc.state.isLoading = false;
                SafeDoc.retryCounters.delete(url);

                return data;

            } catch (error) {
                lastError = error;
                console.warn(`Attempt ${attempt} failed for ${url}:`, error.message);

                if (attempt < SafeDoc.config.retryAttempts) {
                    await this.delay(SafeDoc.config.retryDelay * attempt);
                }
            }
        }

        SafeDoc.state.isLoading = false;

        // Si tous les retries ont échoué
        if (!options.silent) {
            ErrorHandler.handle(lastError, `API Request: ${url}`);
        }
        throw lastError;
    }

    static delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    static async get(url, options = {}) {
        return this.request(url, { ...options, method: 'GET' });
    }

    static async post(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(url, options = {}) {
        return this.request(url, { ...options, method: 'DELETE' });
    }
}

// Gestionnaire de l'état de l'application
class StateManager {
    static setState(updates) {
        const prevState = { ...SafeDoc.state };
        SafeDoc.state = { ...SafeDoc.state, ...updates };

        // Notifier les changements
        this.notifyStateChange(prevState, SafeDoc.state);
    }

    static getState(key) {
        return key ? SafeDoc.state[key] : SafeDoc.state;
    }

    static notifyStateChange(prevState, newState) {
        // Mettre à jour l'UI en fonction des changements
        if (prevState.isAuthenticated !== newState.isAuthenticated) {
            this.handleAuthChange(newState.isAuthenticated);
        }

        if (prevState.userData !== newState.userData) {
            this.handleUserDataChange(newState.userData);
        }

        if (prevState.isLoading !== newState.isLoading) {
            this.handleLoadingChange(newState.isLoading);
        }
    }

    static handleAuthChange(isAuthenticated) {
        // Authentification désactivée - Toujours autorisé
        return;
    }

    static handleUserDataChange(userData) {
        if (userData) {
            this.updateUserInterface(userData);
        }
    }

    static handleLoadingChange(isLoading) {
        const loadingElements = document.querySelectorAll('.loading-indicator');
        loadingElements.forEach(el => {
            el.style.display = isLoading ? 'block' : 'none';
        });
    }

    static updateUserInterface(userData) {
        // Mettre à jour le nom d'utilisateur
        const userNameElement = document.getElementById('user-name');
        if (userNameElement) {
            userNameElement.textContent = userData.nom_utilisateur;
        }

        // Mettre à jour le badge
        const badgeElement = document.getElementById('user-level');
        if (badgeElement) {
            if (userData.est_premium) {
                badgeElement.textContent = 'Premium';
                badgeElement.className = 'badge bg-warning text-dark me-3';
            } else {
                badgeElement.textContent = 'Gratuit';
                badgeElement.className = 'badge bg-secondary me-3';
            }
        }

        // Mettre à jour le stockage
        this.updateStorageInfo(userData);

        // Mettre à jour le bouton premium
        const premiumBtn = document.getElementById('premium-btn');
        if (premiumBtn) {
            premiumBtn.style.display = userData.est_premium ? 'none' : 'inline-flex';
        }
    }

    static updateStorageInfo(userData) {
        const storageAmount = document.getElementById('storage-amount');
        const storageBar = document.getElementById('storage-bar');

        if (storageAmount) {
            const amount = (userData.stockage_utilise / (1024 * 1024)).toFixed(1);
            storageAmount.textContent = `${amount} Mo`;
        }

        if (storageBar) {
            const percentage = userData.pourcentage;
            storageBar.style.width = `${percentage}%`;
            storageBar.setAttribute('aria-valuenow', percentage);

            // Ajouter une animation
            storageBar.style.transition = 'width 0.6s ease';
        }
    }
}

// Gestionnaire d'animations
class AnimationManager {
    static animateElement(element, properties, duration = SafeDoc.config.animationDuration) {
        return new Promise(resolve => {
            element.style.transition = `all ${duration}ms ease`;

            // Appliquer les propriétés
            Object.keys(properties).forEach(prop => {
                element.style[prop] = properties[prop];
            });

            setTimeout(() => {
                element.style.transition = '';
                resolve();
            }, duration);
        });
    }

    static fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';

        return this.animateElement(element, { opacity: '1' }, duration);
    }

    static fadeOut(element, duration = 300) {
        return this.animateElement(element, { opacity: '0' }, duration)
            .then(() => {
                element.style.display = 'none';
            });
    }

    static slideIn(element, direction = 'left', duration = 300) {
        const transform = direction === 'left' ? 'translateX(-20px)' : 'translateX(20px)';
        element.style.transform = transform;
        element.style.opacity = '0';
        element.style.display = 'block';

        return this.animateElement(element, {
            transform: 'translateX(0)',
            opacity: '1'
        }, duration);
    }

    static pulse(element, duration = 600) {
        return this.animateElement(element, {
            transform: 'scale(1.05)'
        }, duration / 2)
            .then(() => {
                return this.animateElement(element, {
                    transform: 'scale(1)'
                }, duration / 2);
            });
    }
}

// Gestionnaire de notifications
class NotificationManager {
    static show(message, type = 'info', duration = 5000) {
        const container = document.getElementById('flash-messages');
        if (!container) {
            console.warn('Flash messages container not found');
            return;
        }

        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show animate-in`;
        notification.innerHTML = `
            <div class="alert-content">
                <i class="fas fa-${this.getIcon(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer">
                <span aria-hidden="true">&times;</span>
            </button>
        `;

        container.appendChild(notification);

        // Auto-suppression
        setTimeout(() => {
            this.hide(notification);
        }, duration);

        // Bouton de fermeture manuel
        const closeBtn = notification.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hide(notification));
        }
    }

    static hide(notification) {
        notification.classList.remove('animate-in');
        notification.classList.add('animate-out');

        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    static getIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    static success(message, duration) {
        this.show(message, 'success', duration);
    }

    static error(message, duration) {
        this.show(message, 'error', duration);
    }

    static warning(message, duration) {
        this.show(message, 'warning', duration);
    }

    static info(message, duration) {
        this.show(message, 'info', duration);
    }
}

// Gestionnaire de performance
class PerformanceManager {
    static measure(name, fn) {
        return async (...args) => {
            const start = performance.now();
            try {
                const result = await fn(...args);
                const end = performance.now();
                console.log(`[Performance] ${name}: ${(end - start).toFixed(2)}ms`);
                return result;
            } catch (error) {
                const end = performance.now();
                console.error(`[Performance] ${name}: ${(end - start).toFixed(2)}ms (ERROR)`);
                throw error;
            }
        };
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static throttle(func, limit) {
        let inThrottle;
        return function (...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// Fonctions principales
class SafeDocApp {
    static async initialize() {
        try {
            SafeDoc.state.isInitializing = true;
            console.log('SafeDoc - Initialisation stabilisée...');

            // Vérifier l'authentification
            await this.checkAuthentication();

            // Initialiser les écouteurs d'événements
            this.initializeEventListeners();

            // Initialiser les animations
            this.initializeAnimations();

            // Initialiser les observateurs
            this.initializeObservers();

            // Nettoyer le cache ancien
            this.cleanupOldCache();

            // Fin de l'initialisation après un court délai pour stabiliser les erreurs
            setTimeout(() => {
                SafeDoc.state.isInitializing = false;
                console.log('SafeDoc - Système prêt et stabilisé');
            }, 1000);

        } catch (error) {
            SafeDoc.state.isInitializing = false;
            ErrorHandler.handle(error, 'Initialization');
        }
    }

    static async checkAuthentication() {
        // Authentification désactivée - Forcer l'état authentifié pour l'UI
        StateManager.setState({
            isAuthenticated: true
        });
    }

    static initializeEventListeners() {
        // Navigation
        document.addEventListener('click', (e) => {
            const navLink = e.target.closest('.nav-link');
            if (navLink) {
                const href = navLink.getAttribute('href');
                if (href && !href.startsWith('#')) {
                    e.preventDefault();
                    this.navigateWithTransition(href);
                }
            }
        });

        // Boutons d'action
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action]')) {
                this.handleAction(e.target);
            }
        });

        // Formulaires
        document.addEventListener('submit', (e) => {
            if (e.target.matches('[data-ajax]')) {
                e.preventDefault();
                this.handleFormSubmit(e.target);
            }
        });

        // Redimensionnement
        window.addEventListener('resize', PerformanceManager.debounce(() => {
            this.handleResize();
        }, 250));

        // Scroll
        window.addEventListener('scroll', PerformanceManager.throttle(() => {
            this.handleScroll();
        }, 100));
    }

    static initializeAnimations() {
        // Animations au chargement
        document.querySelectorAll('.glass-card').forEach((card, index) => {
            setTimeout(() => {
                AnimationManager.fadeIn(card);
            }, index * 100);
        });

        // Animations au survol
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('mouseenter', () => {
                AnimationManager.pulse(btn);
            });
        });
    }

    static initializeObservers() {
        // Observer pour les animations au scroll
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, {
            threshold: 0.1
        });

        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            observer.observe(el);
        });
    }

    static cleanupOldCache() {
        // Nettoyer le cache trop ancien
        const maxCacheSize = 50;
        if (CacheManager.size() > maxCacheSize) {
            const keys = Array.from(SafeDoc.cache.keys());
            keys.slice(0, keys.length - maxCacheSize).forEach(key => {
                SafeDoc.cache.delete(key);
            });
        }
    }

    static async handleAction(element) {
        const action = element.dataset.action;

        try {
            switch (action) {
                case 'refresh':
                    await this.refreshData();
                    break;
                case 'clear-cache':
                    CacheManager.clear();
                    NotificationManager.success('Cache vidé');
                    break;
                default:
                    console.warn(`Action non gérée: ${action}`);
            }
        } catch (error) {
            ErrorHandler.handle(error, `Action: ${action}`);
        }
    }

    static async handleFormSubmit(form) {
        const formData = new FormData(form);
        const action = form.getAttribute('action');
        const method = form.getAttribute('method') || 'POST';

        try {
            const options = {
                method,
                body: formData
            };

            // Désactiver le bouton
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Chargement...';

            const response = await APIManager.request(action, options);

            // Réactiver le bouton
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;

            // Succès
            NotificationManager.success('Action réussie !');

            // Redirection si nécessaire
            if (form.dataset.redirect) {
                setTimeout(() => {
                    window.location.href = form.dataset.redirect;
                }, 1000);
            }

        } catch (error) {
            // Réactiver le bouton
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;

            throw error;
        }
    }

    static async refreshData() {
        try {
            await this.checkAuthentication();
            NotificationManager.success('Données actualisées');
        } catch (error) {
            throw error;
        }
    }

    static async logout() {
        // Logout désactivé
        return;
    }

    static navigateWithTransition(url) {
        document.body.style.opacity = '0.8';
        setTimeout(() => {
            window.location.href = url;
        }, 200);
    }

    static handleResize() {
        // Adapter l'interface selon la taille
        const isMobile = window.innerWidth < 768;

        document.body.classList.toggle('mobile', isMobile);

        // Mettre à jour les classes responsive
        document.querySelectorAll('.responsive').forEach(el => {
            el.classList.toggle('mobile', isMobile);
        });
    }

    static handleScroll() {
        // Gérer la navbar sticky
        const navbar = document.querySelector('.navbar');
        const scrolled = window.scrollY > 50;

        if (navbar) {
            navbar.classList.toggle('scrolled', scrolled);
        }
    }
}

// API publique
window.SafeDoc = {
    // État
    getState: StateManager.getState.bind(StateManager),

    // Notifications
    showNotification: NotificationManager.show.bind(NotificationManager),
    success: NotificationManager.success.bind(NotificationManager),
    error: NotificationManager.error.bind(NotificationManager),
    warning: NotificationManager.warning.bind(NotificationManager),
    info: NotificationManager.info.bind(NotificationManager),

    // Utilitaires
    formatFileSize: (bytes) => {
        const mb = bytes / (1024 * 1024);
        return mb.toFixed(1) + ' Mo';
    },

    formatPercentage: (value) => Math.round(value) + '%',

    // Cache
    clearCache: () => CacheManager.clear(),

    // Performance
    measure: PerformanceManager.measure.bind(PerformanceManager),

    // Initialisation
    init: SafeDocApp.initialize.bind(SafeDocApp)
};

// Initialiser l'application
document.addEventListener('DOMContentLoaded', () => {
    SafeDoc.init();
});

// Gérer les erreurs non capturées
window.addEventListener('error', (event) => {
    ErrorHandler.handle(event.error, 'Global Error');
});

window.addEventListener('unhandledrejection', (event) => {
    ErrorHandler.handle(event.reason, 'Unhandled Promise Rejection');
});
