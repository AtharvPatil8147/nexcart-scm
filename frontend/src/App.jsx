/**
 * NexCart — App Shell with React Router v6
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';

// Lazy-loaded page placeholders (Phase 6 will build these)
import Dashboard from './pages/Dashboard';
import SKURisk from './pages/SKURisk';
import Signals from './pages/Signals';
import Nudges from './pages/Nudges';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import Login from './pages/Login';

const PAGE_TITLES = {
  '/dashboard': 'Dashboard',
  '/skus': 'SKU Risk Radar',
  '/signals': 'Live Signals',
  '/nudges': 'Nudge Campaigns',
  '/analytics': 'Analytics',
  '/settings': 'Settings',
};

function MainLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-bg-base">
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar pageTitles={PAGE_TITLES} />
        <main className="flex-1 overflow-y-auto p-6">
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/skus" element={<SKURisk />} />
            <Route path="/signals" element={<Signals />} />
            <Route path="/nudges" element={<Nudges />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function ProtectedRoute({ children }) {
  return localStorage.getItem('nexcart_access_token') ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/*" element={<ProtectedRoute><MainLayout /></ProtectedRoute>} />
    </Routes>
  );
}

// ✓ App.jsx complete
