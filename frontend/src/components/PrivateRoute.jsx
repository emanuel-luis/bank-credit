import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  const navigate = useNavigate();
  if (loading) return null;
  if (!user) {
    navigate('/login');
  }
  return children;
};

export default PrivateRoute;
