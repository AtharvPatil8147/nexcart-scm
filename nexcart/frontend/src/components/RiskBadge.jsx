/**
 * NexCart — RiskBadge Component
 * Colour-coded risk level pill. Critical level has pulsing red dot.
 */

import clsx from 'clsx';

const RISK_STYLES = {
  low: {
    bg: 'bg-emerald-900/30',
    text: 'text-accent-teal',
    border: 'border-emerald-700/50',
    dot: 'bg-accent-teal',
  },
  medium: {
    bg: 'bg-amber-900/30',
    text: 'text-accent-amber',
    border: 'border-amber-700/50',
    dot: 'bg-accent-amber',
  },
  high: {
    bg: 'bg-orange-900/30',
    text: 'text-orange-400',
    border: 'border-orange-700/50',
    dot: 'bg-orange-400',
  },
  critical: {
    bg: 'bg-red-900/30',
    text: 'text-accent-danger',
    border: 'border-red-700/50',
    dot: 'bg-accent-danger',
  },
};

export default function RiskBadge({ level = 'low' }) {
  const normalised = (level || 'low').toLowerCase();
  const styles = RISK_STYLES[normalised] || RISK_STYLES.low;

  return (
    <span className={clsx(
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full',
      'text-xs font-semibold border capitalize',
      styles.bg, styles.text, styles.border
    )}>
      <span className={clsx(
        'w-1.5 h-1.5 rounded-full shrink-0',
        styles.dot,
        normalised === 'critical' && 'animate-pulse'
      )} />
      {normalised}
    </span>
  );
}

// ✓ RiskBadge.jsx complete
