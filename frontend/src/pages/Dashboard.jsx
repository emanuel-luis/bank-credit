import React, { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { usePreferences } from '../contexts/PreferencesContext';

const Dashboard = () => {
  const { user, logout } = useContext(AuthContext);
  const { darkMode } = usePreferences();
  const navigate = useNavigate();

  useEffect(() => {
    document.body.className = darkMode ? 'dark-mode' : '';
  }, [darkMode]);

  return (
    <div className="dashboard-container">
      <h1>Bem-vindo, {user?.username}!</h1>
      <nav>
        <button className="darkmode-toggle" onClick={() => navigate('/requests')}>Solicitações de Crédito</button>
        <button className="darkmode-toggle" onClick={() => navigate('/notifications')}>Notificações</button>
        <button className="darkmode-toggle" onClick={() => navigate('/graph')}>Fluxo de Processos</button>
        <button className="darkmode-toggle" onClick={() => logout(() => navigate('/'))}>Sair</button>
      </nav>
    </div>
  );
};

export default Dashboard;
