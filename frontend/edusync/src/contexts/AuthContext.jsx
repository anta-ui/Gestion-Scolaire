import React, { createContext, useState, useContext, useEffect, useRef } from 'react';
// Retirer useNavigate du contexte car il doit être dans un composant à l'intérieur du Router
import odooApi from '../services/odooApi.jsx';

const AuthContext = createContext(null);


// Configuration API depuis les variables d'environnement (Vite)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8069';
const ODOO_DATABASE = import.meta.env.VITE_ODOO_DATABASE || 'school_management_new';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const authCheckRef = useRef(false); // Éviter les vérifications multiples

  useEffect(() => {
    // Éviter les appels multiples si déjà en cours
    if (authCheckRef.current) {
      return;
    }
    
    const checkAuth = async () => {
      authCheckRef.current = true;
      
      try {
        console.log("Vérification de l'authentification au démarrage...");
        
        // Vérifier si nous avons une session valide avec le service API
        const isAuthenticated = await odooApi.isAuthenticated();
        
        if (isAuthenticated) {
          // Si authentifié, récupérer les informations utilisateur
          try {
            const userInfo = await odooApi.getUserInfo();
            setUser(userInfo);
            console.log("Utilisateur authentifié:", userInfo);
          } catch (userError) {
            console.warn("Impossible de récupérer les infos utilisateur:", userError);
            // Faire un appel au test endpoint pour avoir les infos de base
            try {
              const response = await odooApi.makeRequest('/api/test');
              if (response.session_valid && response.user) {
                setUser(response.user);
                console.log("Utilisateur authentifié (via test):", response.user);
              }
            } catch (testError) {
              console.warn("Échec du test endpoint:", testError);
            }
          }
        } else {
          console.log("Aucune session valide trouvée");
        }
      } catch (error) {
        console.error('Erreur lors de la vérification de l\'authentification:', error);
        setError(error.message);
      } finally {
        setLoading(false);
        authCheckRef.current = false;
      }
    };

    checkAuth();
  }, []); // Dépendances vides pour ne s'exécuter qu'une fois

  const login = async (username, password) => {
    setLoading(true);
    setError(null);
    
    try {
      console.log(`Tentative de connexion avec: ${username}`);
      
      const result = await odooApi.authenticate({ username, password });

      if (result.success) {
        setUser(result.user);
        console.log("Connexion réussie:", result.user);
        // Ne pas naviguer directement ici, laisser le composant gérer la navigation
        return { success: true };
      } else {
        setError(result.error);
        return { success: false, error: result.error };
      }
    } catch (error) {
      console.error('Erreur lors de la connexion:', error);
      const errorMessage = error.message || 'Erreur de connexion au serveur';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      setLoading(true);
      console.log("Déconnexion en cours...");
      
      await odooApi.logout();
      
      setUser(null);
      console.log("Déconnexion réussie");
      // Ne pas naviguer directement ici, laisser le composant gérer la navigation
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    isAuthenticated: !!user
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ 
            animation: 'spin 1s linear infinite', 
            width: '48px', 
            height: '48px', 
            border: '4px solid #f3f3f3',
            borderTop: '4px solid #00008B',
            borderRadius: '50%',
            margin: '0 auto'
          }}></div>
          <p style={{ marginTop: '16px', color: '#666' }}>Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 