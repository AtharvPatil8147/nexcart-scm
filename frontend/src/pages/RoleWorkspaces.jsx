import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Activity, AlertTriangle, ArrowUpRight, Database, Radio, Shield, ShieldAlert,
  Signal, Users, Wifi, WifiOff,
} from 'lucide-react';
import {
  Cell, Pie, PieChart, ResponsiveContainer, Tooltip,
} from 'recharts';
import {
  getAuditLogs, getDisruptions, getHealth, getNudges, getSignalHistory, getSkus, getStats,
  getUsers, getRiskTrend, testDbConnection, triggerDisruptionAgent,
} from '../api/client';
import { ROLE_PERMISSIONS } from '../auth/permissions';
import { useAuth } from '../auth/AuthContext';
import RiskBadge from '../components/RiskBadge';
import StatCard from '../components/StatCard';

const cardClass = 'rounded-card border border-border bg-bg-card p-5';
const roles = ['admin', 'manager', 'viewer'];
const roleLabels = { admin: 'Admin', manager: 'Manager', viewer: 'Viewer' };
const roleColors = ['#7C6DDD', '#1D9E75', '#EF9F27'];

function PageHeading({ eyebrow, title, description, icon: Icon }) {
  return (
    <header className="mb-6">
      {eyebrow && <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-accent-purple">{eyebrow}</p>}
      <h1 className="flex items-center gap-2 text-xl font-bold text-text-primary">
        {Icon && <Icon className="h-5 w-5 text-accent-purple" />}{title}
      </h1>
      {description && <p className="mt-1 text-sm text-text-secondary">{description}</p>}
    </header>
  );
}

function DataLink({ to, title, detail, icon: Icon }) {
  return (
    <Link to={to} className={`${cardClass} group block transition-colors hover:border-accent-purple/40`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-accent-purple/15 text-accent-purple"><Icon className="h-4 w-4" /></div>
          <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
          <p className="mt-1 text-xs text-text-secondary">{detail}</p>
        </div>
        <ArrowUpRight className="h-4 w-4 text-text-secondary transition-colors group-hover:text-accent-purple" />
      </div>
    </Link>
  );
}

export function AdminOverview() {
  const users = useQuery({ queryKey: ['admin-users'], queryFn: () => getUsers({}) });
  const stats = useQuery({ queryKey: ['admin-platform-stats'], queryFn: getStats });
  const disruptions = useQuery({ queryKey: ['admin-disruption-count'], queryFn: () => getDisruptions({ limit: 1 }) });
  const campaigns = useQuery({ queryKey: ['admin-campaign-count'], queryFn: () => getNudges({ limit: 1 }) });
  const db = useQuery({ queryKey: ['admin-db-health'], queryFn: testDbConnection, refetchInterval: 30000 });
  const logs = useQuery({ queryKey: ['admin-recent-audit'], queryFn: () => getAuditLogs(8) });
  const accounts = users.data?.items || [];
  const roleCounts = roles.map((role, index) => ({
    name: roleLabels[role],
    value: accounts.filter((account) => account.role === role).length,
    color: roleColors[index],
  }));
  const activeUsers = accounts.filter((account) => account.active).length;

  return (
    <div className="space-y-6">
      <PageHeading eyebrow="Platform governance" title="Admin overview" description="Platform access, service health, and system-wide activity." icon={Shield} />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard label="Registered users" value={users.data?.total ?? 0} icon={Users} color="purple" loading={users.isLoading} />
        <StatCard label="Active users" value={activeUsers} icon={Activity} color="teal" loading={users.isLoading} />
        <StatCard label="Inactive users" value={users.data ? users.data.total - activeUsers : 0} icon={Users} color="amber" loading={users.isLoading} />
        <StatCard label="Monitored SKUs" value={stats.data?.total_skus ?? 0} icon={ShieldAlert} color="amber" loading={stats.isLoading} />
        <StatCard label="Disruption records" value={disruptions.data?.total ?? 0} icon={Signal} color="purple" loading={disruptions.isLoading} />
        <StatCard label="Signals · 24h" value={stats.data?.signal_events_24h ?? 0} icon={Radio} color="purple" loading={stats.isLoading} />
        <StatCard label="Nudge campaigns" value={campaigns.data?.total ?? 0} icon={Activity} color="teal" loading={campaigns.isLoading} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.3fr)_minmax(300px,0.7fr)]">
        <section className={cardClass}>
          <div className="mb-4 flex items-center justify-between">
            <div><h2 className="text-sm font-semibold text-text-primary">Platform services</h2><p className="mt-1 text-xs text-text-secondary">Live checks from the application and database health endpoints.</p></div>
            <Link to="/admin/health" className="text-xs text-accent-purple">Details</Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex items-center gap-3 rounded-xl border border-border/70 bg-bg-base p-4">
              <Activity className="h-5 w-5 text-accent-teal" /><div><p className="text-xs text-text-secondary">API service</p><p className="text-sm font-semibold text-text-primary">{stats.isError ? 'Unavailable' : 'Reachable'}</p></div>
            </div>
            <div className="flex items-center gap-3 rounded-xl border border-border/70 bg-bg-base p-4">
              {db.data?.status === 'ok' ? <Database className="h-5 w-5 text-accent-teal" /> : <WifiOff className="h-5 w-5 text-accent-danger" />}
              <div><p className="text-xs text-text-secondary">MongoDB</p><p className="text-sm font-semibold text-text-primary">{db.isLoading ? 'Checking…' : db.data?.status === 'ok' ? 'Connected' : 'Unavailable'}</p></div>
            </div>
          </div>
          {db.data?.latency_ms != null && <p className="mt-3 text-xs text-text-secondary">Database response: {db.data.latency_ms} ms</p>}
        </section>

        <section className={cardClass}>
          <h2 className="text-sm font-semibold text-text-primary">User distribution</h2>
          <p className="mt-1 text-xs text-text-secondary">Accounts by assigned workspace role.</p>
          {users.isLoading ? <div className="skeleton mt-4 h-48 rounded-xl" /> : accounts.length ? (
            <div className="mt-3 flex items-center gap-2">
              <ResponsiveContainer width="58%" height={180}>
                <PieChart><Pie data={roleCounts} dataKey="value" nameKey="name" innerRadius={45} outerRadius={72} paddingAngle={3}>
                  {roleCounts.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                </Pie><Tooltip /></PieChart>
              </ResponsiveContainer>
              <div className="space-y-3">{roleCounts.map((entry) => <div key={entry.name} className="flex items-center gap-2 text-xs"><span className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} /><span className="text-text-secondary">{entry.name}</span><strong className="ml-auto text-text-primary">{entry.value}</strong></div>)}</div>
            </div>
          ) : <p className="py-12 text-center text-xs text-text-secondary">No user records found.</p>}
        </section>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <section className={cardClass}>
          <div className="mb-4 flex items-center justify-between"><div><h2 className="text-sm font-semibold text-text-primary">Recent governance activity</h2><p className="mt-1 text-xs text-text-secondary">Latest recorded administrative and operational actions.</p></div><Link to="/admin/audit" className="text-xs text-accent-purple">Audit trail</Link></div>
          <AuditRows items={logs.data?.items || []} loading={logs.isLoading} />
        </section>
        <section className={cardClass}>
          <h2 className="mb-4 text-sm font-semibold text-text-primary">Governance shortcuts</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <DataLink to="/admin/users" title="Manage users" detail="Create accounts and manage access." icon={Users} />
            <DataLink to="/admin/access" title="Role & access" detail="Review effective permission grants." icon={Shield} />
            <DataLink to="/admin/activity" title="Platform activity" detail="Review current platform signals." icon={Signal} />
            <DataLink to="/admin/settings" title="Platform settings" detail="Review application settings." icon={Database} />
          </div>
        </section>
      </div>
    </div>
  );
}

