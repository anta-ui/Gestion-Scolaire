// JavaScript pour le portail de paiement étudiant

document.addEventListener('DOMContentLoaded', function() {
    initializePortalPayment();
});

function initializePortalPayment() {
    // Initialiser les boutons de paiement
    const paymentButtons = document.querySelectorAll('.btn-pay-invoice');
    paymentButtons.forEach(button => {
        button.addEventListener('click', handlePaymentClick);
    });

    // Initialiser les modales
    initializePaymentModal();
    
    // Initialiser les filtres
    initializeFilters();
}

function handlePaymentClick(event) {
    event.preventDefault();
    
    const button = event.target;
    const invoiceId = button.dataset.invoiceId;
    const amount = parseFloat(button.dataset.amount);
    const currency = button.dataset.currency || 'EUR';
    
    openPaymentModal(invoiceId, amount, currency);
}

function openPaymentModal(invoiceId, amount, currency) {
    const modal = document.getElementById('paymentModal');
    if (!modal) return;
    
    // Mettre à jour les informations de la facture
    document.getElementById('modal-invoice-id').textContent = invoiceId;
    document.getElementById('modal-amount').textContent = formatCurrency(amount, currency);
    document.getElementById('payment-amount').value = amount;
    
    // Afficher la modale
    modal.style.display = 'flex';
    
    // Focus sur le premier champ
    const firstInput = modal.querySelector('input, select');
    if (firstInput) {
        firstInput.focus();
    }
}

function closePaymentModal() {
    const modal = document.getElementById('paymentModal');
    if (modal) {
        modal.style.display = 'none';
        
        // Réinitialiser le formulaire
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }
}

function initializePaymentModal() {
    const modal = document.getElementById('paymentModal');
    if (!modal) return;
    
    // Bouton de fermeture
    const closeButton = modal.querySelector('.close-modal');
    if (closeButton) {
        closeButton.addEventListener('click', closePaymentModal);
    }
    
    // Fermer en cliquant à l'extérieur
    modal.addEventListener('click', function(event) {
        if (event.target === modal) {
            closePaymentModal();
        }
    });
    
    // Échapper pour fermer
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modal.style.display === 'flex') {
            closePaymentModal();
        }
    });
    
    // Sélection des méthodes de paiement
    const paymentMethods = modal.querySelectorAll('.payment-method-card');
    paymentMethods.forEach(method => {
        method.addEventListener('click', function() {
            // Désélectionner toutes les méthodes
            paymentMethods.forEach(m => m.classList.remove('selected'));
            
            // Sélectionner la méthode cliquée
            this.classList.add('selected');
            
            // Mettre à jour le champ caché
            const methodId = this.dataset.methodId;
            const hiddenInput = modal.querySelector('#selected-payment-method');
            if (hiddenInput) {
                hiddenInput.value = methodId;
            }
        });
    });
    
    // Formulaire de paiement
    const paymentForm = modal.querySelector('#paymentForm');
    if (paymentForm) {
        paymentForm.addEventListener('submit', handlePaymentSubmit);
    }
}

async function handlePaymentSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // Validation
    const amount = parseFloat(formData.get('amount'));
    const paymentMethod = formData.get('payment_method');
    
    if (!amount || amount <= 0) {
        showAlert('Veuillez saisir un montant valide', 'danger');
        return;
    }
    
    if (!paymentMethod) {
        showAlert('Veuillez sélectionner une méthode de paiement', 'warning');
        return;
    }
    
    // Désactiver le bouton de soumission
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.textContent = 'Traitement en cours...';
    
    try {
        // Envoyer la demande de paiement
        const response = await fetch('/portal/payment/process', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('Paiement traité avec succès!', 'success');
            
            // Fermer la modale après un délai
            setTimeout(() => {
                closePaymentModal();
                // Recharger la page pour afficher les mises à jour
                window.location.reload();
            }, 2000);
            
        } else {
            showAlert(result.error || 'Erreur lors du traitement du paiement', 'danger');
        }
        
    } catch (error) {
        console.error('Erreur de paiement:', error);
        showAlert('Erreur de connexion. Veuillez réessayer.', 'danger');
        
    } finally {
        // Réactiver le bouton
        submitButton.disabled = false;
        submitButton.textContent = originalText;
    }
}

