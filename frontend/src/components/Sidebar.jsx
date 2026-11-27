/**
 * NexCart role-specific navigation workspaces.
 */

import { NavLink, useLocation } from 'react-router-dom';
import {
  Activity, BarChart2, ChevronLeft, ChevronRight, Database,
  LayoutDashboard, Radio, Settings, Shield, ShieldAlert, Signal, Users, Zap,
} from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '../auth/AuthContext';

const WORKSPACES = {
  admin: {
    name: 'Governance',
    sections: [
      { title: 'Overview', links: [{ path: '/admin/dashboard', label: 'Admin Overview', icon: LayoutDashboard, permission: 'dashboard:view' }] },
      { title: 'Governance', links: [
        { path: '/admin/users', label: 'User Management', icon: Users, permission: 'users:view' },
        { path: '/admin/access', label: 'Role & Access', icon: Shield, permission: 'users:view' },
        { path: '/admin/audit', label: 'Audit Trail', icon: Activity, permission: 'audit_logs:view' },
      ] },
      { title: 'Platform Monitoring', links: [
        { path: '/admin/health', label: 'System Health', icon: Database, permission: 'dashboard:view' },
        { path: '/admin/activity', label: 'Platform Activity', icon: Signal, permission: 'dashboard:view' },
      ] },
      { title: 'Configuration', links: [{ path: '/admin/settings', label: 'Platform Settings', icon: Settings, permission: 'settings:view' }] },
    ],
  },
  manager: {
    name: 'Operations',
    sections: [
      { title: 'Command Center', links: [{ path: '/manager/dashboard', label: 'Operations Overview', icon: LayoutDashboard, permission: 'dashboard:view' }] },
      { title: 'Operations', links: [
        { path: '/manager/inventory', label: 'Inventory & SKUs', icon: ShieldAlert, permission: 'sku:view' },
        { path: '/manager/disruptions', label: 'Disruption Center', icon: Signal, permission: 'disruptions:view' },
        { path: '/manager/signals', label: 'Signal Monitor', icon: Radio, permission: 'signals:view' },
      ] },
      { title: 'Performance', links: [{ path: '/manager/analytics', label: 'Operational Analytics', icon: BarChart2, permission: 'analytics:view' }] },
    ],
  },
  viewer: {
    name: 'Intelligence',
    sections: [
      { title: 'Explore', links: [{ path: '/intelligence/overview', label: 'Intelligence Overview', icon: LayoutDashboard, permission: 'dashboard:view' }] },
      { title: 'Supply Chain Intelligence', links: [
        { path: '/intelligence/risks', label: 'Risk Explorer', icon: ShieldAlert, permission: 'sku:view' },
        { path: '/intelligence/disruptions', label: 'Disruption Insights', icon: Signal, permission: 'disruptions:view' },
        { path: '/intelligence/signals', label: 'Signal Explorer', icon: Radio, permission: 'signals:view' },
      ] },
      { title: 'Reports', links: [{ path: '/intelligence/analytics', label: 'Analytics & Trends', icon: BarChart2, permission: 'analytics:view' }] },
    ],
  },
};

export default function Sidebar({ collapsed, onToggle }) {
  const location = useLocation();
  const { user, hasPermission } = useAuth();
  const workspace = WORKSPACES[user?.role] || WORKSPACES.viewer;

  return (
    <aside className={clsx(
      'flex h-screen shrink-0 flex-col border-r border-border bg-bg-card transition-all duration-200 ease-in-out',
      collapsed ? 'w-[60px]' : 'w-[250px]'
    )}>
      <div className={clsx('flex h-[56px] items-center border-b border-border px-4', collapsed ? 'justify-center' : 'gap-3')}>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-purple/20"><Zap className="h-4 w-4 text-accent-purple" /></div>
        {!collapsed && <div className="min-w-0"><span className="block truncate text-lg font-bold tracking-tight text-text-primary">NexCart</span><span className="text-[10px] uppercase tracking-wider text-text-secondary">{workspace.name} workspace</span></div>}
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto px-2 py-4">
        {workspace.sections.map((section) => {
          const links = section.links.filter((link) => hasPermission(link.permission));
          if (!links.length) return null;
          return <div key={section.title}>
            {!collapsed && <p className="mb-2 px-3 text-[9px] font-bold uppercase tracking-[0.16em] text-text-secondary/70">{section.title}</p>}
            <div className="space-y-1">
              {links.map(({ path, label, icon: Icon }) => {
                const active = location.pathname === path || location.pathname.startsWith(`${path}/`);
                return <NavLink key={path} to={path} title={collapsed ? label : undefined} className={clsx(
                  'group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all duration-150',
                  collapsed && 'justify-center px-0',
                  active ? 'bg-accent-purple/15 text-white' : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'
                )}>
                  <Icon className={clsx('h-4.5 w-4.5 shrink-0', active ? 'text-accent-purple' : 'group-hover:text-text-primary')} />
                  {!collapsed && <span className="truncate text-xs font-medium">{label}</span>}
                  {active && !collapsed && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-accent-purple" />}
                </NavLink>;
              })}
            </div>
          </div>;
        })}
      </nav>
      <button onClick={onToggle} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} className="flex h-12 items-center justify-center border-t border-border text-text-secondary transition-colors hover:bg-bg-hover hover:text-text-primary">
        {collapsed ? <ChevronRight className="h-4 w-4" /> : <div className="flex items-center gap-2"><ChevronLeft className="h-4 w-4" /><span className="text-xs font-medium">Collapse</span></div>}
      </button>
    </aside>
  );
}
