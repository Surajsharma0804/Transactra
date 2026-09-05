'use client';

import { Package, Shield, Clock, Eye } from 'lucide-react';
import { formatPaise, formatRelativeTime } from '@/lib/utils';

const orders = [
  { order_id: 'a1b2c3d4', status: 'paid', total_paise: 150000, cart_hash: 'f4a2e83c91', created_at: new Date(Date.now() - 7200000).toISOString(), evidence: 5 },
  { order_id: 'e5f6g7h8', status: 'payment_pending', total_paise: 85000, cart_hash: '7b3d19a4f2', created_at: new Date(Date.now() - 14400000).toISOString(), evidence: 3 },
  { order_id: 'i9j0k1l2', status: 'fulfilled', total_paise: 320000, cart_hash: 'c9e1f58d72', created_at: new Date(Date.now() - 86400000).toISOString(), evidence: 8 },
];

function statusBadge(status: string) {
  const map: Record<string, string> = {
    paid: 'badge-success', fulfilled: 'badge-success', payment_pending: 'badge-warning', created: 'badge-info',
    failed: 'badge-danger', denied: 'badge-danger',
  };
  return map[status] || 'badge-neutral';
}

export default function OrdersPage() {
  return (
    <div className="max-w-4xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Orders</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Transaction history with evidence trails</p>
      </div>
      <div className="space-y-2">
        {orders.map(o => (
          <div key={o.order_id} className="card flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              <Package className="w-4.5 h-4.5 shrink-0" style={{ color: 'var(--text-muted)' }} />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium font-mono" style={{ color: 'var(--text)' }}>ORD-{o.order_id.slice(0, 8).toUpperCase()}</span>
                  <span className={`badge ${statusBadge(o.status)}`}>{o.status.replace('_', ' ')}</span>
                </div>
                <div className="flex items-center gap-2 mt-0.5 text-xs" style={{ color: 'var(--text-muted)' }}>
                  <Clock className="w-3 h-3" />
                  <span>{formatRelativeTime(o.created_at)}</span>
                  <span className="hash-display">{o.cart_hash}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{formatPaise(o.total_paise)}</p>
                <p className="text-xs flex items-center gap-1 justify-end" style={{ color: 'var(--text-muted)' }}>
                  <Shield className="w-3 h-3" /> {o.evidence} records
                </p>
              </div>
              <button className="btn-secondary" style={{ padding: '6px' }}>
                <Eye className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
