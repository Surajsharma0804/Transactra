'use client';

import { IndianRupee, Package, ShoppingBag, Star, Shield } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { formatPaise } from '@/lib/utils';

const stats = [
  { label: 'Revenue', value: '₹2,45,000', icon: IndianRupee },
  { label: 'Products', value: '12', icon: Package },
  { label: 'Orders', value: '47', icon: ShoppingBag },
  { label: 'Trust Score', value: '0.94', icon: Star },
];

const recentOrders = [
  { id: 'ORD-A1B2', buyer: 'Rahul S.', amount: 150000, status: 'paid', time: '2h ago' },
  { id: 'ORD-C3D4', buyer: 'Priya M.', amount: 85000, status: 'pending', time: '4h ago' },
  { id: 'ORD-E5F6', buyer: 'Amit K.', amount: 320000, status: 'fulfilled', time: '1d ago' },
];

function statusBadge(s: string) {
  return s === 'paid' || s === 'fulfilled' ? 'badge-success' : s === 'pending' ? 'badge-warning' : 'badge-neutral';
}

export default function MerchantDashboard() {
  const router = useRouter();
  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Dashboard</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Revenue, orders, and trust overview</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(s => (
          <div key={s.label} className="card p-5">
            <s.icon className="w-4.5 h-4.5 mb-3" style={{ color: 'var(--text-muted)' }} />
            <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>{s.value}</p>
            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{s.label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium" style={{ color: 'var(--text)' }}>Recent Orders</h2>
            <button onClick={() => router.push('/merchant/orders')} className="text-xs" style={{ color: 'var(--accent)' }}>View all →</button>
          </div>
          <div className="space-y-3">
            {recentOrders.map(o => (
              <div key={o.id} className="flex items-center justify-between py-2" style={{ borderBottom: '1px solid var(--border)' }}>
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{o.id}</p>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{o.buyer} · {o.time}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{formatPaise(o.amount)}</p>
                  <span className={`badge ${statusBadge(o.status)}`}>{o.status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium" style={{ color: 'var(--text)' }}>Trust Score</h2>
            <button onClick={() => router.push('/merchant/trust')} className="text-xs" style={{ color: 'var(--accent)' }}>Details →</button>
          </div>
          <div className="flex items-center gap-6 mb-4">
            <div className="relative w-20 h-20 shrink-0">
              <svg className="w-20 h-20 -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="var(--border)" strokeWidth="5" />
                <circle cx="50" cy="50" r="42" fill="none" stroke="var(--accent)" strokeWidth="5" strokeDasharray={`${0.94 * 264} ${264}`} strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-semibold" style={{ color: 'var(--text)' }}>0.94</span>
              </div>
            </div>
            <div className="space-y-2 flex-1 text-sm">
              {[{ l: 'Fulfillment', v: '96%' }, { l: 'On-time', v: '92%' }, { l: 'Disputes', v: '1.2%' }, { l: 'Chain integrity', v: '100%' }].map(m => (
                <div key={m.l} className="flex justify-between">
                  <span style={{ color: 'var(--text-muted)' }}>{m.l}</span>
                  <span style={{ color: 'var(--text)' }}>{m.v}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-xs" style={{ color: '#10b981' }}>
            <Shield className="w-3 h-3" /> All evidence chains verified
          </div>
        </div>
      </div>
    </div>
  );
}
