import React, { createContext, useContext } from 'react';
import odooApi from '../services/odooApi.jsx';

const OdooContext = createContext();

export const OdooProvider = ({ children }) => {
  const contextValue = {
    api: odooApi
  };

  return (
    <OdooContext.Provider value={contextValue}>
      {children}
    </OdooContext.Provider>
  );
};

export const useOdoo = () => {
  const context = useContext(OdooContext);
  
  if (!context) {
    throw new Error('useOdoo must be used within an OdooProvider');
  }
  
  return context;
};

export default OdooContext; 