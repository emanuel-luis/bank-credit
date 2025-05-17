import React, { useContext, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { AuthProvider, AuthContext } from './contexts/AuthContext';
import { PreferencesProvider, usePreferences } from './contexts/PreferencesContext';
import Loader from './components/Loader';
import PrivateRoute from './components/PrivateRoute';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import CreditRequestsPage from './pages/CreditRequestsPage';
import NotificationsPage from './pages/NotificationsPage';
import GraphPage from './pages/GraphPage';
import './App.css';
import './pages/LoginRegister.css';
import FancyHome from './pages/FancyHome';
import ProtectedRoutesMiddleware from './components/ProtectedRoutesMiddleware';

const PortalLayout = ({ children }) => {
  const { logout, user } = useContext(AuthContext);
  const navigate = useNavigate();
  return (
    <div className="portal-layout">
      <aside className="portal-sidebar">
        <div className="portal-user">👤 {user?.username}</div>
        <nav>
          <button className="darkmode-toggle" onClick={() => navigate('/portal/requests')}>Solicitações</button>
          <button className="darkmode-toggle" onClick={() => navigate('/portal/notifications')}>Notificações</button>
          <button className="darkmode-toggle" onClick={() => navigate('/portal/graph')}>Fluxo</button>
          <button className="darkmode-toggle" onClick={() => logout(() => navigate('/'))}>Sair</button>
        </nav>
      </aside>
      <main className="portal-main">{children}</main>
    </div>
  );
};

function DarkModeFloatingButton() {
  const { darkMode, setDarkMode } = usePreferences();
  return (
    <button
      className="floating-darkmode-toggle"
      onClick={() => setDarkMode(d => !d)}
      title="Alternar modo claro/escuro"
      style={{left: 24, bottom: 24, top: 'auto', position: 'fixed'}}
    >
      <span style={{fontSize: '1.2rem'}}>{darkMode ? '🌙' : '☀️'}</span>
    </button>
  );
}

function App() {
  return (
    <PreferencesProvider>
      <AuthProvider>
        <Router>
            <React.Suspense fallback={<Loader />}>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/" element={<FancyHome />} />
                <Route path="/portal" element={<PrivateRoute><PortalLayout><Dashboard /></PortalLayout></PrivateRoute>} />
                <Route path="/portal/requests" element={<PrivateRoute><PortalLayout><CreditRequestsPage /></PortalLayout></PrivateRoute>} />
                <Route path="/portal/notifications" element={<PrivateRoute><PortalLayout><NotificationsPage /></PortalLayout></PrivateRoute>} />
                <Route path="/portal/graph" element={<PrivateRoute><PortalLayout><GraphPage /></PortalLayout></PrivateRoute>} />
                <Route path="*" element={<Navigate to="/" />} />
              </Routes>
              <DarkModeFloatingButton />
            </React.Suspense>
        </Router>
      </AuthProvider>
    </PreferencesProvider>
  );
}

export default App;
