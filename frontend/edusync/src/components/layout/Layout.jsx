import React from 'react';
import { useLocation } from 'react-router-dom';
import { Box } from '@mui/material';
import Sidebar from './Sidebar';

const Layout = ({ children }) => {
  const location = useLocation();
  const isHomePage = location.pathname === '/';
  const isLoginPage = location.pathname === '/login';
  const isAboutPage = location.pathname === '/about';
  const isContactPage = location.pathname === '/contact';
  const isPortailParentPage = location.pathname === '/parent';
  const isFormulairePubliquePage = location.pathname === '/formulaire-publique';
 
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {!isHomePage && !isLoginPage && !isAboutPage && !isContactPage && !isPortailParentPage && !isFormulairePubliquePage && <Sidebar />}
      <Box component="main" sx={{ flexGrow: 1, bgcolor: 'background.default' }}>
        {children}
      </Box>
    </Box>
  );
};

export default Layout; 