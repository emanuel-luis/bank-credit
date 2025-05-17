import React, { useEffect, useState } from 'react';
import { getNotifications, markNotificationAsRead, markAllNotificationsAsRead, deleteNotification } from '../services/notifications';
import { usePreferences } from '../contexts/PreferencesContext';

const NotificationsPage = () => {
  const { darkMode } = usePreferences();
  const [notifications, setNotifications] = useState([]);
  const [error, setError] = useState('');

  const fetchNotifications = async () => {
    try {
      const { data } = await getNotifications();
      setNotifications(data);
    } catch (err) {
      setError('Erro ao buscar notificações.');
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  useEffect(() => {
    document.body.className = darkMode ? 'dark-mode' : '';
  }, [darkMode]);

  const handleMarkAsRead = async (id) => {
    await markNotificationAsRead(id);
    fetchNotifications();
  };

  const handleMarkAllAsRead = async () => {
    await markAllNotificationsAsRead();
    fetchNotifications();
  };

  const handleDelete = async (id) => {
    await deleteNotification(id);
    fetchNotifications();
  };

  return (
    <div>
      <h2>Notificações</h2>
      <button className="darkmode-toggle" onClick={handleMarkAllAsRead}>Marcar todas como lidas</button>
      {error && <div className="error">{error}</div>}
      <ul>
        {notifications.map((n) => (
          <li key={n.id} style={{ fontWeight: n.read ? 'normal' : 'bold' }}>
            <b>{n.subject}</b> - {n.message} <br />
            <small>{new Date(n.created_at).toLocaleString()}</small>
            {!n.read && <button className="darkmode-toggle" onClick={() => handleMarkAsRead(n.id)}>Marcar como lida</button>}
            <button className="darkmode-toggle" onClick={() => handleDelete(n.id)}>Excluir</button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default NotificationsPage;
