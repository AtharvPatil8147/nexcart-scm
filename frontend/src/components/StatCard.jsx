/**
 * NexCart — StatCard Component
 * Reusable KPI metric card with count-up animation and skeleton loader.
 */

import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import clsx from 'clsx';

export default function StatCard({ label, value, unit, trend, icon: Icon, color = 'purple', loading = false }) {
  const [displayValue, setDisplayValue] = useState(0);

  // Count-up animation
  useEffect(() => {
    if (loading || typeof value !== 'number') {
      setDisplayValue(value);
      return;
    }

    const target = value;
    const duration = 800;
    const startTime = Date.now();
    const startVal = 0;

    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(Math.round(startVal + (target - startVal) * eased));

      if (progress >= 1) clearInterval(timer);
    }, 16);

    return () => clearInterval(timer);
  }, [value, loading]);

  const colorMap = {
    purple: { bg: 'bg-accent-purple/15', text: 'text-accent-purple', border: 'border-accent-purple/20' },
    teal: { bg: 'bg-accent-teal/15', text: 'text-accent-teal', border: 'border-accent-teal/20' },
    amber: { bg: 'bg-accent-amber/15', text: 'text-accent-amber', border: 'border-accent-amber/20' },
    danger: { bg: 'bg-accent-danger/15', text: 'text-accent-danger', border: 'border-accent-danger/20' },
  };

  const colors = colorMap[color] || colorMap.purple;

  if (loading) {
    return (
      <div className="bg-bg-card border border-border rounded-card p-5">
        <div className="skeleton h-4 w-24 mb-3" />
        <div className="skeleton h-8 w-32 mb-2" />
        <div className="skeleton h-3 w-16" />
      </div>
    );
  }

  const formattedValue = typeof displayValue === 'number'
    ? new Intl.NumberFormat().format(displayValue)
    : displayValue;

  return (
    <div className={clsx(
      'bg-bg-card border border-border rounded-card p-5',
      'hover:border-border/80 transition-all duration-200',
      'hover:shadow-lg hover:shadow-black/20'
    )}>
      <div className="flex items-start justify-between mb-3">
        <span className="text-sm text-text-secondary font-medium">{label}</span>
        {Icon && (
          <div className={clsx('flex items-center justify-center w-9 h-9 rounded-xl', colors.bg)}>
            <Icon className={clsx('w-4.5 h-4.5', colors.text)} />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-1.5 animate-count-up">
        <span className="text-2xl font-bold text-text-primary tabular-nums">
          {formattedValue}
        </span>
        {unit && <span className="text-sm text-text-secondary">{unit}</span>}
      </div>

      {trend !== undefined && trend !== null && (
        <div className={clsx(
          'flex items-center gap-1 mt-2 text-xs font-medium',
          trend >= 0 ? 'text-accent-teal' : 'text-accent-danger'
        )}>
          {trend >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
          <span>{Math.abs(trend)}% vs last week</span>
        </div>
      )}
    </div>
  );
}

// ✓ StatCard.jsx complete