function AuditRows({ items, loading }) {
  if (loading) return <div className="space-y-2">{[1, 2, 3].map((item) => <div key={item} className="skeleton h-12 rounded-lg" />)}</div>;
  if (!items.length) return <p className="py-8 text-center text-xs text-text-secondary">No audit events have been recorded yet.</p>;
  return <div className="divide-y divide-border/60">{items.map((item) => <div key={item._id} className="flex items-center justify-between gap-4 py-3"><div className="min-w-0"><p className="truncate text-xs font-medium text-text-primary">{item.action}</p><p className="truncate text-[11px] text-text-secondary">{item.actor_email || 'System'} · {item.resource}</p></div><time className="shrink-0 text-[10px] text-text-secondary">{item.timestamp ? new Date(item.timestamp).toLocaleString() : ''}</time></div>)}</div>;
}

export function AdminAccess() {
  const permissionNames = [...new Set(Object.values(ROLE_PERMISSIONS).flat())].sort();
  return (
    <div>
      <PageHeading eyebrow="Governance" title="Role & access control" description="Effective permissions configured for the three NexCart roles." icon={Shield} />
      <div className="overflow-x-auto rounded-card border border-border bg-bg-card">
        <table className="w-full min-w-[640px] text-left">
          <thead><tr className="border-b border-border text-xs text-text-secondary"><th className="px-4 py-3">Permission</th>{roles.map((role) => <th key={role} className="px-4 py-3">{roleLabels[role]}</th>)}</tr></thead>
          <tbody>{permissionNames.map((permission) => <tr key={permission} className="border-b border-border/50 text-xs"><td className="px-4 py-3 font-mono text-text-primary">{permission}</td>{roles.map((role) => <td key={role} className="px-4 py-3">{ROLE_PERMISSIONS[role].includes(permission) ? <span className="text-accent-teal">Granted</span> : <span className="text-text-secondary/50">—</span>}</td>)}</tr>)}</tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-text-secondary">This view reports the frontend permission registry; API authorization remains enforced independently by the backend.</p>
    </div>
  );
}

