/**
 * NexCart — MongoDB Status Indicator
 * Polls GET /api/health/db every 30s. Green dot = connected, red dot = error.
 */

import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Database } from 'lucide-react';
import { testDbConnection } from '../api/client';
import clsx from 'clsx';

export default function MongoStatus() {
  const navigate = useNavigate();

  const { data, isError } = useQuery({
    queryKey: ['db-health'],
    queryFn: testDbConnection,
    refetchInterval: 30000,
    retry: 1,
  });

  const isOk = data?.status === 'ok' && !isError;
  const latency = data?.latency_ms;

  return (
    <button
      onClick={() => navigate('/settings')}
      className={clsx(
        'hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg',
        'text-xs font-medium transition-colors',
        'hover:bg-bg-hover border border-transparent',
        isOk
          ? 'text-accent-teal hover:border-accent-teal/20'
          : 'text-accent-danger hover:border-accent-danger/20'
      )}
    >
      {/* Animated Dot */}
      <span className={clsx(
        'w-2 h-2 rounded-full shrink-0',
        isOk
          ? 'bg-accent-teal animate-pulse-dot'
          : 'bg-accent-danger animate-pulse-dot'
      )} />

      {/* Label */}
      <Database className="w-3.5 h-3.5" />
      <span className="hidden lg:inline">
        {isOk ? `MongoDB (${latency}ms)` : 'DB disconnected'}
      </span>
    </button>
  );
}

// ✓ MongoStatus.jsx complete
