import { createContext, useContext, useEffect, useState } from 'react';
import { getCurrentUser, login as apiLogin } from '../api/client';
import { hasPermission as checkPermission } from './permissions';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('nexcart_user') || 'null'); } catch { return null; }
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('nexcart_access_token');
    if (!token) {
      setLoading(false);
      return;
    }
    getCurrentUser()
      .then((profile) => {
        setUser(profile);
        localStorage.setItem('nexcart_user', JSON.stringify(profile));
      })
      .catch(() => {
        setUser(null);
        localStorage.removeItem('nexcart_access_token');
        localStorage.removeItem('nexcart_user');
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (credentials) => {
    const result = await apiLogin(credentials);
    localStorage.setItem('nexcart_access_token', result.access_token);
    localStorage.setItem('nexcart_user', JSON.stringify(result.user));
    setUser(result.user);
    return result.user;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('nexcart_access_token');
    localStorage.removeItem('nexcart_user');
  };

  const hasPermission = (permission) => checkPermission(user, permission);

  return (
    <AuthContext.Provider value={{ user, role: user?.role, isAuthenticated: Boolean(user), loading, login, logout, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