export function AdminAudit() {
  const logs = useQuery({ queryKey: ['admin-audit-full'], queryFn: () => getAuditLogs(200) });
  return <div><PageHeading eyebrow="Governance" title="Audit trail" description="Recorded user, inventory, signal, campaign, and agent actions." icon={Activity} /><section className={cardClass}><AuditRows items={logs.data?.items || []} loading={logs.isLoading} /></section></div>;
}

export function AdminHealth() {
  const api = useQuery({ queryKey: ['system-api-health'], queryFn: getHealth, refetchInterval: 30000 });
  const db = useQuery({ queryKey: ['system-db-health'], queryFn: testDbConnection, refetchInterval: 30000 });
  const Item = ({ title, data, loading }) => <div className={`${cardClass} flex items-center gap-4`}>
    {data?.status === 'ok' || data?.environment ? <Wifi className="h-6 w-6 text-accent-teal" /> : <WifiOff className="h-6 w-6 text-accent-danger" />}
    <div><p className="text-sm font-semibold text-text-primary">{title}</p><p className="mt-1 text-xs text-text-secondary">{loading ? 'Checking…' : data?.status === 'ok' ? `Available${data.latency_ms ? ` · ${data.latency_ms} ms` : ''}` : data?.environment ? `Available · ${data.environment}` : data?.detail || 'Unavailable'}</p></div>
  </div>;
  return <div><PageHeading eyebrow="Platform monitoring" title="System health" description="Live service checks; no synthetic uptime metrics are shown." icon={Activity} /><div className="grid gap-4 md:grid-cols-2"><Item title="NexCart API" data={api.data} loading={api.isLoading} /><Item title="MongoDB" data={db.data} loading={db.isLoading} /></div><p className="mt-4 text-xs text-text-secondary">Checks refresh every 30 seconds. API version: {api.data?.version || '—'}.</p></div>;
}

export function AdminActivity() {
  const stats = useQuery({ queryKey: ['activity-stats'], queryFn: getStats });
  const signals = useQuery({ queryKey: ['activity-signals'], queryFn: () => getSignalHistory({ limit: 8 }) });
  const disruptions = useQuery({ queryKey: ['activity-disruptions'], queryFn: () => getDisruptions({ limit: 6 }) });
  return (
    <div className="space-y-6">
      <PageHeading eyebrow="Platform monitoring" title="Platform activity" description="Current operational activity drawn from live NexCart data." icon={Signal} />
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="SKUs monitored" value={stats.data?.total_skus ?? 0} icon={ShieldAlert} color="purple" loading={stats.isLoading} />
        <StatCard label="Signals · 24h" value={stats.data?.signal_events_24h ?? 0} icon={Radio} color="teal" loading={stats.isLoading} />
        <StatCard label="Disruptions listed" value={disruptions.data?.total ?? 0} icon={AlertTriangle} color="amber" loading={disruptions.isLoading} />
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        <section className={cardClass}><h2 className="mb-3 text-sm font-semibold text-text-primary">Recent signals</h2><ActivityList items={signals.data?.items || []} loading={signals.isLoading} type="signal" /></section>
        <section className={cardClass}><h2 className="mb-3 text-sm font-semibold text-text-primary">Recent disruptions</h2><ActivityList items={disruptions.data?.items || []} loading={disruptions.isLoading} type="disruption" /></section>
      </div>
    </div>
  );
}

