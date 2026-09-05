'use client';

import { motion } from 'framer-motion';
import { Shield, Star, TrendingUp, CheckCircle, AlertTriangle, BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function TrustPage() {
  const trustScore = 0.94;
  const metrics = [
    { label: 'Fulfillment Rate', value: 0.96, display: '96%', desc: 'Orders completed / total orders', icon: CheckCircle, color: 'emerald' },
    { label: 'On-Time Delivery', value: 0.92, display: '92%', desc: 'Delivered within commitment window', icon: TrendingUp, color: 'blue' },
    { label: 'Dispute Rate', value: 0.012, display: '1.2%', desc: 'Disputes filed / total orders (lower = better)', icon: AlertTriangle, color: 'amber' },
    { label: 'Chain Integrity', value: 1.0, display: '100%', desc: 'Evidence chains verified without tampering', icon: Shield, color: 'purple' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">Trust Score</h1>
        <p className="text-gray-400 mt-1">Your trust evidence — computed, not declared</p>
      </div>

      {/* Main Score */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-8 text-center"
      >
        <div className="relative w-40 h-40 mx-auto mb-6">
          <svg className="w-40 h-40 -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="#1f2937" strokeWidth="6" />
            <motion.circle
              cx="50" cy="50" r="42" fill="none"
              stroke="url(#scoreGrad)" strokeWidth="6"
              strokeLinecap="round"
              initial={{ strokeDasharray: '0 264' }}
              animate={{ strokeDasharray: `${trustScore * 264} ${264}` }}
              transition={{ duration: 1.5, ease: 'easeOut' }}
            />
            <defs>
              <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#8b5cf6" />
                <stop offset="50%" stopColor="#3b82f6" />
                <stop offset="100%" stopColor="#10b981" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.span
              className="text-4xl font-bold text-white"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              {trustScore}
            </motion.span>
            <span className="text-xs text-gray-500">out of 1.0</span>
          </div>
        </div>
        <div className="flex items-center justify-center gap-2 mb-2">
          <Star className="w-5 h-5 text-amber-400 fill-amber-400" />
          <span className="text-xl font-semibold text-emerald-400">Excellent</span>
        </div>
        <p className="text-gray-500 text-sm max-w-md mx-auto">
          Trust score formula: 40% fulfillment + 25% on-time + 20% (1−disputes) + 15% chain integrity
        </p>
      </motion.div>

      {/* Metric Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {metrics.map((m, idx) => (
          <motion.div
            key={m.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + idx * 0.1 }}
            className="glass-card p-5"
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`w-10 h-10 rounded-xl bg-${m.color}-500/10 flex items-center justify-center`}>
                <m.icon className={`w-5 h-5 text-${m.color}-400`} />
              </div>
              <span className={`text-2xl font-bold text-${m.color}-400`}>{m.display}</span>
            </div>
            <h3 className="text-white font-semibold text-sm">{m.label}</h3>
            <p className="text-gray-500 text-xs mt-1">{m.desc}</p>
            {/* Progress bar */}
            <div className="mt-3 h-1.5 rounded-full bg-gray-800 overflow-hidden">
              <motion.div
                className={`h-full rounded-full bg-${m.color}-500`}
                initial={{ width: 0 }}
                animate={{ width: `${(m.label === 'Dispute Rate' ? 1 - m.value : m.value) * 100}%` }}
                transition={{ duration: 1, delay: 0.5 + idx * 0.1 }}
              />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Explainer */}
      <div className="glass-card p-5 border-l-4 border-purple-500">
        <div className="flex items-center gap-2 mb-2">
          <BarChart3 className="w-4 h-4 text-purple-400" />
          <span className="text-purple-400 font-semibold text-sm">How is trust computed?</span>
        </div>
        <p className="text-gray-400 text-sm">
          Trust is <span className="text-white">computed from evidence</span>, not self-declared.
          Every completed order, on-time delivery, and evidence chain verification contributes to your score.
          The SHA-256 hash-linked evidence chain proves every step was authorized and tamper-free.
        </p>
      </div>
    </div>
  );
}
