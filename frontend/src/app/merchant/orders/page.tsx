'use client';

import { ShoppingBag, CheckCircle, Clock } from 'lucide-react';
import { formatPaise, formatRelativeTime, getStatusColor } from '@/lib/utils';

const orders = [
  { id: 'ORD-A1B2', buyer: 'Rahul Sharma', total_paise: 150000, status: 'paid', items: 2, created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: 'ORD-C3D4', buyer: 'Priya Mehta', total_paise: 85000, status: 'payment_pending', items: 1, created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: 'ORD-E5F6', buyer: 'Amit Kumar', total_paise: 320000, status: 'fulfilled', items: 3, created_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 'ORD-G7H8', buyer: 'Neha Singh', total_paise: 45000, status: 'created', items: 1, created_at: new Date(Date.now() - 172800000).toISOString() },
];

export default function MerchantOrdersPage() {
  return (
    <div className="max-w-4xl space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-white">Orders</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Incoming customer orders</p>
      </div>

      <div className="space-y-2">
        {orders.map(o => (
          <div key={o.id} className="flex items-center justify-between p-3.5 border border-zinc-800 rounded-lg bg-zinc-900">
            <div className="flex items-center gap-3">
              <ShoppingBag className="w-4 h-4 text-zinc-500" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-white">{o.id}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${getStatusColor(o.status)}`}>{o.status.replace('_', ' ')}</span>
                </div>
                <p className="text-xs text-zinc-600 mt-0.5">{o.buyer} · {o.items} item{o.items !== 1 ? 's' : ''} · {formatRelativeTime(o.created_at)}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-white">{formatPaise(o.total_paise)}</p>
              {o.status === 'paid' && (
                <button className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 mt-0.5 ml-auto">
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
