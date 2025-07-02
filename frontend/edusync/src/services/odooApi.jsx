// odooApi.jsx
// Configuration API depuis les variables d'environnement
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8069';
const ODOO_DATABASE = import.meta.env.VITE_ODOO_DATABASE || 'school_management_new';

// Configuration par défaut pour fetch
const defaultConfig = {
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
};

class OdooAPI {
  constructor() {
    this.sessionId = localStorage.getItem('session_id') || null;
  };
}

// Exporter une instance unique
const odooApi = new OdooAPI();
export default odooApi; 