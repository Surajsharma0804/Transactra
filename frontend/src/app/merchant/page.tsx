'use client';

import { useState, useEffect } from 'react';
import { IndianRupee, Package, ShoppingBag, Star, Shield, Loader2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { trustApi } from '@/lib/api';
import { formatPaise } from '@/lib/utils';

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
  const { user } = useAuthStore();
  const [trustScore, setTrustScore] = useState<number | null>(null);
  const [trustMetrics, setTrustMetrics] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrust = async () => {
      try {
        const data = await trustApi.get(user?.id || '');
        setTrustScore(data.trust_score);
        setTrustMetrics({
          fulfillment: data.fulfillment_rate,
          on_time: data.on_time_rate,
          disputes: data.dispute_rate,
          chain: data.chain_integrity_rate,
        });
      } catch {
        setTrustScore(null);
        setTrustMetrics(null);
      } finally {
        setLoading(false);
      }
    };
    fetchTrust();
  }, [user?.id]);

  const score = trustScore ?? 0;
  const hasTrust = trustScore !== null && trustScore > 0;

  const stats = [
    { label: 'Revenue', value: '—', icon: IndianRupee },
    { label: 'Products', value: '—', icon: Package },
    { label: 'Orders', value: '—', icon: ShoppingBag },
    { label: 'Trust Score', value: loading ? '···' : (hasTrust ? score.toFixed(2) : '—'), icon: Star },
  ];

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Dashboard</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
          {user?.name ? `Welcome, ${user.name}` : 'Revenue, orders, and trust overview'}
        </p>
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
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin" style={{ color: 'var(--text-muted)' }} />
            </div>
          ) : !hasTrust ? (
            <div className="text-center py-6">
              <Shield className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--border)' }} />
              <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No trust data yet</p>
              <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Complete orders to build trust</p>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-6 mb-4">
                <div className="relative w-20 h-20 shrink-0">
                  <svg className="w-20 h-20 -rotate-90" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="var(--border)" strokeWidth="5" />
                    <circle cx="50" cy="50" r="42" fill="none" stroke="var(--accent)" strokeWidth="5"
                      strokeDasharray={`${score * 264} ${264}`} strokeLinecap="round"
                      style={{ transition: 'stroke-dasharray 0.6s ease' }} />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-lg font-semibold" style={{ color: 'var(--text)' }}>{score.toFixed(2)}</span>
                  </div>
                </div>
                <div className="space-y-2 flex-1 text-sm">
                  {[
                    { l: 'Fulfillment', v: `${((trustMetrics?.fulfillment ?? 0) * 100).toFixed(0)}%` },
                    { l: 'On-time', v: `${((trustMetrics?.on_time ?? 0) * 100).toFixed(0)}%` },
                    { l: 'Disputes', v: `${((trustMetrics?.disputes ?? 0) * 100).toFixed(1)}%` },
                    { l: 'Chain integrity', v: `${((trustMetrics?.chain ?? 1) * 100).toFixed(0)}%` },
                  ].map(m => (
                    <div key={m.l} className="flex justify-between">
                      <span style={{ color: 'var(--text-muted)' }}>{m.l}</span>
                      <span style={{ color: 'var(--text)' }}>{m.v}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-1.5 text-xs" style={{ color: '#10b981' }}>
                <Shield className="w-3 h-3" /> Computed from verified evidence
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
