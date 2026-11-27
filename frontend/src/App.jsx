/**
 * NexCart role-specific application experiences.
 */

import { useState } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { useAuth } from './auth/AuthContext';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import ProtectedRoute from './components/ProtectedRoute';
import Analytics from './pages/Analytics';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Nudges from './pages/Nudges';
import Settings from './pages/Settings';
import Signals from './pages/Signals';
import SKURisk from './pages/SKURisk';
import Unauthorized from './pages/Unauthorized';
import UserManagement from './pages/UserManagement';
import {
  AdminAccess, AdminActivity, AdminAudit, AdminHealth, AdminOverview,
  DisruptionWorkspace, ViewerOverview,
} from './pages/RoleWorkspaces';

const PAGE_TITLES = {
  '/admin/dashboard': 'Admin Overview',
  '/admin/users': 'User Management',
  '/admin/access': 'Role & Access Control',
  '/admin/audit': 'Audit Trail',
  '/admin/health': 'System Health',
  '/admin/activity': 'Platform Activity',
  '/admin/settings': 'Platform Settings',
  '/manager/dashboard': 'Operations Command Center',
  '/manager/inventory': 'Inventory & SKU Management',
  '/manager/disruptions': 'Disruption Center',
  '/manager/signals': 'Signal Monitor',
  '/manager/analytics': 'Operational Analytics',
  '/intelligence/overview': 'Intelligence Overview',
  '/intelligence/risks': 'Risk Explorer',
  '/intelligence/disruptions': 'Disruption Insights',
  '/intelligence/signals': 'Signal Explorer',
  '/intelligence/analytics': 'Analytics & Trends',
};

function RoleHomeRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex h-screen items-center justify-center bg-bg-base text-text-secondary">Loading NexCart…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === 'admin') return <Navigate to="/admin/dashboard" replace />;
  if (user.role === 'manager') return <Navigate to="/manager/dashboard" replace />;
  if (user.role === 'viewer') return <Navigate to="/intelligence/overview" replace />;
  return <Navigate to="/unauthorized" replace />;
}

function MainLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base">
      <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar pageTitles={PAGE_TITLES} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Routes>
            <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="/admin/dashboard" element={<ProtectedRoute roles={['admin']} permission="dashboard:view"><AdminOverview /></ProtectedRoute>} />
            <Route path="/admin/users" element={<ProtectedRoute roles={['admin']} permission="users:view"><UserManagement /></ProtectedRoute>} />
            <Route path="/admin/access" element={<ProtectedRoute roles={['admin']} permission="users:view"><AdminAccess /></ProtectedRoute>} />
            <Route path="/admin/audit" element={<ProtectedRoute roles={['admin']} permission="audit_logs:view"><AdminAudit /></ProtectedRoute>} />
            <Route path="/admin/health" element={<ProtectedRoute roles={['admin']} permission="dashboard:view"><AdminHealth /></ProtectedRoute>} />
            <Route path="/admin/activity" element={<ProtectedRoute roles={['admin']} permission="dashboard:view"><AdminActivity /></ProtectedRoute>} />
            <Route path="/admin/settings" element={<ProtectedRoute roles={['admin']} permission="settings:view"><Settings /></ProtectedRoute>} />

            <Route path="/manager" element={<Navigate to="/manager/dashboard" replace />} />
            <Route path="/manager/dashboard" element={<ProtectedRoute roles={['manager']} permission="dashboard:view"><Dashboard /></ProtectedRoute>} />
            <Route path="/manager/inventory" element={<ProtectedRoute roles={['manager']} permission="sku:view"><SKURisk /></ProtectedRoute>} />
            <Route path="/manager/disruptions" element={<ProtectedRoute roles={['manager']} permission="disruptions:view"><DisruptionWorkspace /></ProtectedRoute>} />
            <Route path="/manager/signals" element={<ProtectedRoute roles={['manager']} permission="signals:view"><Signals /></ProtectedRoute>} />
            <Route path="/manager/analytics" element={<ProtectedRoute roles={['manager']} permission="analytics:view"><Analytics /></ProtectedRoute>} />

            <Route path="/intelligence" element={<Navigate to="/intelligence/overview" replace />} />
            <Route path="/intelligence/overview" element={<ProtectedRoute roles={['viewer']} permission="dashboard:view"><ViewerOverview /></ProtectedRoute>} />
            <Route path="/intelligence/risks" element={<ProtectedRoute roles={['viewer']} permission="sku:view"><SKURisk readOnly /></ProtectedRoute>} />
            <Route path="/intelligence/disruptions" element={<ProtectedRoute roles={['viewer']} permission="disruptions:view"><DisruptionWorkspace readOnly /></ProtectedRoute>} />
            <Route path="/intelligence/signals" element={<ProtectedRoute roles={['viewer']} permission="signals:view"><Signals /></ProtectedRoute>} />
            <Route path="/intelligence/analytics" element={<ProtectedRoute roles={['viewer']} permission="analytics:view"><Analytics /></ProtectedRoute>} />

            <Route path="/dashboard" element={<RoleHomeRedirect />} />
            <Route path="/skus" element={<RoleHomeRedirect />} />
            <Route path="/signals" element={<RoleHomeRedirect />} />
            <Route path="/analytics" element={<RoleHomeRedirect />} />
            <Route path="/nudges" element={<ProtectedRoute permission="nudges:view"><Nudges /></ProtectedRoute>} />
            <Route path="/settings" element={<RoleHomeRedirect />} />
            <Route path="/users" element={<RoleHomeRedirect />} />
            <Route path="*" element={<Navigate to={location.pathname.startsWith('/unauthorized') ? '/unauthorized' : '/'} replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/unauthorized" element={<Unauthorized />} />
      <Route path="/" element={<RoleHomeRedirect />} />
      <Route path="/*" element={<ProtectedRoute><MainLayout /></ProtectedRoute>} />
    </Routes>
  );
}
