// Utilitaires pour l'authentification et la gestion de session
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8069';

// Configuration axios par défaut pour l'authentification
const apiClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest'
  },
  timeout: 10000
});

// Intercepteur pour gérer les réponses d'erreur d'authentification
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn('Session expirée détectée');
      // Ici vous pourriez déclencher une redirection vers la page de connexion
      // ou afficher un modal de reconnexion
      
      // Émettre un événement personnalisé pour notifier l'application
      window.dispatchEvent(new CustomEvent('auth:sessionExpired', {
        detail: { error: error.response.data }
      }));
    }
    return Promise.reject(error);
  }
);

export const authUtils = {
  // Vérifier l'état de la session
  async checkSession() {
    try {
      const response = await apiClient.get('/api/debug/session');
      return {
        success: true,
        isValid: response.data.session_info?.session_valid || false,
        sessionInfo: response.data.session_info,
        userInfo: response.data.environment_info
      };
    } catch (error) {
      console.error('Erreur lors de la vérification de session:', error);
      return {
        success: false,
        isValid: false,
        error: error.message
      };
    }
  },

  // Effectuer une requête authentifiée
  async makeAuthenticatedRequest(endpoint, options = {}) {
    try {
      // Vérifier d'abord la session si demandé
      if (options.checkSession !== false) {
        const sessionCheck = await this.checkSession();
        if (!sessionCheck.isValid) {
          throw new Error('Session invalide ou expirée');
        }
      }

      // Faire la requête
      const response = await apiClient({
        url: endpoint,
        method: options.method || 'GET',
        data: options.data,
        params: options.params,
        ...options
      });

      return {
        success: true,
        data: response.data,
        status: response.status
      };
    } catch (error) {
      console.error(`Erreur lors de la requête vers ${endpoint}:`, error);
      return {
        success: false,
        error: error.message,
        status: error.response?.status
      };
    }
  },

  // Récupérer les données du tableau de bord avec gestion d'erreur
  async getDashboardData(section) {
    return this.makeAuthenticatedRequest(`/api/dashboard/${section}`, {
      params: {
        timestamp: new Date().getTime(), // Éviter le cache
        db: import.meta.env.VITE_ODOO_DATABASE || 'odoo_ecole'
      }
    });
  },

  // Méthodes spécifiques pour chaque section
  async getStudents() {
    return this.getDashboardData('students');
  },

  async getClasses() {
    return this.getDashboardData('classes');
  },

  async getTeachers() {
    return this.getDashboardData('teachers');
  },

  async getGrades() {
    return this.getDashboardData('grades');
  },

  async getStatistics() {
    return this.getDashboardData('statistics');
  }
};

// Fonction pour configurer les écouteurs d'événements d'authentification
export const setupAuthListeners = () => {
  window.addEventListener('auth:sessionExpired', (event) => {
    console.warn('Session expirée:', event.detail);
    
    // Afficher un message à l'utilisateur
    const message = 'Votre session a expiré. Veuillez vous reconnecter.';
    
    // Vous pouvez remplacer ceci par votre système de notification préféré
    if (window.showNotification) {
      window.showNotification(message, 'warning');
    } else {
      alert(message);
    }
    
    // Optionnel: redirection automatique vers la page de connexion
    // window.location.href = '/login';
  });
};

export default authUtils; 