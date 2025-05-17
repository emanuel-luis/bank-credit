import { useContext, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';

// Define as rotas desprotegidas explicitamente
const unprotectedRoutes = ['/', '/login'];

export default function ProtectedRoutesMiddleware({ children }) {
  const { user, loading } = useContext(AuthContext);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !user && !unprotectedRoutes.includes(location.pathname)) {
      navigate('/login', { replace: true });
    }
  }, [user, loading, location.pathname, navigate]);

  return children;
}