function initializeFilters() {
    // Filtre par statut
    const statusFilter = document.getElementById('status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', applyFilters);
    }
    
    // Filtre par période
    const periodFilter = document.getElementById('period-filter');
    if (periodFilter) {
        periodFilter.addEventListener('change', applyFilters);
    }
    
    // Recherche
    const searchInput = document.getElementById('invoice-search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(applyFilters, 300);
        });
    }
}

function applyFilters() {
    const statusFilter = document.getElementById('status-filter')?.value || '';
    const periodFilter = document.getElementById('period-filter')?.value || '';
    const searchTerm = document.getElementById('invoice-search')?.value.toLowerCase() || '';
    
    const invoiceCards = document.querySelectorAll('.portal-invoice-card');
    
    invoiceCards.forEach(card => {
        let visible = true;
        
        // Filtre par statut
        if (statusFilter && card.dataset.status !== statusFilter) {
            visible = false;
        }
        
        // Filtre par période
        if (periodFilter) {
            const invoiceDate = new Date(card.dataset.date);
            const now = new Date();
            let showCard = false;
            
            switch (periodFilter) {
                case 'current_month':
                    showCard = invoiceDate.getMonth() === now.getMonth() && 
                              invoiceDate.getFullYear() === now.getFullYear();
                    break;
                case 'last_month':
                    const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
                    showCard = invoiceDate.getMonth() === lastMonth.getMonth() && 
                              invoiceDate.getFullYear() === lastMonth.getFullYear();
                    break;
                case 'current_year':
                    showCard = invoiceDate.getFullYear() === now.getFullYear();
                    break;
                default:
                    showCard = true;
            }
            
            if (!showCard) {
                visible = false;
            }
        }
        
        // Filtre par recherche
        if (searchTerm) {
            const cardText = card.textContent.toLowerCase();
            if (!cardText.includes(searchTerm)) {
                visible = false;
            }
        }
        
        // Afficher/masquer la carte
        card.style.display = visible ? 'block' : 'none';
    });
    
    // Afficher un message si aucun résultat
    updateNoResultsMessage();
}

function updateNoResultsMessage() {
    const visibleCards = document.querySelectorAll('.portal-invoice-card[style*="block"], .portal-invoice-card:not([style*="none"])');
    const noResultsMsg = document.getElementById('no-results-message');
    
    if (visibleCards.length === 0) {
        if (!noResultsMsg) {
            const message = document.createElement('div');
            message.id = 'no-results-message';
            message.className = 'alert-portal info';
            message.innerHTML = '<i class="fa fa-info-circle"></i> Aucune facture ne correspond à vos critères de recherche.';
            
            const container = document.querySelector('.invoices-container');
            if (container) {
                container.appendChild(message);
            }
        }
    } else {
        if (noResultsMsg) {
            noResultsMsg.remove();
        }
    }
}

function showAlert(message, type = 'info') {
    // Supprimer les alertes existantes
    const existingAlerts = document.querySelectorAll('.temp-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Créer la nouvelle alerte
    const alert = document.createElement('div');
    alert.className = `alert-portal ${type} temp-alert`;
    alert.innerHTML = `<i class="fa fa-${getAlertIcon(type)}"></i> ${message}`;
    
    // Ajouter l'alerte en haut de la page
    const container = document.querySelector('.edu-portal-accounting') || document.body;
    container.insertBefore(alert, container.firstChild);
    
    // Supprimer automatiquement après 5 secondes
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'warning': 'exclamation-triangle',
        'danger': 'times-circle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function formatCurrency(amount, currency = 'EUR') {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// Fonction utilitaire pour déboguer
function debugPayment(message, data = null) {
    if (window.location.hostname === 'localhost' || window.location.hostname.includes('dev')) {
        console.log('[Portal Payment]', message, data);
    }
}

// Exporter les fonctions pour les tests
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializePortalPayment,
        handlePaymentClick,
        openPaymentModal,
        closePaymentModal,
        formatCurrency
    };
} 