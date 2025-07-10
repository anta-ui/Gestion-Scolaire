import React from 'react';
import { Routes, Route, Navigate, BrowserRouter } from 'react-router-dom';
import { Box } from '@mui/material';
import { OdooProvider } from './contexts/OdooContext';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/layout/Layout';
import HomePage from './components/home';
import AboutPage from './components/AboutPage';
import LoginPage from './components/auth/LoginPage';
function App() {
  return (
    <Box sx={{ width: '100%', minHeight: '100vh' }}>
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
                
                {/* Page À propos */}
                <Route path="/about" element={<AboutPage />} />
                <Route path="/login" element={<LoginPage />} />

                
                {/* Redirection par défaut */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          </AuthProvider>
        </OdooProvider>
      </BrowserRouter>
    </Box>
  );
}

export default App;