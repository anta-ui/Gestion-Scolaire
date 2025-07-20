/* Module Education Enhanced - JavaScript */

console.log('Module Education Enhanced - JavaScript chargé');

// Fonctions utilitaires pour le module
var StudentEnhanced = {
    
    // Formater un score en pourcentage
    formatScore: function(score) {
        return Math.round(score) + '%';
    },
    
    // Obtenir la couleur pour un score
    getScoreColor: function(score) {
        if (score >= 80) return '#28a745';
        if (score >= 60) return '#17a2b8';
        if (score >= 40) return '#ffc107';
        return '#dc3545';
    },
    
    // Animation des cartes au survol
    initCardAnimations: function() {
        document.addEventListener('DOMContentLoaded', function() {
            var cards = document.querySelectorAll('.student-card');
            cards.forEach(function(card) {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-2px)';
                });
                card.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0)';
                });
            });
        });
    }
};

// Initialiser les animations
StudentEnhanced.initCardAnimations();

// Rendre disponible globalement
window.StudentEnhanced = StudentEnhanced; 