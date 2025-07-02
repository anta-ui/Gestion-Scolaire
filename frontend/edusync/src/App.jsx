import React from 'react';

import { Routes, Route, Navigate, BrowserRouter } from 'react-router-dom';
import { OdooProvider } from './contexts/OdooContext';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/layout/Layout';
import HomePage from './components/home';
function App() {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true
      }}
    >
      <OdooProvider>
        <AuthProvider>
          <Layout>
            <Routes>
              {/* Authentification */}
             
              {/* Page d'accueil */}
              <Route path="/" element={<HomePage />} />
              
              {/* Redirection par défaut */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Layout>
        </AuthProvider>
      </OdooProvider>
    </BrowserRouter>
  );
}

export default App;