/**
 * NexCart — Collapsible Sidebar
 * 240px expanded, 60px collapsed. Linear.app aesthetic.
 */

import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, ShieldAlert, Radio, Bell,
  BarChart2, Settings, ChevronLeft, ChevronRight, Zap,
} from 'lucide-react';
import clsx from 'clsx';

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/skus', label: 'SKU Risk Radar', icon: ShieldAlert },
  { path: '/signals', label: 'Live Signals', icon: Radio },
  { path: '/nudges', label: 'Nudge Campaigns', icon: Bell },
  { path: '/analytics', label: 'Analytics', icon: BarChart2 },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar({ collapsed, onToggle }) {
  const location = useLocation();

  return (
    <aside
      className={clsx(
        'flex flex-col h-screen bg-bg-card border-r border-border',
        'transition-all duration-200 ease-in-out shrink-0',
        collapsed ? 'w-[60px]' : 'w-[240px]'
      )}
    >
      {/* Logo */}
      <div className={clsx(
        'flex items-center h-[56px] border-b border-border px-4',
        collapsed ? 'justify-center' : 'gap-3'
      )}>
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-accent-purple/20">
          <Zap className="w-4 h-4 text-accent-purple" />
        </div>
        {!collapsed && (
          <span className="text-lg font-bold text-text-primary tracking-tight">
            NexCart
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-2 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ path, label, icon: Icon }) => {
          const isActive = location.pathname === path;
          return (
            <NavLink
              key={path}
              to={path}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl',
                'transition-all duration-150 group',
                collapsed && 'justify-center px-0',
                isActive
                  ? 'bg-accent-purple/15 text-white'
                  : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'
              )}
            >
              <Icon className={clsx(
                'w-5 h-5 shrink-0',
                isActive ? 'text-accent-purple' : 'text-text-secondary group-hover:text-text-primary'
              )} />
              {!collapsed && (
                <span className="text-sm font-medium truncate">{label}</span>
              )}
              {isActive && !collapsed && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-accent-purple" />
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <button
        onClick={onToggle}
        className={clsx(
          'flex items-center justify-center h-12 border-t border-border',
          'text-text-secondary hover:text-text-primary hover:bg-bg-hover',
          'transition-colors duration-150'
        )}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? (
          <ChevronRight className="w-4 h-4" />
        ) : (
          <div className="flex items-center gap-2">
            <ChevronLeft className="w-4 h-4" />
            <span className="text-xs font-medium">Collapse</span>
          </div>
        )}
      </button>
    </aside>
  );
}

// ✓ Sidebar.jsx complete
