'use client';

import { Shield, CheckCircle, AlertTriangle, TrendingUp, Star } from 'lucide-react';

const metrics = [
  { label: 'Fulfillment Rate', value: '96%', desc: 'Completed / total orders', icon: CheckCircle },
  { label: 'On-Time Delivery', value: '92%', desc: 'Delivered within commitment', icon: TrendingUp },
  { label: 'Dispute Rate', value: '1.2%', desc: 'Lower is better', icon: AlertTriangle },
  { label: 'Chain Integrity', value: '100%', desc: 'Evidence chains verified', icon: Shield },
];

export default function TrustPage() {
  const score = 0.94;
  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Trust Score</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Computed from transaction evidence</p>
      </div>
      <div className="card p-8 text-center">
        <div className="relative w-32 h-32 mx-auto mb-4">
          <svg className="w-32 h-32 -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="var(--border)" strokeWidth="5" />
            <circle cx="50" cy="50" r="42" fill="none" stroke="var(--accent)" strokeWidth="5"
              strokeDasharray={`${score * 264} ${264}`} strokeLinecap="round" />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-semibold" style={{ color: 'var(--text)' }}>{score}</span>
            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>/ 1.0</span>
          </div>
        </div>
        <div className="flex items-center justify-center gap-1 mb-2">
          <Star className="w-4 h-4" style={{ color: '#f59e0b', fill: '#f59e0b' }} />
          <span className="text-sm font-medium" style={{ color: '#10b981' }}>Excellent</span>
        </div>
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
          40% fulfillment + 25% on-time + 20% (1−disputes) + 15% chain integrity
        </p>
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
      <div className="card p-5">
        <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
          <span className="font-medium" style={{ color: 'var(--text)' }}>How is trust computed?</span>{' '}
          Every completed order, on-time delivery, and evidence chain verification contributes.
          The SHA-256 hash-linked chain proves every step was authorized and tamper-free.
        </p>
      </div>
    </div>
  );
}
