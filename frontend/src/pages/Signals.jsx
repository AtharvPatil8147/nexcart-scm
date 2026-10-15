/**
 * NexCart — Signals Page
 * Live signal intelligence feed with SSE, source filter tabs,
 * severity badges, and manual signal ingest form.
 */

import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Radio, Newspaper, Cloud, Anchor, Plus, Send,
  X, ChevronDown, MapPin, AlertTriangle,
} from 'lucide-react';
import { getSignalHistory, ingestSignal } from '../api/client';
import useSSE from '../hooks/useSSE';
import RiskBadge from '../components/RiskBadge';
import clsx from 'clsx';

const SOURCE_TABS = [
  { key: 'all', label: 'All', icon: Radio },
  { key: 'news', label: 'News', icon: Newspaper },
  { key: 'weather', label: 'Weather', icon: Cloud },
  { key: 'shipping', label: 'Shipping', icon: Anchor },
];

const SEVERITY_LABELS = ['', 'Low', 'Minor', 'Moderate', 'Major', 'Critical'];
const SEVERITY_COLORS = [
  '',
  'text-accent-teal',
  'text-accent-teal',
  'text-accent-amber',
  'text-orange-400',
  'text-accent-danger',
];

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function SignalCard({ signal, index }) {
  const [expanded, setExpanded] = useState(false);
  const payload = signal.raw_payload || {};
  const source = signal.source || payload.source || 'news';
  const Icon = source === 'weather' ? Cloud : source === 'shipping' ? Anchor : Newspaper;
  const title = signal.title || payload.title || payload.headline || `Disruption update from ${source}`;
  const description = signal.description || payload.description || '';
  const severity = Math.min(5, Math.max(1, signal.severity || payload.severity || 1));
  const affected_regions = (signal.affected_regions && signal.affected_regions.length > 0)
    ? signal.affected_regions
    : (payload.affected_regions || (payload.region ? [payload.region] : []));
  const affected_sku_ids = signal.affected_sku_ids || payload.affected_sku_ids || [];
  const timestamp = signal.created_at || signal.processed_at || signal.published_at || payload.published_at;

  return (
    <div
      className={clsx(
        'bg-bg-card border border-border rounded-card p-4',
        'hover:border-border/80 transition-all duration-200',
        'hover:shadow-lg hover:shadow-black/10',
        'animate-fade-in'
      )}
      style={{ animationDelay: `${index * 40}ms` }}
    >
      {/* Header Row */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-3 min-w-0">
          {/* Source Icon */}
          <div className={clsx(
            'flex items-center justify-center w-9 h-9 rounded-xl shrink-0',
            source === 'news' && 'bg-accent-purple/15 text-accent-purple',
            source === 'weather' && 'bg-blue-900/30 text-blue-400',
            source === 'shipping' && 'bg-accent-teal/15 text-accent-teal',
          )}>
            <Icon className="w-4.5 h-4.5" />
          </div>

          <div className="min-w-0">
            <p className={clsx(
              'text-sm font-medium text-text-primary leading-snug',
              !expanded && 'truncate'
            )}>
              {title}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <span className={clsx(
                'text-xs font-semibold capitalize',
                SEVERITY_COLORS[severity]
              )}>
                {SEVERITY_LABELS[severity]}
              </span>
              <span className="text-xs text-text-secondary">•</span>
              <span className="text-xs text-text-secondary capitalize">{source}</span>
              <span className="text-xs text-text-secondary">•</span>
              <span className="text-xs text-text-secondary">{timeAgo(timestamp)}</span>
            </div>
          </div>
        </div>

        {/* Severity Dots */}
        <div className="flex gap-0.5 shrink-0 mt-1">
          {Array.from({ length: 5 }).map((_, i) => (
            <span
              key={i}
              className={clsx(
                'w-2 h-2 rounded-full transition-colors',
                i < severity ? 'bg-accent-danger' : 'bg-border'
              )}
            />
          ))}
        </div>
      </div>

      {/* Description (expandable) */}
      {description && (
        <div className="mb-3">
          <p className={clsx(
            'text-xs text-text-secondary leading-relaxed',
            !expanded && 'line-clamp-2'
          )}>
            {description}
          </p>
          {description.length > 100 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-accent-purple hover:text-accent-purple/80 mt-1 flex items-center gap-0.5"
            >
              {expanded ? 'Show less' : 'Show more'}
              <ChevronDown className={clsx('w-3 h-3 transition-transform', expanded && 'rotate-180')} />
            </button>
          )}
        </div>
      )}

      {/* Affected Regions */}
      {affected_regions && affected_regions.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {affected_regions.map((region, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-bg-hover text-xs text-text-secondary border border-border/50"
            >
              <MapPin className="w-2.5 h-2.5" />
              {region}
            </span>
          ))}
        </div>
      )}

      {/* Affected SKUs */}
      {affected_sku_ids && affected_sku_ids.length > 0 && (
        <div className="flex flex-wrap gap-1.5 pt-2 border-t border-border/50">
          {affected_sku_ids.slice(0, 5).map((skuId, i) => (
            <span key={i} className="px-2 py-0.5 rounded-md bg-accent-danger/10 text-accent-danger text-[10px] font-mono">
              {skuId}
            </span>
          ))}
          {affected_sku_ids.length > 5 && (
            <span className="text-[10px] text-text-secondary self-center">
              +{affected_sku_ids.length - 5} more
            </span>
          )}
        </div>
      )}
    </div>
  );
}

