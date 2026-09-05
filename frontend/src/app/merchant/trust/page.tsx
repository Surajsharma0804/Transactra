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
        <h1 className="text-xl font-semibold text-white">Trust Score</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Computed from transaction evidence, not self-declared</p>
      </div>

      {/* Score */}
      <div className="border border-zinc-800 rounded-lg bg-zinc-900 p-6 text-center">
        <div className="relative w-28 h-28 mx-auto mb-4">
          <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="#27272a" strokeWidth="5" />
            <circle cx="50" cy="50" r="42" fill="none" stroke="#3b82f6" strokeWidth="5"
              strokeDasharray={`${score * 264} ${264}`} strokeLinecap="round" />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-semibold text-white">{score}</span>
            <span className="text-xs text-zinc-600">/ 1.0</span>
          </div>
        </div>
        <p className="text-sm text-zinc-500">
          40% fulfillment + 25% on-time + 20% (1−disputes) + 15% chain integrity
        </p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {metrics.map(m => (
          <div key={m.label} className="border border-zinc-800 rounded-lg bg-zinc-900 p-4">
            <div className="flex items-start justify-between mb-2">
              <m.icon className="w-4 h-4 text-zinc-500" />
              <span className="text-xl font-semibold text-white">{m.value}</span>
            </div>
            <p className="text-sm text-zinc-300">{m.label}</p>
            <p className="text-xs text-zinc-600 mt-0.5">{m.desc}</p>
          </div>
        ))}
      </div>

      <div className="border border-zinc-800 rounded-lg bg-zinc-900 p-4">
        <p className="text-sm text-zinc-400">
          <span className="text-zinc-300 font-medium">How is trust computed?</span>{' '}
          Every completed order, on-time delivery, and evidence chain verification contributes.
          The SHA-256 hash-linked chain proves every step was authorized and tamper-free.
          Trust is computed from evidence — merchants cannot self-declare their score.
        </p>
      </div>
    </div>
  );
}
