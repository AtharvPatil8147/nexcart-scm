/**
 * NexCart — Dashboard Page
 * Main command centre with KPI cards, risk donut chart, at-risk SKU table,
 * recent nudge campaigns, and live signal feed via SSE.
 */

import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Package, ShieldAlert, Bell, TrendingUp, Radio,
  ArrowRight, RefreshCw,
} from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
} from 'recharts';
import { getStats, getDisruptions, getSkus, getNudges } from '../api/client';
import useSSE from '../hooks/useSSE';
import StatCard from '../components/StatCard';
import SKUTable from '../components/SKUTable';
import DisruptionFeed from '../components/DisruptionFeed';
import NudgeCard from '../components/NudgeCard';

const RISK_COLORS = {
  low: '#1D9E75',
  medium: '#EF9F27',
  high: '#F97316',
  critical: '#E24B4A',
};

const CURRENCY_FMT = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

function DonutSkeleton() {
  return (
    <div className="flex items-center justify-center h-[260px]">
      <div className="skeleton w-40 h-40 rounded-full" />
    </div>
  );
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const { name, value } = payload[0];
  return (
    <div className="bg-bg-card border border-border rounded-lg px-3 py-2 shadow-xl">
      <p className="text-xs text-text-secondary capitalize">{name}</p>
      <p className="text-sm font-bold text-text-primary">{value} SKUs</p>
    </div>
  );
}

function DonutLabel({ viewBox, total }) {
  const { cx, cy } = viewBox;
  return (
    <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle">
      <tspan x={cx} y={cy - 8} className="fill-text-primary text-2xl font-bold">
        {total}
      </tspan>
      <tspan x={cx} y={cy + 14} className="fill-text-secondary text-xs">
        Total SKUs
      </tspan>
    </text>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();

  // ── Data Queries ──
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getStats,
    refetchInterval: 60000, // Auto-refresh every 60s
  });

  const { data: skuData, isLoading: skusLoading } = useQuery({
    queryKey: ['skus-top-risk'],
    queryFn: () => getSkus({ limit: 5, page: 1 }),
    refetchInterval: 60000,
  });

  const { data: nudgeData, isLoading: nudgesLoading } = useQuery({
    queryKey: ['nudges-recent'],
    queryFn: () => getNudges({ limit: 5 }),
    refetchInterval: 60000,
  });

  const { data: disruptionData, isLoading: disruptionsLoading } = useQuery({
    queryKey: ['disruptions-recent'],
    queryFn: () => getDisruptions({ limit: 8 }),
    refetchInterval: 60000,
  });

  // ── SSE Live Signal Feed ──
  const { data: liveSignal, connected: sseConnected } = useSSE('/api/signals/feed');

  // ── Risk Distribution Data for Donut Chart ──
  const riskDist = stats?.risk_distribution || { low: 0, medium: 0, high: 0, critical: 0 };
  const donutData = Object.entries(riskDist).map(([name, value]) => ({
    name,
    value: value || 0,
  }));
  const totalSkus = donutData.reduce((sum, d) => sum + d.value, 0);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── Row 1: KPI Stat Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <StatCard
          label="Total SKUs"
          value={stats?.total_skus || 0}
          icon={Package}
          color="teal"
          loading={statsLoading}
        />
        <StatCard
          label="At Risk SKUs"
          value={stats?.at_risk_count || 0}
          icon={ShieldAlert}
          color="amber"
          loading={statsLoading}
        />
        <StatCard
          label="Nudges Sent Today"
          value={stats?.nudges_sent_today || 0}
          icon={Bell}
          color="purple"
          loading={statsLoading}
        />
        <StatCard
          label="Revenue Recovered (7d)"
          value={stats?.revenue_recovered_7d || 0}
          unit="USD"
          icon={TrendingUp}
          color="teal"
          loading={statsLoading}
        />
        <StatCard
          label="Signals (24h)"
          value={stats?.signal_events_24h || 0}
          icon={Radio}
          color="purple"
          loading={statsLoading}
        />
      </div>

      {/* ── Row 2: At-Risk SKUs + Risk Donut ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Top At-Risk SKUs (60%) */}
        <div className="lg:col-span-3 bg-bg-card border border-border rounded-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text-primary">
              Top At-Risk SKUs
            </h2>
            <button
              onClick={() => navigate('/skus')}
              className="flex items-center gap-1 text-xs text-accent-purple hover:text-accent-purple/80 transition-colors"
            >
              View all <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          <SKUTable
            skus={skuData?.items || []}
            loading={skusLoading}
            showPagination={false}
            onRowClick={(sku) => navigate(`/skus`)}
          />
        </div>

        {/* Risk Distribution Donut (40%) */}
        <div className="lg:col-span-2 bg-bg-card border border-border rounded-card p-5">
          <h2 className="text-sm font-semibold text-text-primary mb-4">
            Risk Distribution
          </h2>
          {statsLoading ? (
            <DonutSkeleton />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={donutData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                >
                  {donutData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={RISK_COLORS[entry.name] || '#6E6E8A'}
                    />
                  ))}
                  {/* Center label */}
                  <DonutLabel total={totalSkus} />
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  verticalAlign="bottom"
                  iconType="circle"
                  iconSize={8}
                  formatter={(value) => (
                    <span className="text-xs text-text-secondary capitalize ml-1">
                      {value} ({riskDist[value] || 0})
                    </span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ── Row 3: Recent Nudges + Live Signal Feed ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Recent Nudge Campaigns (60%) */}
        <div className="lg:col-span-3 bg-bg-card border border-border rounded-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text-primary">
              Recent Nudge Campaigns
            </h2>
            <button
              onClick={() => navigate('/nudges')}
              className="flex items-center gap-1 text-xs text-accent-purple hover:text-accent-purple/80 transition-colors"
            >
              View all <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          {nudgesLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-bg-hover rounded-card p-4 space-y-3">
                  <div className="skeleton h-4 w-3/4" />
                  <div className="skeleton h-3 w-1/2" />
                  <div className="skeleton h-3 w-full" />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {(nudgeData?.items || []).slice(0, 4).map((campaign, idx) => (
                <NudgeCard key={campaign.campaign_id || idx} campaign={campaign} />
              ))}
              {(!nudgeData?.items || nudgeData.items.length === 0) && (
                <div className="col-span-2 flex flex-col items-center justify-center py-8 text-text-secondary">
                  <Bell className="w-8 h-8 mb-2 opacity-40" />
                  <p className="text-sm">No nudge campaigns yet</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Live Signal Feed (40%) */}
        <div className="lg:col-span-2 bg-bg-card border border-border rounded-card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-text-primary">
                Live Signal Feed
              </h2>
              {sseConnected && (
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent-teal animate-pulse-dot" />
                  <span className="text-[10px] text-accent-teal font-medium">LIVE</span>
                </span>
              )}
            </div>
            <button
              onClick={() => navigate('/signals')}
              className="flex items-center gap-1 text-xs text-accent-purple hover:text-accent-purple/80 transition-colors"
            >
              View all <ArrowRight className="w-3 h-3" />
            </button>
          </div>
          <DisruptionFeed
            events={disruptionData?.items || []}
            loading={disruptionsLoading}
            maxItems={8}
          />
        </div>
      </div>
    </div>
  );
}

// ✓ Dashboard.jsx complete
