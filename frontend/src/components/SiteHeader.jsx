import React from 'react';
import { usePreferences } from '../contexts/PreferencesContext';
import './SiteHeader.css'; // Adicionando estilos específicos para o cabeçalho

const SiteHeader = () => {
  const { darkMode, setDarkMode } = usePreferences();
  return (
    <header className="fancy-landing-header centered-header">
      <div className="logo-area">
        <img src="/vite.svg" alt="Logo" className="site-logo" />
        <span className="site-title">Bank Credit System</span>
      </div>
      <div className="header-actions">
        <button className="darkmode-toggle" onClick={() => setDarkMode(d => !d)} title="Alternar modo claro/escuro">
          {darkMode ? '🌙' : '☀️'}
        </button>
        <a className="fancy-btn login-header-btn" href="/login">Entrar</a>
      </div>
    </header>
  );
};

export default SiteHeader;