function ActivityList({ items, loading, type }) {
  if (loading) return <p className="py-8 text-center text-xs text-text-secondary">Loading activity…</p>;
  if (!items.length) return <p className="py-8 text-center text-xs text-text-secondary">No recent {type}s available.</p>;
  return <div className="divide-y divide-border/60">{items.map((item, index) => <div key={item.signal_id || item.event_id || item._id || index} className="py-3"><p className="text-xs font-medium text-text-primary">{item.title || item.raw_payload?.title || item.event_id || 'Supply chain update'}</p><p className="mt-1 text-[11px] text-text-secondary">{item.source || 'unknown source'} · {item.processed_at || item.created_at ? new Date(item.processed_at || item.created_at).toLocaleString() : 'time unavailable'}</p></div>)}</div>;
}

export function ViewerOverview() {
  const stats = useQuery({ queryKey: ['viewer-overview-stats'], queryFn: getStats });
  const trend = useQuery({ queryKey: ['viewer-overview-risk-trend'], queryFn: getRiskTrend });
  const skus = useQuery({ queryKey: ['viewer-overview-skus'], queryFn: () => getSkus({ page: 1, limit: 6 }) });
  const disruptions = useQuery({ queryKey: ['viewer-overview-disruptions'], queryFn: () => getDisruptions({ limit: 5 }) });
  const signals = useQuery({ queryKey: ['viewer-overview-signals'], queryFn: () => getSignalHistory({ limit: 5 }) });
  const trendItems = trend.data?.trend || [];
  return (
    <div className="space-y-6">
      <PageHeading eyebrow="Supply-chain intelligence" title="Intelligence overview" description="Explore current exposure, emerging signals, and risk patterns. Read-only workspace." icon={Activity} />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="SKUs monitored" value={stats.data?.total_skus ?? 0} icon={ShieldAlert} color="purple" loading={stats.isLoading} />
        <StatCard label="SKUs at elevated risk" value={stats.data?.at_risk_count ?? 0} icon={AlertTriangle} color="amber" loading={stats.isLoading} />
        <StatCard label="Signals · 24h" value={stats.data?.signal_events_24h ?? 0} icon={Radio} color="teal" loading={stats.isLoading} />
        <StatCard label="Disruption records" value={disruptions.data?.total ?? 0} icon={Signal} color="purple" loading={disruptions.isLoading} />
      </div>
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(280px,0.8fr)]">
        <section className={cardClass}>
          <div className="mb-4 flex items-center justify-between"><div><h2 className="text-sm font-semibold text-text-primary">Risk trend</h2><p className="mt-1 text-xs text-text-secondary">Historical risk signal summary from NexCart analytics.</p></div><Link to="/intelligence/analytics" className="text-xs text-accent-purple">Explore analytics</Link></div>
          {trend.isLoading ? <div className="skeleton h-64 rounded-xl" /> : trendItems.length ? <div className="h-64 space-y-2 overflow-y-auto">{trendItems.slice(-10).map((point) => <div key={point.date} className="grid grid-cols-[90px_1fr_54px] items-center gap-3 text-xs"><span className="text-text-secondary">{point.date}</span><div className="h-2 rounded-full bg-bg-base"><div className="h-full rounded-full bg-accent-purple" style={{ width: `${Math.min(100, Math.max(0, point.avg_risk_score))}%` }} /></div><span className="text-right text-text-primary">{Math.round(point.avg_risk_score)}</span></div>)}</div> : <p className="py-16 text-center text-xs text-text-secondary">No risk trend data available.</p>}
        </section>
        <section className={cardClass}>
          <div className="mb-4 flex items-center justify-between"><div><h2 className="text-sm font-semibold text-text-primary">Highest-risk SKUs</h2><p className="mt-1 text-xs text-text-secondary">Current catalog sorted by risk.</p></div><Link to="/intelligence/risks" className="text-xs text-accent-purple">Risk explorer</Link></div>
          <div className="divide-y divide-border/60">{(skus.data?.items || []).map((sku) => <div key={sku.sku_id} className="flex items-center justify-between gap-3 py-3"><div className="min-w-0"><p className="truncate text-xs font-medium text-text-primary">{sku.name}</p><p className="text-[10px] text-text-secondary">{sku.sku_id} · stock {sku.current_stock}</p></div><RiskBadge level={sku.risk_level} score={sku.risk_score} /></div>)}{!skus.isLoading && !(skus.data?.items || []).length && <p className="py-8 text-center text-xs text-text-secondary">No SKU records available.</p>}</div>
        </section>
      </div>
      <div className="grid gap-5 xl:grid-cols-2">
        <section className={cardClass}><div className="mb-3 flex items-center justify-between"><h2 className="text-sm font-semibold text-text-primary">Disruption intelligence</h2><Link to="/intelligence/disruptions" className="text-xs text-accent-purple">Explore</Link></div><ActivityList items={disruptions.data?.items || []} loading={disruptions.isLoading} type="disruption" /></section>
        <section className={cardClass}><div className="mb-3 flex items-center justify-between"><h2 className="text-sm font-semibold text-text-primary">Signal intelligence</h2><Link to="/intelligence/signals" className="text-xs text-accent-purple">Explore</Link></div><ActivityList items={signals.data?.items || []} loading={signals.isLoading} type="signal" /></section>
      </div>
      <div className="grid gap-3 sm:grid-cols-3"><DataLink to="/intelligence/risks" title="Risk explorer" detail="Review SKU-level exposure." icon={ShieldAlert} /><DataLink to="/intelligence/disruptions" title="Disruption insights" detail="Analyze event severity and reach." icon={AlertTriangle} /><DataLink to="/intelligence/analytics" title="Analytics & trends" detail="Explore the historic risk series." icon={Activity} /></div>
    </div>
  );
}

