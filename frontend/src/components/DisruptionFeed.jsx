/**
 * NexCart — DisruptionFeed Component
 * Live feed of disruption events/signals with fade-in animation.
 */

import { Newspaper, Cloud, Ship, ShieldCheck } from 'lucide-react';
import clsx from 'clsx';

const SOURCE_ICONS = {
  news: Newspaper,
  weather: Cloud,
  shipping: Ship,
};

const SEVERITY_COLORS = [
  '', // 0 - unused
  'bg-emerald-900/40 text-accent-teal',
  'bg-amber-900/40 text-accent-amber',
  'bg-orange-900/40 text-orange-400',
  'bg-red-900/30 text-accent-danger',
  'bg-red-900/50 text-red-300',
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

function SkeletonItem() {
  return (
    <div className="flex items-start gap-3 p-3 rounded-xl">
      <div className="skeleton w-8 h-8 rounded-lg shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="skeleton h-3.5 w-3/4" />
        <div className="skeleton h-3 w-1/2" />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-text-secondary">
      <ShieldCheck className="w-10 h-10 mb-2 opacity-40" />
      <p className="text-sm font-medium">No disruptions detected</p>
      <p className="text-xs mt-1">All supply chains are running smoothly</p>
    </div>
  );
}

export default function DisruptionFeed({ events = [], loading = false, maxItems = 10 }) {
  if (loading) {
    return (
      <div className="space-y-1">
        {Array.from({ length: 4 }).map((_, i) => <SkeletonItem key={i} />)}
      </div>
    );
  }

  if (events.length === 0) return <EmptyState />;

  const displayed = events.slice(0, maxItems);

  return (
    <div className="space-y-1">
      {displayed.map((event, idx) => {
        const Icon = SOURCE_ICONS[event.source] || Newspaper;
        const severity = Math.min(5, Math.max(1, event.severity || 1));
        const sevColor = SEVERITY_COLORS[severity];
        const timestamp = event.created_at || event.published_at || event.processed_at;

        return (
          <div
            key={event.event_id || event.signal_id || idx}
            className={clsx(
              'flex items-start gap-3 p-3 rounded-xl',
              'hover:bg-bg-hover transition-colors duration-150',
              'animate-fade-in'
            )}
            style={{ animationDelay: `${idx * 50}ms` }}
          >
            {/* Source Icon */}
            <div className={clsx(
              'flex items-center justify-center w-8 h-8 rounded-lg shrink-0',
              sevColor
            )}>
              <Icon className="w-4 h-4" />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <p className="text-sm text-text-primary font-medium leading-snug truncate">
                {event.title}
              </p>
              <div className="flex items-center gap-2 mt-1">
                {/* Severity Dots */}
                <div className="flex gap-0.5">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <span
                      key={i}
                      className={clsx(
                        'w-1.5 h-1.5 rounded-full',
                        i < severity ? 'bg-accent-danger' : 'bg-border'
                      )}
                    />
                  ))}
                </div>
                <span className="text-xs text-text-secondary">
                  {timeAgo(timestamp)}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ✓ DisruptionFeed.jsx complete
