import React, { createContext, useState, useEffect } from 'react';
import { getMe } from '../services/auth';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      getMe()
        .then((res) => setUser(res.data))
        .catch(() => setUser(null))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = (token) => {
    localStorage.setItem('access_token', token);
    getMe().then((res) => setUser(res.data));
  };

  const logout = (afterLogout) => {
    localStorage.removeItem('access_token');
    setUser(null);
    if (typeof afterLogout === 'function') afterLogout();
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
