/**
 * NexCart — SKU Risk Radar Page
 * Full SKU table with search, filters, expandable rows with sparklines,
 * and "Run Disruption Agent" trigger button.
 */

import { useState, Fragment } from 'react';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import {
  ShieldAlert, Search, ChevronDown, ChevronUp, Play, Plus, X, Pencil,
  Loader2, Package, AlertTriangle, Filter,
} from 'lucide-react';
import { getSkus, getDisruptions, triggerDisruptionAgent, triggerNudgeAgent, createSku, updateSku } from '../api/client';
import RiskBadge from '../components/RiskBadge';
import clsx from 'clsx';
import { useAuth } from '../auth/AuthContext';

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

function ExpandedRow({ sku, onNudge, nudgeLoading, canRunNudge, canUpdate, onEdit }) {
  const { data: disruptions, isLoading: disruptionsLoading } = useQuery({
    queryKey: ['sku-disruptions', sku.sku_id],
    queryFn: () => getDisruptions({ sku_id: sku.sku_id, limit: 5 }),
  });

  return (
    <tr className="bg-bg-hover/50">
      <td colSpan={8} className="px-6 py-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in">
          {/* Sparkline */}
          <div>
            <h4 className="text-xs font-semibold text-text-secondary mb-2 uppercase tracking-wider">
              Current SKU Exposure
            </h4>
            <div className="bg-bg-card rounded-lg p-3 border border-border/50">
              <div className="mb-2 flex items-center justify-between text-xs"><span className="text-text-secondary">Current risk score</span><strong className="text-text-primary">{sku.risk_score}/100</strong></div>
              <div className="h-2 overflow-hidden rounded-full bg-bg-hover"><div className="h-full rounded-full bg-accent-purple" style={{ width: `${Math.min(100, Math.max(0, sku.risk_score || 0))}%` }} /></div>
              <p className="mt-3 text-[10px] text-text-secondary">No per-SKU historical risk series is currently available.</p>
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
              {canUpdate && <button onClick={() => onEdit(sku)} className="flex w-full items-center justify-center gap-2 rounded-xl border border-border px-3 py-2 text-xs font-semibold text-text-primary hover:border-accent-purple/40"><Pencil className="h-3.5 w-3.5" />Edit inventory details</button>}
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
              {canRunNudge && <button
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
              </button>}
            </div>
          </div>
        </div>
      </td>
    </tr>
  );
}

