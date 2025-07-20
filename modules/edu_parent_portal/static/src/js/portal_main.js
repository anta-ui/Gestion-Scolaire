/**
 * JavaScript principal pour le Portail Parents
 * ===========================================
 */

// Namespace pour le portail parent
const ParentPortal = {
    
    // Configuration
    config: {
        refreshInterval: 300000, // 5 minutes
        notificationTimeout: 5000, // 5 secondes
    },
    
    // Initialisation
    init: function() {
        console.log('Initialisation du Portail Parents...');
        this.bindEvents();
        this.initNotifications();
        this.startAutoRefresh();
    },
    
    // Liaison des événements
    bindEvents: function() {
        // Gestion des clics sur les boutons
        $(document).on('click', '.portal-btn', function(e) {
            const button = $(this);
            if (button.hasClass('loading')) {
                e.preventDefault();
                return false;
            }
        });
        
        // Gestion des formulaires
        $(document).on('submit', '.portal-form', function(e) {
            ParentPortal.handleFormSubmit(e);
        });
        
        // Gestion du menu mobile
        $(document).on('click', '.mobile-menu-toggle', function() {
            $('.portal-mobile-menu').toggleClass('active');
        });
        
        // Fermeture automatique des notifications
        $(document).on('click', '.portal-notification .close', function() {
            $(this).closest('.portal-notification').fadeOut();
        });
    },
    
    // Gestion des notifications
    initNotifications: function() {
        // Vérifier les permissions de notification
        if ("Notification" in window) {
            if (Notification.permission === "default") {
                Notification.requestPermission();
            }
        }
        
        // Auto-fermeture des notifications
        setTimeout(function() {
            $('.portal-notification.auto-close').fadeOut();
        }, this.config.notificationTimeout);
    },
    
    // Affichage d'une notification
    showNotification: function(message, type = 'info', autoClose = true) {
        const notificationClass = `portal-notification ${type} ${autoClose ? 'auto-close' : ''}`;
        const notification = $(`
            <div class="${notificationClass}">
                <span class="message">${message}</span>
                <button class="close" type="button">&times;</button>
            </div>
        `);
        
        $('#notification-container').prepend(notification);
        
        if (autoClose) {
            setTimeout(function() {
                notification.fadeOut();
            }, this.config.notificationTimeout);
        }
    },
    
    // Gestion des formulaires
    handleFormSubmit: function(e) {
        const form = $(e.target);
        const submitButton = form.find('button[type="submit"]');
        
        // Ajouter l'indicateur de chargement
        submitButton.addClass('loading').prop('disabled', true);
        
        // Retirer l'indicateur après 5 secondes maximum
        setTimeout(function() {
            submitButton.removeClass('loading').prop('disabled', false);
        }, 5000);
    },
    
    // Actualisation automatique
    startAutoRefresh: function() {
        setInterval(function() {
            ParentPortal.refreshDashboardData();
        }, this.config.refreshInterval);
    },
    
    // Actualisation des données du tableau de bord
    refreshDashboardData: function() {
        $.ajax({
            url: '/my/dashboard/refresh',
            method: 'GET',
            success: function(data) {
                if (data.success) {
                    ParentPortal.updateDashboardWidgets(data.widgets);
                }
            },
            error: function() {
                console.log('Erreur lors de l\'actualisation des données');
            }
        });
    },
    
    // Mise à jour des widgets du tableau de bord
    updateDashboardWidgets: function(widgets) {
        Object.keys(widgets).forEach(function(widgetId) {
            const widgetElement = $(`#widget-${widgetId}`);
            if (widgetElement.length) {
                widgetElement.html(widgets[widgetId]);
            }
        });
    },
    
    // Utilitaires
    utils: {
        // Formatage des dates
        formatDate: function(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('fr-FR');
        },
        
        // Formatage des heures
        formatTime: function(timeString) {
            const time = new Date(`2000-01-01T${timeString}`);
            return time.toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'});
        },
        
        // Vérification de la connectivité
        checkConnection: function() {
            return navigator.onLine;
        }
    }
};

// Initialisation au chargement de la page
$(document).ready(function() {
    ParentPortal.init();
});

// Gestion de la connectivité
window.addEventListener('online', function() {
    ParentPortal.showNotification('Connexion rétablie', 'success');
});

window.addEventListener('offline', function() {
    ParentPortal.showNotification('Connexion perdue', 'warning', false);
});