export function DisruptionWorkspace({ readOnly = false }) {
  const { hasPermission } = useAuth();
  const events = useQuery({ queryKey: ['disruption-workspace', readOnly], queryFn: () => getDisruptions({ limit: 100 }) });
  const runAgent = async () => {
    await triggerDisruptionAgent();
    await events.refetch();
  };
  const items = events.data?.items || [];
  const severe = items.filter((event) => Number(event.severity) >= 4).length;
  const label = readOnly ? 'Disruption insights' : 'Disruption center';
  return (
    <div className="space-y-5">
      <PageHeading eyebrow={readOnly ? 'Intelligence workspace' : 'Operational response'} title={label} description={readOnly ? 'Read-only analysis of disruption severity, affected regions, and linked SKUs.' : 'Review disruption events and run AI-assisted disruption analysis.'} icon={AlertTriangle} />
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Events in view" value={events.data?.total ?? items.length} icon={Signal} color="purple" loading={events.isLoading} />
        <StatCard label="High / critical" value={severe} icon={AlertTriangle} color="amber" loading={events.isLoading} />
        <StatCard label="Affected SKU links" value={items.reduce((sum, event) => sum + (event.affected_sku_ids?.length || 0), 0)} icon={ShieldAlert} color="teal" loading={events.isLoading} />
      </div>
      {!readOnly && hasPermission('disruption_agent:run') && <button onClick={runAgent} className="rounded-xl bg-accent-purple px-4 py-2.5 text-xs font-semibold text-white">Run disruption analysis</button>}
      <section className={cardClass}>
        {events.isLoading ? <p className="py-10 text-center text-xs text-text-secondary">Loading disruption records…</p> : items.length ? (
          <div className="divide-y divide-border/60">{items.map((event) => <article key={event.event_id || event._id} className="grid gap-3 py-4 md:grid-cols-[minmax(0,1fr)_auto]">
            <div><div className="flex flex-wrap items-center gap-2"><h2 className="text-sm font-semibold text-text-primary">{event.title}</h2><span className="rounded-md bg-bg-base px-2 py-1 text-[10px] capitalize text-text-secondary">{event.source}</span></div><p className="mt-1 text-xs leading-relaxed text-text-secondary">{event.description || 'No description supplied.'}</p><p className="mt-2 text-[10px] text-text-secondary">{(event.affected_regions || []).join(', ') || 'No region listed'} · {(event.affected_sku_ids || []).length} linked SKU(s) · {event.created_at ? new Date(event.created_at).toLocaleString() : ''}</p></div>
            <div className="flex items-center gap-2"><span className="text-xs text-text-secondary">Severity {event.severity}/5</span></div>
          </article>)}</div>
        ) : <p className="py-12 text-center text-xs text-text-secondary">No disruption records found.</p>}
      </section>
    </div>
  );
}
