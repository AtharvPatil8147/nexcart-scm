/**
 * NexCart — Analytics & Insights Page
 * 30-day risk trend line chart, nudge conversion bar chart,
 * metric summary cards, and top disrupted SKUs table.
 */

import { useQuery } from '@tanstack/react-query';
import {
  BarChart2, TrendingUp, ShieldAlert, Target,
} from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { getRiskTrend, getNudgeConversion, getStats, getSkus } from '../api/client';
import StatCard from '../components/StatCard';
import RiskBadge from '../components/RiskBadge';
import clsx from 'clsx';

function ChartSkeleton({ height = 300 }) {
  return (
    <div className="space-y-3" style={{ height }}>
      <div className="skeleton h-full w-full rounded-lg" />
    </div>
  );
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-bg-card border border-border rounded-lg px-3 py-2 shadow-xl">
      <p className="text-xs font-medium text-text-secondary mb-1">{label}</p>
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          <span className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
          <span className="text-text-primary">{entry.name}: <strong>{entry.value}</strong></span>
        </div>
      ))}
    </div>
  );
}

export default function Analytics() {
  // ── Data Queries ──
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getStats,
  });

  const { data: riskTrendRaw, isLoading: trendLoading } = useQuery({
    queryKey: ['risk-trend'],
    queryFn: getRiskTrend,
  });

  const { data: conversionData, isLoading: conversionLoading } = useQuery({
    queryKey: ['nudge-conversion'],
    queryFn: getNudgeConversion,
  });

  const { data: topSkuData, isLoading: topSkuLoading } = useQuery({
    queryKey: ['top-disrupted-skus'],
    queryFn: () => getSkus({ limit: 5, page: 1 }),
  });

  // ── Process Risk Trend Data ──
  const riskTrend = Array.isArray(riskTrendRaw) ? riskTrendRaw : (riskTrendRaw?.trend || riskTrendRaw?.items || []);
  const trendChartData = riskTrend.map(item => ({
        date: item.date ? new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '',
        avg_risk: item.avg_risk_score || 0,
        at_risk: item.at_risk_count || 0,
      }));

  const conversionChartData = [
    { stage: 'Sent', count: conversionData?.sent || 0 },
    { stage: 'Opened', count: conversionData?.opened || 0 },
    { stage: 'Converted', count: conversionData?.converted || 0 },
  ];

  // Conversion rate
  const convRate = conversionData?.sent > 0
    ? ((conversionData?.converted / conversionData?.sent) * 100).toFixed(1)
    : '0';

  // Avg risk score from top SKUs
  const topSkus = topSkuData?.items || [];
  const avgRisk = topSkus.length > 0
    ? Math.round(topSkus.reduce((sum, s) => sum + (s.risk_score || 0), 0) / topSkus.length)
    : 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── Header + Date Range ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-accent-purple" />
            Analytics & Insights
          </h1>
          <p className="text-sm text-text-secondary mt-0.5">
            Track risk trends and campaign performance
          </p>
        </div>

      </div>

      {/* ── Row 1: Summary Metric Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label="Revenue Recovered (7d)"
          value={stats?.revenue_recovered_7d || 0}
          unit="USD"
          icon={TrendingUp}
          color="teal"
          loading={statsLoading}
        />
        <StatCard
          label="Avg Risk · Top 5 SKUs"
          value={avgRisk}
          icon={ShieldAlert}
          color="amber"
          loading={topSkuLoading}
        />
        <StatCard
          label="Nudge Conversion Rate"
          value={parseFloat(convRate)}
          unit="%"
          icon={Target}
          color="purple"
          loading={conversionLoading}
        />
      </div>

      {/* ── Row 2: 30-Day Risk Trend Line Chart ── */}
      <div className="bg-bg-card border border-border rounded-card p-5">
        <h2 className="text-sm font-semibold text-text-primary mb-4">
          Risk Score Trend (30 Days)
        </h2>
        {trendLoading ? (
          <ChartSkeleton height={320} />
        ) : trendChartData.length ? (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={trendChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E1E2E" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: '#6E6E8A' }}
                tickLine={false}
                axisLine={{ stroke: '#1E1E2E' }}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fontSize: 11, fill: '#6E6E8A' }}
                tickLine={false}
                axisLine={{ stroke: '#1E1E2E' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                verticalAlign="top"
                align="right"
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: '11px', color: '#6E6E8A' }}
              />
              <Line type="monotone" dataKey="avg_risk" name="Avg Risk Score" stroke="#7C6DDD" strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
              <Line type="monotone" dataKey="at_risk" name="At-Risk Count" stroke="#E24B4A" strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : <p className="py-16 text-center text-xs text-text-secondary">No risk trend data available.</p>}
      </div>

      {/* ── Row 3: Conversion Bar Chart + Top Disrupted SKUs ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Nudge Conversion Funnel */}
        <div className="bg-bg-card border border-border rounded-card p-5">
          <h2 className="text-sm font-semibold text-text-primary mb-4">
            Campaign Conversion Funnel
          </h2>
          {conversionLoading ? (
            <ChartSkeleton height={260} />
          ) : conversionData?.sent ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={conversionChartData} barGap={4}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E1E2E" />
                <XAxis
                  dataKey="stage"
                  tick={{ fontSize: 12, fill: '#6E6E8A' }}
                  tickLine={false}
                  axisLine={{ stroke: '#1E1E2E' }}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#6E6E8A' }}
                  tickLine={false}
                  axisLine={{ stroke: '#1E1E2E' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  verticalAlign="top"
                  align="right"
                  iconType="circle"
                  iconSize={8}
                  wrapperStyle={{ fontSize: '11px', color: '#6E6E8A' }}
                />
                <Bar dataKey="count" name="Campaigns" fill="#7C6DDD" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="py-16 text-center text-xs text-text-secondary">No campaign conversion data available.</p>}
        </div>

        {/* Top 5 Most Disrupted SKUs */}
        <div className="bg-bg-card border border-border rounded-card p-5">
          <h2 className="text-sm font-semibold text-text-primary mb-4">
            Top Disrupted SKUs
          </h2>
          {topSkuLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="skeleton h-8 w-full rounded-lg" />
                </div>
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left text-xs font-semibold text-text-secondary pb-3 uppercase tracking-wider">SKU</th>
                    <th className="text-right text-xs font-semibold text-text-secondary pb-3 uppercase tracking-wider">Score</th>
                    <th className="text-left text-xs font-semibold text-text-secondary pb-3 uppercase tracking-wider">Level</th>
                    <th className="text-left text-xs font-semibold text-text-secondary pb-3 uppercase tracking-wider hidden md:table-cell">Category</th>
                  </tr>
                </thead>
                <tbody>
                  {topSkus.map((sku, idx) => (
                    <tr
                      key={sku.sku_id}
                      className="border-b border-border/50 hover:bg-bg-hover transition-colors"
                    >
                      <td className="py-3 pr-4">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-text-secondary font-mono w-5">{idx + 1}.</span>
                          <span className="text-sm text-text-primary font-medium truncate max-w-[160px]">
                            {sku.name}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 text-right tabular-nums">
                        <span className={clsx(
                          'text-sm font-bold',
                          sku.risk_score >= 76 ? 'text-accent-danger'
                            : sku.risk_score >= 51 ? 'text-orange-400'
                            : sku.risk_score >= 26 ? 'text-accent-amber'
                            : 'text-accent-teal'
                        )}>
                          {sku.risk_score}
                        </span>
                      </td>
                      <td className="py-3"><RiskBadge level={sku.risk_level} /></td>
                      <td className="py-3 text-text-secondary text-xs hidden md:table-cell">{sku.category}</td>
                    </tr>
                  ))}
                  {topSkus.length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-8 text-center text-text-secondary text-xs">
                        No SKU data available
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ✓ Analytics.jsx complete
