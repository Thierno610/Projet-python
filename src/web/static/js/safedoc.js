/**
 * SafeDoc - JavaScript Principal
 * Remplace Jinja2 par du JavaScript moderne
 */

// Variables globales
let userData = null;
let appData = {
    documents: [],
    etiquettes: [],
    categories: ["Toutes", "Facture", "Contrat", "Identité"]
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    console.log('SafeDoc JS - Initialisation...');
    loadUserData();
    initializeEventListeners();
    initializeStorageBar();
    initializeNavigation();
});

// Charger les données utilisateur depuis l'API
async function loadUserData() {
    try {
        const response = await fetch('/api/user-data');
        if (response.ok) {
            userData = await response.json();
            console.log('Données utilisateur chargées:', userData);
            updateUserInterface();
        } else {
            console.error('Erreur lors du chargement des données utilisateur');
            window.location.href = '/connexion';
        }
    } catch (error) {
        console.error('Erreur réseau:', error);
    }
}

// Mettre à jour l'interface avec les données utilisateur
function updateUserInterface() {
    if (!userData) return;

    // Mettre à jour le nom d'utilisateur dans la navbar
    const userNameElement = document.querySelector('.navbar-text .fa-user');
    if (userNameElement) {
        userNameElement.nextSibling.textContent = userData.nom_utilisateur;
    }

    // Mettre à jour le badge Premium/Gratuit
    const badgeElement = document.querySelector('.navbar-text .badge');
    if (badgeElement) {
        if (userData.est_premium) {
            badgeElement.className = 'badge bg-warning text-dark me-3';
            badgeElement.textContent = 'Premium';
        } else {
            badgeElement.className = 'badge bg-secondary me-3';
            badgeElement.textContent = 'Gratuit';
        }
    }

    // Mettre à jour les informations de stockage
    updateStorageInfo();
}

// Mettre à jour la barre de stockage
function updateStorageInfo() {
    if (!userData) return;

    const storageInfo = document.querySelector('.storage-info');
    const progressBar = document.querySelector('.progress-bar');
    const premiumButton = document.querySelector('.btn-warning');

    if (storageInfo) {
        const stockageMo = (userData.stockage_utilise / (1024 * 1024)).toFixed(1);
        storageInfo.innerHTML = `
            <i class="fas fa-hdd me-2"></i>
            Stockage : ${stockageMo} Mo
        `;
    }

    if (progressBar) {
        progressBar.style.width = `${userData.pourcentage}%`;
        progressBar.setAttribute('aria-valuenow', userData.pourcentage);
    }

    if (premiumButton && !userData.est_premium) {
        premiumButton.style.display = 'inline-flex';
    } else if (premiumButton) {
        premiumButton.style.display = 'none';
    }
}

// Initialiser la barre de stockage
function initializeStorageBar() {
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        // Animation de la barre de progression
        setTimeout(() => {
            progressBar.style.transition = 'width 0.6s ease';
        }, 100);
    }
}

// Initialiser les écouteurs d'événements
function initializeEventListeners() {
    // Gestion des formulaires
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });

    // Gestion des boutons d'action
    const actionButtons = document.querySelectorAll('.btn-action');
    actionButtons.forEach(button => {
        button.addEventListener('click', handleActionButton);
    });

    // Gestion des liens de navigation
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', handleNavigation);
    });
}

// Gérer la soumission des formulaires
async function handleFormSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const action = form.getAttribute('action');
    const method = form.getAttribute('method') || 'POST';

    try {
        const response = await fetch(action, {
            method: method,
            body: formData
        });

        if (response.ok) {
            showNotification('Action réussie !', 'success');
            if (form.classList.contains('reload')) {
                setTimeout(() => location.reload(), 1000);
            }
        } else {
            showNotification('Erreur lors de l\'action', 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('Erreur réseau', 'error');
    }
}

// Gérer les boutons d'action
function handleActionButton(event) {
    const button = event.currentTarget;
    const action = button.getAttribute('data-action');
    
    switch(action) {
        case 'refresh':
            loadUserData();
            showNotification('Données actualisées', 'success');
            break;
        case 'logout':
            logout();
            break;
        default:
            console.log('Action non gérée:', action);
    }
}

// Gérer la navigation
function handleNavigation(event) {
    const link = event.currentTarget;
    const href = link.getAttribute('href');
    
    // Ajouter une animation de transition
    document.body.style.opacity = '0.8';
    setTimeout(() => {
        window.location.href = href;
    }, 100);
}

// Initialiser la navigation active
function initializeNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

// Afficher une notification
function showNotification(message, type = 'info') {
    // Créer l'élément de notification
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        <div class="alert-content">${message}</div>
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>
    `;
    
    // Ajouter à la page
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.insertBefore(notification, mainContent.firstChild);
        
        // Auto-suppression après 5 secondes
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Déconnexion
async function logout() {
    try {
        const response = await fetch('/logout', { method: 'POST' });
        if (response.ok) {
            window.location.href = '/connexion';
        }
    } catch (error) {
        console.error('Erreur de déconnexion:', error);
    }
}

// Fonctions utilitaires
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Mo';
    const mb = bytes / (1024 * 1024);
    return mb.toFixed(1) + ' Mo';
}

function formatPercentage(value) {
    return Math.round(value) + '%';
}

// Gestion des animations
function animateValue(element, start, end, duration) {
    const range = end - start;
    const startTime = performance.now();
    
    function updateValue(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const value = start + (range * progress);
        
        element.textContent = formatValue(value);
        
        if (progress < 1) {
            requestAnimationFrame(updateValue);
        }
    }
    
    requestAnimationFrame(updateValue);
}

// Gestion du thème
function toggleTheme() {
    document.body.classList.toggle('light-theme');
    const isLight = document.body.classList.contains('light-theme');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
}

// Charger le thème sauvegardé
function loadTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
    }
}

// Gestion des animations de scroll
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observer les éléments à animer
    const animatedElements = document.querySelectorAll('.glass-card, .metric-card');
    animatedElements.forEach(el => observer.observe(el));
}

// Gestion du drag and drop
function initializeDragDrop() {
    const dropZone = document.querySelector('.upload-zone');
    if (!dropZone) return;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    dropZone.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    e.currentTarget.classList.add('drag-over');
}

function unhighlight(e) {
    e.currentTarget.classList.remove('drag-over');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFiles(files) {
    ([...files]).forEach(uploadFile);
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        showNotification('Fichier uploadé avec succès!', 'success');
    })
    .catch(error => {
        console.error('Erreur upload:', error);
        showNotification('Erreur lors de l\'upload', 'error');
    });
}

// Initialisation complète
document.addEventListener('DOMContentLoaded', function() {
    loadTheme();
    initializeScrollAnimations();
    initializeDragDrop();
    
    // Ajouter les classes d'animation
    setTimeout(() => {
        document.querySelectorAll('.glass-card').forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('animate-in');
            }, index * 100);
        });
    }, 100);
});

// Exporter les fonctions globales
window.SafeDoc = {
    loadUserData,
    showNotification,
    logout,
    toggleTheme,
    formatFileSize,
    formatPercentage
};
