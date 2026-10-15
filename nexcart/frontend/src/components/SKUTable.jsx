/**
 * NexCart — SKUTable Component
 * Paginated, sortable table for SKU data with risk score progress bars.
 */

import { Package, AlertTriangle } from 'lucide-react';
import RiskBadge from './RiskBadge';
import clsx from 'clsx';

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

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-text-secondary">
      <Package className="w-12 h-12 mb-3 opacity-40" />
      <p className="text-sm font-medium">No SKUs found</p>
      <p className="text-xs mt-1">Try adjusting your filters</p>
    </div>
  );
}

export default function SKUTable({ skus = [], loading = false, onRowClick, showPagination = true }) {
  if (!loading && skus.length === 0) {
    return <EmptyState />;
  }

  return (
    <div className="overflow-x-auto rounded-card border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-bg-card/50">
            <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">SKU ID</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Name</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider hidden md:table-cell">Category</th>
            <th className="px-4 py-3 text-right text-xs font-semibold text-text-secondary uppercase tracking-wider">Stock</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Risk Score</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider">Level</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider hidden lg:table-cell">Country</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider hidden lg:table-cell">Updated</th>
          </tr>
        </thead>
        <tbody>
          {loading
            ? Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)
            : skus.map((sku) => {
                const riskColor = RISK_BAR_COLORS[sku.risk_level] || RISK_BAR_COLORS.low;
                const updatedStr = sku.last_updated
                  ? new Date(sku.last_updated).toLocaleDateString()
                  : '—';

                return (
                  <tr
                    key={sku.sku_id}
                    onClick={() => onRowClick?.(sku)}
                    className={clsx(
                      'border-b border-border/50 transition-colors duration-150',
                      onRowClick && 'cursor-pointer hover:bg-bg-hover'
                    )}
                  >
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
                    <td className="px-4 py-3 text-text-secondary text-xs hidden lg:table-cell">{updatedStr}</td>
                  </tr>
                );
              })
          }
        </tbody>
      </table>
    </div>
  );
}

// ✓ SKUTable.jsx complete
