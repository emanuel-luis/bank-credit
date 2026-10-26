import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { fetchMe, login as apiLogin } from '../api/auth';
import { tokenStore } from '../api/client';
import type { Me, Role } from '../api/types';

export type UserRole = Role;

interface AuthContextType {
  user: Me | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<Me>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<Me | null>(null);
  const [isLoading, setIsLoading] = useState(() => tokenStore.get() !== null);

  useEffect(() => {
    if (!tokenStore.get()) return;
    fetchMe()
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setIsLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    tokenStore.set(await apiLogin(email, password));
    try {
      const me = await fetchMe();
      setUser(me);
      return me;
    } catch (err) {
      tokenStore.clear();
      throw err;
    }
  };

  const logout = () => {
    tokenStore.clear();
    setUser(null);
    queryClient.clear();
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook next to its provider on purpose.
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