function IngestForm({ onSubmit, loading, onClose }) {
  const [form, setForm] = useState({
    source: 'news',
    title: '',
    description: '',
    severity: 3,
    affected_regions: '',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      ...form,
      severity: parseInt(form.severity),
      affected_regions: form.affected_regions
        .split(',')
        .map(r => r.trim())
        .filter(Boolean),
    });
  };

  return (
    <div className="bg-bg-card border border-accent-purple/20 rounded-card p-5 animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
          <Plus className="w-4 h-4 text-accent-purple" />
          Ingest Manual Signal
        </h3>
        <button onClick={onClose} className="p-1 rounded-lg hover:bg-bg-hover transition-colors">
          <X className="w-4 h-4 text-text-secondary" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Source */}
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1.5">Source</label>
          <select
            value={form.source}
            onChange={(e) => setForm({ ...form, source: e.target.value })}
            className="w-full px-3 py-2.5 rounded-xl text-sm bg-bg-base border border-border text-text-primary focus:outline-none focus:border-accent-purple/50 appearance-none cursor-pointer"
          >
            <option value="news">News</option>
            <option value="weather">Weather</option>
            <option value="shipping">Shipping</option>
          </select>
        </div>

        {/* Severity */}
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1.5">
            Severity ({form.severity}/5)
          </label>
          <input
            type="range"
            min="1"
            max="5"
            value={form.severity}
            onChange={(e) => setForm({ ...form, severity: e.target.value })}
            className="w-full mt-2 accent-accent-purple"
          />
          <div className="flex justify-between text-[10px] text-text-secondary mt-1">
            <span>Low</span><span>Critical</span>
          </div>
        </div>

        {/* Title */}
        <div className="md:col-span-2">
          <label className="block text-xs font-medium text-text-secondary mb-1.5">Title</label>
          <input
            type="text"
            required
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            placeholder="e.g., Port strike at Shanghai delays semiconductor shipments"
            className="w-full px-3 py-2.5 rounded-xl text-sm bg-bg-base border border-border text-text-primary placeholder:text-text-secondary/40 focus:outline-none focus:border-accent-purple/50"
          />
        </div>

        {/* Description */}
        <div className="md:col-span-2">
          <label className="block text-xs font-medium text-text-secondary mb-1.5">Description</label>
          <textarea
            rows={3}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Detailed description of the disruption signal..."
            className="w-full px-3 py-2.5 rounded-xl text-sm bg-bg-base border border-border text-text-primary placeholder:text-text-secondary/40 focus:outline-none focus:border-accent-purple/50 resize-none"
          />
        </div>

        {/* Affected Regions */}
        <div className="md:col-span-2">
          <label className="block text-xs font-medium text-text-secondary mb-1.5">
            Affected Regions <span className="text-text-secondary/50">(comma separated)</span>
          </label>
          <input
            type="text"
            value={form.affected_regions}
            onChange={(e) => setForm({ ...form, affected_regions: e.target.value })}
            placeholder="e.g., Shanghai, East Asia, Pacific"
            className="w-full px-3 py-2.5 rounded-xl text-sm bg-bg-base border border-border text-text-primary placeholder:text-text-secondary/40 focus:outline-none focus:border-accent-purple/50"
          />
        </div>

        {/* Submit */}
        <div className="md:col-span-2 flex justify-end">
          <button
            type="submit"
            disabled={loading || !form.title}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-accent-purple text-white hover:bg-accent-purple/80 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
            {loading ? 'Submitting...' : 'Submit Signal'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default function Signals() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('all');
  const [showForm, setShowForm] = useState(false);
  const [liveSignals, setLiveSignals] = useState([]);
  const feedRef = useRef(null);

  // Fetch signal history
  const { data: historyData, isLoading } = useQuery({
    queryKey: ['signal-history'],
    queryFn: () => getSignalHistory({ limit: 50 }),
  });

  // SSE live feed
  const { data: sseData, connected: sseConnected } = useSSE('/api/signals/feed');

  // Append new SSE signals
  useEffect(() => {
    if (sseData && sseData.signal_id) {
      setLiveSignals(prev => {
        const exists = prev.some(s => s.signal_id === sseData.signal_id);
        if (exists) return prev;
        return [sseData, ...prev].slice(0, 20);
      });
    }
  }, [sseData]);

  // Manual signal ingest
  const ingestMutation = useMutation({
    mutationFn: ingestSignal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signal-history'] });
      setShowForm(false);
    },
  });

  // Combine live + history, filter by source
  const historicalSignals = historyData?.items || [];
  const allSignals = [...liveSignals, ...historicalSignals];

  // Deduplicate by signal_id
  const seen = new Set();
  const deduplicated = allSignals.filter(s => {
    const id = s.signal_id || s.event_id || JSON.stringify(s);
    if (seen.has(id)) return false;
    seen.add(id);
    return true;
  });

  const filtered = activeTab === 'all'
    ? deduplicated
    : deduplicated.filter(s => s.source === activeTab);

  return (
    <div className="space-y-5 animate-fade-in">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-xl font-bold text-text-primary flex items-center gap-2">
              <Radio className="w-5 h-5 text-accent-purple" />
              Signal Intelligence
            </h1>
            <p className="text-sm text-text-secondary mt-0.5">
              Real-time disruption signal monitoring
            </p>
          </div>
          {/* Live Indicator */}
          {sseConnected && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-accent-teal/10 border border-accent-teal/20">
              <span className="w-2 h-2 rounded-full bg-accent-teal animate-pulse-dot" />
              <span className="text-xs font-semibold text-accent-teal">LIVE</span>
            </span>
          )}
        </div>

        <button
          onClick={() => setShowForm(!showForm)}
          className={clsx(
            'flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold',
            'transition-all duration-200',
            showForm
              ? 'bg-bg-hover border border-border text-text-secondary'
              : 'bg-accent-purple text-white hover:bg-accent-purple/80'
          )}
        >
          {showForm ? <X className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
          {showForm ? 'Cancel' : 'Ingest Manual Signal'}
        </button>
      </div>

      {/* ── Ingest Form ── */}
      {showForm && (
        <IngestForm
          onSubmit={(data) => ingestMutation.mutate(data)}
          loading={ingestMutation.isPending}
          onClose={() => setShowForm(false)}
        />
      )}

      {/* ── Filter Tabs ── */}
      <div className="flex items-center gap-1 p-1 bg-bg-card border border-border rounded-xl w-fit">
        {SOURCE_TABS.map(({ key, label, icon: TabIcon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={clsx(
              'flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200',
              activeTab === key
                ? 'bg-accent-purple/15 text-accent-purple'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
            )}
          >
            <TabIcon className="w-3.5 h-3.5" />
            {label}
            {key !== 'all' && (
              <span className={clsx(
                'text-[10px] px-1.5 py-0.5 rounded-full',
                activeTab === key ? 'bg-accent-purple/20' : 'bg-border'
              )}>
                {deduplicated.filter(s => s.source === key).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Signal Feed ── */}
      <div ref={feedRef} className="space-y-3">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-bg-card border border-border rounded-card p-4 space-y-3">
              <div className="flex items-start gap-3">
                <div className="skeleton w-9 h-9 rounded-xl shrink-0" />
                <div className="flex-1 space-y-2">
                  <div className="skeleton h-4 w-3/4" />
                  <div className="skeleton h-3 w-1/2" />
                </div>
              </div>
              <div className="skeleton h-3 w-full" />
            </div>
          ))
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-text-secondary bg-bg-card border border-border rounded-card">
            <Radio className="w-12 h-12 mb-3 opacity-40" />
            <p className="text-sm font-medium">No signals found</p>
            <p className="text-xs mt-1">
              {activeTab !== 'all' ? 'Try switching to "All" tab' : 'Signals will appear here in real-time'}
            </p>
          </div>
        ) : (
          filtered.map((signal, idx) => (
            <SignalCard
              key={signal.signal_id || signal.event_id || idx}
              signal={signal}
              index={idx}
            />
          ))
        )}
      </div>
    </div>
  );
}

// ✓ Signals.jsx complete
