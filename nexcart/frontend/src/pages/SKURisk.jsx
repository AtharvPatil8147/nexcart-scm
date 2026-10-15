/**
 * NexCart — SKU Risk Radar Page
 * Full SKU table with search, filters, expandable rows with sparklines,
 * and "Run Disruption Agent" trigger button.
 */

import { useState, Fragment } from 'react';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import {
  ShieldAlert, Search, ChevronDown, ChevronUp, Play,
  Loader2, Package, AlertTriangle, Filter,
} from 'lucide-react';
import {
  LineChart, Line, ResponsiveContainer, Tooltip as ReTooltip,
} from 'recharts';
import { getSkus, getDisruptions, triggerDisruptionAgent, triggerNudgeAgent } from '../api/client';
import RiskBadge from '../components/RiskBadge';
import clsx from 'clsx';

const CATEGORIES = ['All', 'Electronics', 'Apparel', 'Food', 'Pharma', 'Home Goods'];
const RISK_LEVELS = ['all', 'low', 'medium', 'high', 'critical'];
const PAGE_SIZE = 10;

const RISK_BAR_COLORS = {
  low: 'bg-accent-teal',
  medium: 'bg-accent-amber',
  high: 'bg-orange-400',
  critical: 'bg-accent-danger',
};

function SkeletonRow() {
  return (
    <tr className="border-b border-border/50">
      {Array.from({ length: 8 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="skeleton h-4 w-full rounded" />
        </td>
      ))}
    </tr>
  );
}

function SparklineSkeleton() {
  return (
    <div className="space-y-3">
      <div className="skeleton h-20 w-full rounded-lg" />
      <div className="skeleton h-4 w-3/4" />
      <div className="skeleton h-4 w-1/2" />
    </div>
  );
}

