'use client';

import { Package, Shield, Clock, Eye } from 'lucide-react';
import { formatPaise, formatRelativeTime, getStatusColor } from '@/lib/utils';

const orders = [
  { order_id: 'a1b2c3d4', status: 'paid', total_paise: 150000, cart_hash: 'f4a2e83c91', created_at: new Date(Date.now() - 7200000).toISOString(), evidence: 5 },
  { order_id: 'e5f6g7h8', status: 'payment_pending', total_paise: 85000, cart_hash: '7b3d19a4f2', created_at: new Date(Date.now() - 14400000).toISOString(), evidence: 3 },
  { order_id: 'i9j0k1l2', status: 'fulfilled', total_paise: 320000, cart_hash: 'c9e1f58d72', created_at: new Date(Date.now() - 86400000).toISOString(), evidence: 8 },
];

export default function OrdersPage() {
  return (
    <div className="max-w-4xl space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-white">Orders</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Transaction history with evidence trails</p>
      </div>

      <div className="space-y-2">
        {orders.map((o) => (
          <div key={o.order_id} className="flex items-center justify-between p-3.5 border border-zinc-800 rounded-lg bg-zinc-900">
            <div className="flex items-center gap-3">
              <Package className="w-4 h-4 text-zinc-500" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-white font-mono">ORD-{o.order_id.slice(0, 8).toUpperCase()}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${getStatusColor(o.status)}`}>
                    {o.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-0.5 text-xs text-zinc-600">
                  <Clock className="w-3 h-3" />
                  <span>{formatRelativeTime(o.created_at)}</span>
                  <span className="hash-display">{o.cart_hash}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm font-medium text-white">{formatPaise(o.total_paise)}</p>
                <p className="text-xs text-zinc-600 flex items-center gap-1 justify-end">
                  <Shield className="w-3 h-3" /> {o.evidence} records
                </p>
              </div>
              <button className="w-7 h-7 rounded-md bg-zinc-800 flex items-center justify-center text-zinc-500 hover:text-white transition-colors">
                <Eye className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