export default function SKURisk({ readOnly = false }) {
  const { hasPermission } = useAuth();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [riskLevel, setRiskLevel] = useState('all');
  const [category, setCategory] = useState('All');
  const [expandedId, setExpandedId] = useState(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [createError, setCreateError] = useState('');
  const [editingSku, setEditingSku] = useState(null);
  const [editError, setEditError] = useState('');
  const [newSku, setNewSku] = useState({
    sku_id: '', name: '', category: 'Electronics', supplier_country: '',
    current_stock: 0, reorder_point: 10,
  });

  const createMutation = useMutation({
    mutationFn: createSku,
    onSuccess: () => {
      setCreateOpen(false);
      setCreateError('');
      setNewSku({ sku_id: '', name: '', category: 'Electronics', supplier_country: '', current_stock: 0, reorder_point: 10 });
      queryClient.invalidateQueries({ queryKey: ['skus-list'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
    onError: (error) => setCreateError(error.response?.data?.detail || 'Unable to create SKU'),
  });
  const updateMutation = useMutation({
    mutationFn: ({ skuId, data }) => updateSku(skuId, data),
    onSuccess: () => {
      setEditingSku(null);
      setEditError('');
      queryClient.invalidateQueries({ queryKey: ['skus-list'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
    onError: (error) => setEditError(error.response?.data?.detail || 'Unable to update SKU'),
  });

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
            {readOnly ? 'Risk Explorer' : 'SKU Risk Radar'}
          </h1>
          <p className="text-sm text-text-secondary mt-0.5">
            {readOnly ? 'Explore product risk exposure and stock levels. Read-only access.' : 'Monitor inventory exposure and manage supply chain risk across all SKUs.'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
        {hasPermission('sku:create') && <button
          onClick={() => setCreateOpen(true)}
          className="flex items-center gap-2 rounded-xl border border-border bg-bg-card px-4 py-2.5 text-sm font-semibold text-text-primary hover:border-accent-purple/40"
        ><Plus className="h-4 w-4" />Add SKU</button>}
        {hasPermission('disruption_agent:run') && <button
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
        </button>}
        </div>
      </div>

      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <form onSubmit={(event) => {
            event.preventDefault();
            setCreateError('');
            createMutation.mutate({
              ...newSku,
              current_stock: Number(newSku.current_stock),
              reorder_point: Number(newSku.reorder_point),
            });
          }} className="w-full max-w-lg space-y-4 rounded-card border border-border bg-bg-card p-6 shadow-2xl">
            <div className="flex items-center justify-between"><div><h2 className="text-sm font-semibold text-text-primary">Add inventory SKU</h2><p className="mt-1 text-xs text-text-secondary">New products start at low risk until scored by the disruption agent.</p></div><button type="button" onClick={() => setCreateOpen(false)} aria-label="Close form"><X className="h-4 w-4 text-text-secondary" /></button></div>
            {createError && <p role="alert" className="rounded-lg bg-accent-danger/10 p-3 text-xs text-accent-danger">{createError}</p>}
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-xs text-text-secondary">SKU ID<input required value={newSku.sku_id} onChange={(e) => setNewSku({...newSku,sku_id:e.target.value})} className="mt-1 w-full rounded-xl border border-border bg-bg-base px-3 py-2 text-sm text-text-primary" /></label>
              <label className="text-xs text-text-secondary">Name<input required value={newSku.name} onChange={(e) => setNewSku({...newSku,name:e.target.value})} className="mt-1 w-full rounded-xl border border-border bg-bg-base px-3 py-2 text-sm text-text-primary" /></label>
              <label className="text-xs text-text-secondary">Category<select value={newSku.category} onChange={(e) => setNewSku({...newSku,category:e.target.value})} className="mt-1 w-full rounded-xl border border-border bg-bg-base px-3 py-2 text-sm text-text-primary">{CATEGORIES.filter((category) => category !== 'All').map((category) => <option key={category}>{category}</option>)}</select></label>
              <label className="text-xs text-text-secondary">Supplier country<input required value={newSku.supplier_country} onChange={(e) => setNewSku({...newSku,supplier_country:e.target.value})} className="mt-1 w-full rounded-xl border border-border bg-bg-base px-3 py-2 text-sm text-text-primary" /></label>
              <label className="text-xs text-text-secondary">Current stock<input type="number" min="0" required value={newSku.current_stock} onChange={(e) => setNewSku({...newSku,current_stock:e.target.value})} className="mt-1 w-full rounded-xl border border-border bg-bg-base px-3 py-2 text-sm text-text-primary" /></label>
              <label className="text-xs text-text-secondary">Reorder point<input type="number" min="0" required value={newSku.reorder_point} onChange={(e) => setNewSku({...newSku,reorder_point:e.target.value})} className="mt-1 w-full rounded-xl border border-border bg-bg-base px-3 py-2 text-sm text-text-primary" /></label>
            </div>
            <div className="flex justify-end gap-2"><button type="button" onClick={() => setCreateOpen(false)} className="rounded-xl px-4 py-2 text-xs text-text-secondary">Cancel</button><button type="submit" disabled={createMutation.isPending} className="rounded-xl bg-accent-purple px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">{createMutation.isPending ? 'Creating…' : 'Create SKU'}</button></div>
          </form>
        </div>
      )}
      {editingSku && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <form onSubmit={(event) => {
            event.preventDefault();
            setEditError('');
            const formData = new FormData(event.currentTarget);
            updateMutation.mutate({
              skuId: editingSku.sku_id,
              data: {
                name: formData.get('name'),
                supplier_country: formData.get('supplier_country'),
                current_stock: Number(formData.get('current_stock')),
                reorder_point: Number(formData.get('reorder_point')),
              },
            });
          }} className="w-full max-w-lg space-y-4 rounded-card border border-border bg-bg-card p-6 shadow-2xl">
            <div className="flex items-center justify-between"><div><h2 className="text-sm font-semibold text-text-primary">Update inventory</h2><p className="mt-1 text-xs text-text-secondary">{editingSku.sku_id}</p></div><button type="button" onClick={() => setEditingSku(null)} aria-label="Close form"><X className="h-4 w-4 text-text-secondary" /></button></div>
            {editError && <p role="alert" className="rounded-lg bg-accent-danger/10 p-3 text-xs text-accent-danger">{editError}</p>}
            <label className="block text-xs text-text-secondary">Product name<input name="name" required defaultValue={editingSku.name} className="mt-1 w-full rounded-xl border border-border bg-bg-base px-3 py-2 text-sm text-text-primary" /></label>
            <label className="block text-xs text-text-secondary">Supplier country<input name="supplier_country" required defaultValue={editingSku.supplier_country} className="mt-1 w-full rounded-xl border border-border bg-bg-base px-3 py-2 text-sm text-text-primary" /></label>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-xs text-text-secondary">Current stock<input name="current_stock" type="number" min="0" required defaultValue={editingSku.current_stock} className="mt-1 w-full rounded-xl border border-border bg-bg-base px-3 py-2 text-sm text-text-primary" /></label>
              <label className="text-xs text-text-secondary">Reorder point<input name="reorder_point" type="number" min="0" required defaultValue={editingSku.reorder_point} className="mt-1 w-full rounded-xl border border-border bg-bg-base px-3 py-2 text-sm text-text-primary" /></label>
            </div>
            <div className="flex justify-end gap-2"><button type="button" onClick={() => setEditingSku(null)} className="rounded-xl px-4 py-2 text-xs text-text-secondary">Cancel</button><button type="submit" disabled={updateMutation.isPending} className="rounded-xl bg-accent-purple px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">{updateMutation.isPending ? 'Saving…' : 'Save updates'}</button></div>
          </form>
        </div>
      )}

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
                        canRunNudge={hasPermission('nudge_agent:run')}
                        canUpdate={hasPermission('sku:update')}
                        onEdit={setEditingSku}
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
