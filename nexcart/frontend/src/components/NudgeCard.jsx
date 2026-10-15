/**
 * NexCart — NudgeCard Component
 * Card for a single nudge campaign with status pill, channel icon, and offer preview.
 */

import { Bell, Mail, ArrowRight, DollarSign } from 'lucide-react';
import clsx from 'clsx';

const STATUS_STYLES = {
  pending: { bg: 'bg-gray-800/50', text: 'text-gray-400', border: 'border-gray-700/50', label: 'Pending' },
  sent: { bg: 'bg-blue-900/30', text: 'text-blue-400', border: 'border-blue-700/50', label: 'Sent' },
  opened: { bg: 'bg-amber-900/30', text: 'text-accent-amber', border: 'border-amber-700/50', label: 'Opened' },
  converted: { bg: 'bg-emerald-900/30', text: 'text-accent-teal', border: 'border-emerald-700/50', label: 'Converted' },
};

export default function NudgeCard({ campaign }) {
  if (!campaign) return null;

  const status = STATUS_STYLES[campaign.status] || STATUS_STYLES.pending;
  const ChannelIcon = campaign.channel === 'push' ? Bell : Mail;

  return (
    <div className={clsx(
      'bg-bg-card border border-border rounded-card p-4',
      'hover:border-accent-purple/30 transition-all duration-200',
      'hover:shadow-lg hover:shadow-accent-purple/5'
    )}>
      {/* Header: Customer + Channel + Status */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <ChannelIcon className="w-4 h-4 text-text-secondary shrink-0" />
          <span className="text-sm font-semibold text-text-primary truncate">
            {campaign.customer_id}
          </span>
        </div>
        <span className={clsx(
          'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border',
          status.bg, status.text, status.border
        )}>
          {status.label}
        </span>
      </div>

      {/* SKU Flow: At-Risk → Substitute */}
      <div className="flex items-center gap-2 mb-3 text-xs">
        <span className="px-2 py-1 rounded-md bg-accent-danger/10 text-accent-danger font-mono truncate max-w-[120px]">
          {campaign.sku_id}
        </span>
        <ArrowRight className="w-3.5 h-3.5 text-text-secondary shrink-0" />
        <span className="px-2 py-1 rounded-md bg-accent-teal/10 text-accent-teal font-mono truncate max-w-[120px]">
          {campaign.substitute_sku_id || '—'}
        </span>
      </div>

      {/* Offer Text Preview */}
      {campaign.offer_text && (
        <p className="text-xs text-text-secondary leading-relaxed line-clamp-2 mb-3">
          {campaign.offer_text}
        </p>
      )}

      {/* Footer: Revenue + Date */}
      <div className="flex items-center justify-between pt-2 border-t border-border/50">
        {campaign.status === 'converted' && campaign.revenue_recovered > 0 ? (
          <div className="flex items-center gap-1 text-accent-teal text-xs font-semibold">
            <DollarSign className="w-3.5 h-3.5" />
            {new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(campaign.revenue_recovered)}
          </div>
        ) : (
          <span className="text-xs text-text-secondary">
            {campaign.channel === 'push' ? 'Push' : 'Email'}
          </span>
        )}
        {campaign.sent_at && (
          <span className="text-xs text-text-secondary">
            {new Date(campaign.sent_at).toLocaleDateString()}
          </span>
        )}
      </div>
    </div>
  );
}

// ✓ NudgeCard.jsx complete