function ExpandedRow({ sku, onNudge, nudgeLoading }) {
  // Generate mock 7-day sparkline data from the SKU risk score
  const sparkData = Array.from({ length: 7 }).map((_, i) => ({
    day: `D${i + 1}`,
    score: Math.max(0, Math.min(100,
      sku.risk_score + Math.round((Math.random() - 0.5) * 20 - (6 - i) * 3)
    )),
  }));
  // Ensure last point is actual score
  sparkData[6].score = sku.risk_score;

  const { data: disruptions, isLoading: disruptionsLoading } = useQuery({
    queryKey: ['sku-disruptions', sku.sku_id],
    queryFn: () => getDisruptions({ sku_id: sku.sku_id, limit: 5 }),
  });

  const lineColor = sku.risk_score >= 76 ? '#E24B4A'
    : sku.risk_score >= 51 ? '#F97316'
    : sku.risk_score >= 26 ? '#EF9F27'
    : '#1D9E75';

  return (
    <tr className="bg-bg-hover/50">
      <td colSpan={8} className="px-6 py-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in">
          {/* Sparkline */}
          <div>
            <h4 className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wider">
              7-Day Risk Trend
            </h4>
            <div className="bg-bg-card rounded-lg p-3 border border-border/50">
              <ResponsiveContainer width="100%" height={80}>
                <LineChart data={sparkData}>
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke={lineColor}
                    strokeWidth={2}
                    dot={false}
                  />
                  <ReTooltip
                    contentStyle={{
                      background: '#12121A',
                      border: '1px solid #1E1E2E',
                      borderRadius: '8px',
                      fontSize: '12px',
                      color: '#E8E8F0',
                    }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Linked Disruptions */}
          <div>
            <h4 className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wider">
              Linked Disruptions
            </h4>
            {disruptionsLoading ? (
              <SparklineSkeleton />
            ) : (
              <div className="space-y-2">
                {(disruptions?.items || []).length > 0 ? (
                  (disruptions.items || []).slice(0, 4).map((d, idx) => (
                    <div key={d.event_id || idx} className="flex items-start gap-2 p-2 rounded-lg bg-bg-card border border-border/50">
                      <AlertTriangle className="w-3.5 h-3.5 text-accent-amber mt-0.5 shrink-0" />
                      <div className="min-w-0">
                        <p className="text-xs text-text-primary truncate">{d.title}</p>
                        <p className="text-[10px] text-text-secondary">
                          Severity {d.severity} • {d.source}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-text-secondary py-4 text-center">
                    No disruptions linked
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex flex-col gap-3">
            <h4 className="text-xs font-semibold text-text-secondary mb-1 uppercase tracking-wider">
              Actions
            </h4>
            <div className="bg-bg-card rounded-lg p-4 border border-border/50 space-y-3">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-text-secondary">Category</span>
                  <p className="text-text-primary font-medium">{sku.category}</p>
                </div>
                <div>
                  <span className="text-text-secondary">Supplier</span>
                  <p className="text-text-primary font-medium">{sku.supplier_country}</p>
                </div>
                <div>
                  <span className="text-text-secondary">Stock</span>
                  <p className="text-text-primary font-medium">{new Intl.NumberFormat().format(sku.current_stock)}</p>
                </div>
                <div>
                  <span className="text-text-secondary">Reorder Point</span>
                  <p className="text-text-primary font-medium">{new Intl.NumberFormat().format(sku.reorder_point || 0)}</p>
                </div>
              </div>
              <button
                onClick={() => onNudge(sku.sku_id)}
                disabled={nudgeLoading}
                className={clsx(
                  'w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl',
                  'text-xs font-semibold transition-all duration-200',
                  'bg-accent-purple text-white hover:bg-accent-purple/80',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}
              >
                {nudgeLoading ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5" />
                )}
                Generate Nudges for this SKU
              </button>
            </div>
          </div>
        </div>
      </td>
    </tr>
  );
}

export default function SKURisk() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [riskLevel, setRiskLevel] = useState('all');
  const [category, setCategory] = useState('All');
  const [expandedId, setExpandedId] = useState(null);

  // Fetch SKUs
  const params = {
    page,
    limit: PAGE_SIZE,
    ...(search && { search }),
    ...(riskLevel !== 'all' && { risk_level: riskLevel }),
    ...(category !== 'All' && { category }),
  };

  const { data: skuData, isLoading } = useQuery({
    queryKey: ['skus-list', params],
    queryFn: () => getSkus(params),
    placeholderData: keepPreviousData,
  });

  // Run Disruption Agent
  const agentMutation = useMutation({
    mutationFn: triggerDisruptionAgent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skus-list'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
  });

  // Run Nudge Agent
  const nudgeMutation = useMutation({
    mutationFn: (skuId) => triggerNudgeAgent([skuId]),
  });

  const skus = skuData?.items || [];
  const total = skuData?.total || 0;
  const totalPages = Math.ceil(total / PAGE_SIZE) || 1;

  // Stats counts
  const atRisk = skus.filter(s => s.risk_level === 'high' || s.risk_level === 'critical').length;
  const critical = skus.filter(s => s.risk_level === 'critical').length;

  return (
    <div className="space-y-5 animate-fade-in">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-accent-purple" />
            SKU Risk Radar
          </h1>
          <p className="text-sm text-text-secondary mt-0.5">
            Monitor and manage supply chain risk across all SKUs
          </p>
        </div>
        <button
          onClick={() => agentMutation.mutate()}
          disabled={agentMutation.isPending}
          className={clsx(
            'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold',
            'bg-accent-purple text-white transition-all duration-200',
            'hover:bg-accent-purple/80 hover:shadow-lg hover:shadow-accent-purple/20',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {agentMutation.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          Run Disruption Agent
        </button>
      </div>

      {/* ── Stats Bar ── */}
      <div className="flex items-center gap-6 px-4 py-3 bg-bg-card border border-border rounded-xl">
        <div className="flex items-center gap-2">
          <Package className="w-4 h-4 text-text-secondary" />
          <span className="text-sm text-text-secondary">Total:</span>
          <span className="text-sm font-bold text-text-primary">{total}</span>
        </div>
        <div className="w-px h-5 bg-border" />
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-accent-amber" />
          <span className="text-sm text-text-secondary">At Risk:</span>
          <span className="text-sm font-bold text-accent-amber">{atRisk}</span>
        </div>
        <div className="w-px h-5 bg-border" />
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-accent-danger" />
          <span className="text-sm text-text-secondary">Critical:</span>
          <span className="text-sm font-bold text-accent-danger">{critical}</span>
        </div>
      </div>

      {/* ── Filters ── */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
          <input
            type="text"
            placeholder="Search SKUs by name..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className={clsx(
              'w-full pl-10 pr-4 py-2.5 rounded-xl text-sm',
              'bg-bg-card border border-border text-text-primary',
              'placeholder:text-text-secondary/50',
              'focus:outline-none focus:border-accent-purple/50 focus:ring-1 focus:ring-accent-purple/20',
              'transition-all duration-200'
            )}
          />
        </div>

        {/* Risk Level Filter */}
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
          <select
            value={riskLevel}
            onChange={(e) => { setRiskLevel(e.target.value); setPage(1); }}
            className={clsx(
              'pl-10 pr-8 py-2.5 rounded-xl text-sm appearance-none',
              'bg-bg-card border border-border text-text-primary',
              'focus:outline-none focus:border-accent-purple/50',
              'transition-all duration-200 cursor-pointer'
            )}
          >
            {RISK_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level === 'all' ? 'All Risk Levels' : level.charAt(0).toUpperCase() + level.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Category Filter */}
        <select
          value={category}
          onChange={(e) => { setCategory(e.target.value); setPage(1); }}
          className={clsx(
            'px-4 py-2.5 rounded-xl text-sm appearance-none',
            'bg-bg-card border border-border text-text-primary',
            'focus:outline-none focus:border-accent-purple/50',
            'transition-all duration-200 cursor-pointer'
          )}
        >
          {CATEGORIES.map((cat) => (
            <option key={cat} value={cat}>{cat === 'All' ? 'All Categories' : cat}</option>
          ))}
        </select>
      </div>

      {/* ── Table ── */}
      <div className="overflow-x-auto rounded-card border border-border bg-bg-card">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-bg-card/80">
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider w-8" />
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">SKU ID</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Name</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider hidden md:table-cell">Category</th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">Stock</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Risk Score</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Level</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider hidden lg:table-cell">Country</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: PAGE_SIZE }).map((_, i) => <SkeletonRow key={i} />)
            ) : skus.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-16 text-center">
                  <div className="flex flex-col items-center text-text-secondary">
                    <Package className="w-12 h-12 mb-3 opacity-40" />
                    <p className="text-sm font-medium">No SKUs found</p>
                    <p className="text-xs mt-1">Try adjusting your filters</p>
                  </div>
                </td>
              </tr>
            ) : (
              skus.map((sku) => {
                const isExpanded = expandedId === sku.sku_id;
                const riskColor = RISK_BAR_COLORS[sku.risk_level] || RISK_BAR_COLORS.low;

                return (
                  <Fragment key={sku.sku_id}>
                    <tr
                      onClick={() => setExpandedId(isExpanded ? null : sku.sku_id)}
                      className={clsx(
                        'border-b border-border/50 cursor-pointer transition-colors duration-150',
                        isExpanded ? 'bg-bg-hover' : 'hover:bg-bg-hover'
                      )}
                    >
                      <td className="px-4 py-3">
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-text-secondary" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-text-secondary" />
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-accent-purple">{sku.sku_id}</td>
                      <td className="px-4 py-3 text-text-primary font-medium truncate max-w-[200px]">{sku.name}</td>
                      <td className="px-4 py-3 text-text-secondary hidden md:table-cell">{sku.category}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-text-primary">
                        {new Intl.NumberFormat().format(sku.current_stock)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 rounded-full bg-bg-hover overflow-hidden">
                            <div
                              className={clsx('h-full rounded-full transition-all duration-500', riskColor)}
                              style={{ width: `${sku.risk_score}%` }}
                            />
                          </div>
                          <span className="text-xs tabular-nums text-text-secondary w-7">{sku.risk_score}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3"><RiskBadge level={sku.risk_level} /></td>
                      <td className="px-4 py-3 text-text-secondary hidden lg:table-cell">{sku.supplier_country}</td>
                    </tr>
                    {isExpanded && (
                      <ExpandedRow
                        key={`${sku.sku_id}-expanded`}
                        sku={sku}
                        onNudge={(id) => nudgeMutation.mutate(id)}
                        nudgeLoading={nudgeMutation.isPending}
                      />
                    )}
                  </Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* ── Pagination ── */}
      {!isLoading && totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-text-secondary">
            Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, total)} of {total}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-bg-card border border-border text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
                const pageNum = i + 1;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={clsx(
                      'w-8 h-8 text-xs font-medium rounded-lg transition-colors',
                      page === pageNum
                        ? 'bg-accent-purple text-white'
                        : 'bg-bg-card border border-border text-text-secondary hover:text-text-primary hover:bg-bg-hover'
                    )}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-bg-card border border-border text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ✓ SKURisk.jsx complete
