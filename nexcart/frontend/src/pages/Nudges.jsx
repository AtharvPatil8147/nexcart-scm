/**
 * NexCart — Nudge Campaigns Page
 * Campaign management with conversion funnel, NudgeCard grid,
 * status/channel filters, and Run Nudge Agent trigger.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import {
  Bell, Play, Loader2, ArrowRight, Filter,
  Mail, Send, CheckCircle, Eye, Users,
} from 'lucide-react';
import {
  getNudges, getNudgeConversion, triggerNudgeAgent, updateNudgeStatus,
} from '../api/client';
import NudgeCard from '../components/NudgeCard';
import clsx from 'clsx';

const STATUS_TABS = ['all', 'pending', 'sent', 'opened', 'converted'];
const CHANNEL_FILTERS = ['all', 'push', 'email'];

function FunnelStep({ label, count, total, icon: Icon, color, isLast }) {
  const pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
  return (
    <>
      <div className={clsx(
        'flex-1 bg-bg-card border border-border rounded-xl p-4',
        'hover:border-border/80 transition-all duration-200'
      )}>
        <div className="flex items-center gap-2 mb-2">
          <div className={clsx('flex items-center justify-center w-7 h-7 rounded-lg', color)}>
            <Icon className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-medium text-text-secondary">{label}</span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-xl font-bold text-text-primary tabular-nums">
            {new Intl.NumberFormat().format(count)}
          </span>
          {total > 0 && label !== 'Sent' && (
            <span className="text-xs text-text-secondary">({pct}%)</span>
          )}
        </div>
      </div>
      {!isLast && (
        <ArrowRight className="w-4 h-4 text-text-secondary shrink-0 hidden sm:block" />
      )}
    </>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-bg-card border border-border rounded-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div className="skeleton h-4 w-32" />
        <div className="skeleton h-5 w-16 rounded-full" />
      </div>
      <div className="flex gap-2">
        <div className="skeleton h-5 w-20 rounded-md" />
        <div className="skeleton h-5 w-20 rounded-md" />
      </div>
      <div className="skeleton h-8 w-full" />
      <div className="flex justify-between">
        <div className="skeleton h-3 w-16" />
        <div className="skeleton h-3 w-20" />
      </div>
    </div>
  );
}

export default function Nudges() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState('all');
  const [channelFilter, setChannelFilter] = useState('all');
  const [page, setPage] = useState(1);
  const limit = 12;

  // Fetch nudges
  const params = {
    page,
    limit,
    ...(statusFilter !== 'all' && { status: statusFilter }),
    ...(channelFilter !== 'all' && { channel: channelFilter }),
  };

  const { data: nudgeData, isLoading } = useQuery({
    queryKey: ['nudges', params],
    queryFn: () => getNudges(params),
    placeholderData: keepPreviousData,
  });

  // Fetch conversion funnel
  const { data: funnelData } = useQuery({
    queryKey: ['nudge-conversion'],
    queryFn: getNudgeConversion,
  });

  // Run Nudge Agent
  const agentMutation = useMutation({
    mutationFn: () => triggerNudgeAgent([]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nudges'] });
      queryClient.invalidateQueries({ queryKey: ['nudge-conversion'] });
    },
  });

  // Mark as converted
  const convertMutation = useMutation({
    mutationFn: ({ id }) => updateNudgeStatus(id, { status: 'converted' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['nudges'] });
      queryClient.invalidateQueries({ queryKey: ['nudge-conversion'] });
    },
  });

  const nudges = nudgeData?.items || [];
  const total = nudgeData?.total || 0;
  const totalPages = Math.ceil(total / limit) || 1;

  const funnel = funnelData || { sent: 0, opened: 0, converted: 0 };

  return (
    <div className="space-y-5 animate-fade-in">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-text-primary flex items-center gap-2">
            <Bell className="w-5 h-5 text-accent-purple" />
            Nudge Campaigns
          </h1>
          <p className="text-sm text-text-secondary mt-0.5">
            Manage personalised customer restock nudges
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
          Run Nudge Agent
        </button>
      </div>

      {/* ── Conversion Funnel ── */}
      <div className="flex items-center gap-3">
        <FunnelStep
          label="Sent"
          count={funnel.sent}
          total={funnel.sent}
          icon={Send}
          color="bg-blue-900/30 text-blue-400"
        />
        <FunnelStep
          label="Opened"
          count={funnel.opened}
          total={funnel.sent}
          icon={Eye}
          color="bg-accent-amber/15 text-accent-amber"
        />
        <FunnelStep
          label="Converted"
          count={funnel.converted}
          total={funnel.sent}
          icon={CheckCircle}
          color="bg-accent-teal/15 text-accent-teal"
          isLast
        />
      </div>

      {/* ── Filters ── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        {/* Status Tabs */}
        <div className="flex items-center gap-1 p-1 bg-bg-card border border-border rounded-xl">
          {STATUS_TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => { setStatusFilter(tab); setPage(1); }}
              className={clsx(
                'px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200 capitalize',
                statusFilter === tab
                  ? 'bg-accent-purple/15 text-accent-purple'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
              )}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Channel Filter */}
        <div className="flex items-center gap-1 p-1 bg-bg-card border border-border rounded-xl">
          {CHANNEL_FILTERS.map((ch) => (
            <button
              key={ch}
              onClick={() => { setChannelFilter(ch); setPage(1); }}
              className={clsx(
                'flex items-center gap-1 px-3 py-2 rounded-lg text-xs font-medium transition-all duration-200 capitalize',
                channelFilter === ch
                  ? 'bg-accent-purple/15 text-accent-purple'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
              )}
            >
              {ch === 'push' && <Bell className="w-3 h-3" />}
              {ch === 'email' && <Mail className="w-3 h-3" />}
              {ch === 'all' && <Users className="w-3 h-3" />}
              {ch}
            </button>
          ))}
        </div>
      </div>

      {/* ── Campaign Grid ── */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : nudges.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 bg-bg-card border border-border rounded-card">
          <Bell className="w-14 h-14 mb-4 text-text-secondary opacity-30" />
          <p className="text-sm font-semibold text-text-primary mb-1">No campaigns yet</p>
          <p className="text-xs text-text-secondary mb-4">
            Run the nudge agent to generate personalised campaigns
          </p>
          <button
            onClick={() => agentMutation.mutate()}
            disabled={agentMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-accent-purple text-white hover:bg-accent-purple/80 transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5" />
            Run Nudge Agent
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {nudges.map((campaign, idx) => (
            <div key={campaign.campaign_id || idx} className="relative">
              <NudgeCard campaign={campaign} />
              {/* Mark as Converted button for opened campaigns */}
              {campaign.status === 'opened' && (
                <button
                  onClick={() => convertMutation.mutate({ id: campaign.campaign_id })}
                  disabled={convertMutation.isPending}
                  className={clsx(
                    'absolute bottom-3 right-3 flex items-center gap-1.5 px-3 py-1.5 rounded-lg',
                    'text-[11px] font-semibold bg-accent-teal/15 text-accent-teal border border-accent-teal/20',
                    'hover:bg-accent-teal/25 transition-all',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  <CheckCircle className="w-3 h-3" />
                  Mark Converted
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── Pagination ── */}
      {!isLoading && totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <p className="text-xs text-text-secondary">
            Showing {(page - 1) * limit + 1}–{Math.min(page * limit, total)} of {total}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-bg-card border border-border text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Previous
            </button>
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

// ✓ Nudges.jsx complete
