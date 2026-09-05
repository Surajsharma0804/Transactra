'use client';

import { ShoppingBag, CheckCircle } from 'lucide-react';
import { formatPaise, formatRelativeTime } from '@/lib/utils';

const orders = [
  { id: 'ORD-A1B2', buyer: 'Rahul Sharma', total_paise: 150000, status: 'paid', items: 2, created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: 'ORD-C3D4', buyer: 'Priya Mehta', total_paise: 85000, status: 'payment_pending', items: 1, created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: 'ORD-E5F6', buyer: 'Amit Kumar', total_paise: 320000, status: 'fulfilled', items: 3, created_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 'ORD-G7H8', buyer: 'Neha Singh', total_paise: 45000, status: 'created', items: 1, created_at: new Date(Date.now() - 172800000).toISOString() },
];

function statusBadge(s: string) {
  return s === 'paid' || s === 'fulfilled' ? 'badge-success' : s === 'payment_pending' ? 'badge-warning' : s === 'created' ? 'badge-info' : 'badge-neutral';
}

export default function MerchantOrdersPage() {
  return (
    <div className="max-w-4xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Orders</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Incoming customer orders</p>
      </div>
      <div className="space-y-2">
        {orders.map(o => (
          <div key={o.id} className="card flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              <ShoppingBag className="w-4.5 h-4.5 shrink-0" style={{ color: 'var(--text-muted)' }} />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>{o.id}</span>
                  <span className={`badge ${statusBadge(o.status)}`}>{o.status.replace('_', ' ')}</span>
                </div>
                <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                  {o.buyer} · {o.items} item{o.items !== 1 ? 's' : ''} · {formatRelativeTime(o.created_at)}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{formatPaise(o.total_paise)}</p>
              {o.status === 'paid' && (
                <button className="text-xs flex items-center gap-1 mt-0.5 ml-auto" style={{ color: '#10b981' }}>
                  <CheckCircle className="w-3 h-3" /> Fulfill
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
