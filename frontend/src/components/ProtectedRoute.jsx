import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export default function ProtectedRoute({ permission, roles, children }) {
  const { user, isAuthenticated, loading, hasPermission } = useAuth();
  const location = useLocation();
  if (loading) return <div className="flex h-screen items-center justify-center text-text-secondary">Loading NexCart…</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (roles && !roles.includes(user?.role)) return <Navigate to="/unauthorized" replace />;
  if (permission && !hasPermission(permission)) return <Navigate to="/unauthorized" replace />;
  return children;
}
