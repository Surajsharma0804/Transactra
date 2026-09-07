'use client';

import { useState, useEffect } from 'react';
import { Shield, CheckCircle, AlertTriangle, TrendingUp, Star, RefreshCw, Loader2 } from 'lucide-react';
import { trustApi } from '@/lib/api';
import { useAuthStore } from '@/lib/store';

interface TrustData {
  trust_score: number;
  fulfillment_rate: number;
  on_time_rate: number;
  dispute_rate: number;
  chain_integrity_rate: number;
  total_orders: number;
  completed_orders: number;
  computed_at: string;
}

export default function TrustPage() {
  const { user } = useAuthStore();
  const [trust, setTrust] = useState<TrustData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTrust = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await trustApi.get(user?.id || '');
      setTrust(data);
    } catch (err: any) {
      // If no data yet, show empty state
      setTrust(null);
      if (err?.status !== 404) {
        setError('Unable to load trust data');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTrust(); }, [user?.id]);

  const score = trust?.trust_score ?? 0;
  const hasData = trust !== null && trust.total_orders > 0;

  const getScoreLabel = (s: number) => {
    if (s >= 0.9) return { label: 'Excellent', color: '#10b981' };
    if (s >= 0.7) return { label: 'Good', color: '#3b82f6' };
    if (s >= 0.5) return { label: 'Fair', color: '#f59e0b' };
    return { label: 'Needs improvement', color: '#ef4444' };
  };

  const scoreInfo = getScoreLabel(score);

  const metrics = hasData ? [
    { label: 'Fulfillment Rate', value: `${(trust!.fulfillment_rate * 100).toFixed(1)}%`, desc: `${trust!.completed_orders}/${trust!.total_orders} completed`, icon: CheckCircle },
    { label: 'On-Time Delivery', value: `${(trust!.on_time_rate * 100).toFixed(1)}%`, desc: 'Delivered within commitment', icon: TrendingUp },
    { label: 'Dispute Rate', value: `${(trust!.dispute_rate * 100).toFixed(1)}%`, desc: 'Lower is better', icon: AlertTriangle },
    { label: 'Chain Integrity', value: `${(trust!.chain_integrity_rate * 100).toFixed(1)}%`, desc: 'Evidence chains verified', icon: Shield },
  ] : [];

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Trust Score</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Computed from transaction evidence</p>
        </div>
        <button onClick={fetchTrust} disabled={loading} className="btn-secondary" style={{ padding: '6px 12px' }}>
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
        </button>
      </div>

      {loading ? (
        <div className="card p-12 text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>Computing trust score...</p>
        </div>
      ) : !hasData ? (
        <div className="card p-12 text-center">
          <Shield className="w-10 h-10 mx-auto mb-3" style={{ color: 'var(--border)' }} />
          <h2 className="text-lg font-medium mb-1" style={{ color: 'var(--text)' }}>No trust data yet</h2>
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
            Trust scores are computed from real transaction evidence.
            Complete orders to build your trust profile.
          </p>
        </div>
      ) : (
        <>
          <div className="card p-8 text-center">
            <div className="relative w-32 h-32 mx-auto mb-4">
              <svg className="w-32 h-32 -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="var(--border)" strokeWidth="5" />
                <circle cx="50" cy="50" r="42" fill="none" stroke={scoreInfo.color} strokeWidth="5"
                  strokeDasharray={`${score * 264} ${264}`} strokeLinecap="round"
                  style={{ transition: 'stroke-dasharray 0.6s ease' }} />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-semibold" style={{ color: 'var(--text)' }}>{score.toFixed(2)}</span>
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>/ 1.0</span>
              </div>
            </div>
            <div className="flex items-center justify-center gap-1 mb-2">
              <Star className="w-4 h-4" style={{ color: scoreInfo.color, fill: scoreInfo.color }} />
              <span className="text-sm font-medium" style={{ color: scoreInfo.color }}>{scoreInfo.label}</span>
            </div>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              40% fulfillment + 25% on-time + 20% (1−disputes) + 15% chain integrity
            </p>
            {trust!.computed_at && (
              <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                Last computed: {new Date(trust!.computed_at).toLocaleString()}
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {metrics.map(m => (
              <div key={m.label} className="card p-5">
                <div className="flex items-start justify-between mb-2">
                  <m.icon className="w-4.5 h-4.5" style={{ color: 'var(--text-muted)' }} />
                  <span className="text-xl font-semibold" style={{ color: 'var(--text)' }}>{m.value}</span>
                </div>
                <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>{m.label}</p>
                <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{m.desc}</p>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="card p-5">
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          <span className="font-medium" style={{ color: 'var(--text)' }}>How is trust computed?</span>{' '}
          Every completed order, on-time delivery, and evidence chain verification contributes.
          The SHA-256 hash-linked chain proves every step was authorized and tamper-free.
          Trust is never self-declared — it is computed from verifiable evidence.
        </p>
      </div>
    </div>
  );
}
