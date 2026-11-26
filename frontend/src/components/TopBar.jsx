/**
 * NexCart — Top Bar
 * 56px with page title, live clock, MongoStatus, and avatar.
 */

import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Bell, LogOut } from 'lucide-react';
import MongoStatus from './MongoStatus';

export default function TopBar({ pageTitles = {} }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const pageTitle = pageTitles[location.pathname] || 'NexCart';
  const clockStr = time.toLocaleTimeString('en-US', { hour12: false });
  const user = JSON.parse(localStorage.getItem('nexcart_user') || '{}');
  const logout = () => {
    localStorage.removeItem('nexcart_access_token');
    localStorage.removeItem('nexcart_user');
    navigate('/login', { replace: true });
  };

  return (
    <header className="flex items-center justify-between h-[56px] px-6 bg-bg-card border-b border-border shrink-0">
      {/* Left: Page Title */}
      <h1 className="text-lg font-semibold text-text-primary truncate">
        {pageTitle}
      </h1>

      {/* Centre: Live Clock */}
      <div className="hidden md:flex items-center">
        <span className="text-sm font-mono text-text-secondary tabular-nums">
          {clockStr}
        </span>
      </div>

      {/* Right: MongoStatus + Bell + Avatar */}
      <div className="flex items-center gap-4">
        <MongoStatus />

        {/* Notification Bell */}
        <button className="relative p-2 rounded-lg hover:bg-bg-hover transition-colors">
          <Bell className="w-5 h-5 text-text-secondary" />
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-accent-danger animate-pulse-dot" />
        </button>

        <span className="hidden lg:block text-xs text-text-secondary capitalize">{user.role?.replace('_', ' ')}</span>
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-accent-purple/20 text-accent-purple text-xs font-bold" title={user.name || 'NexCart user'}>
          {(user.name || 'NC').split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase()}
        </div>
        <button onClick={logout} aria-label="Sign out" className="p-2 rounded-lg hover:bg-bg-hover transition-colors"><LogOut className="w-4 h-4 text-text-secondary" /></button>
      </div>
    </header>
  );
}

// ✓ TopBar.jsx complete
