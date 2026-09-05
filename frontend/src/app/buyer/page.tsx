'use client';

import { ShoppingCart, FileText, Shield, Package, ArrowRight } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCartStore } from '@/lib/store';
import { formatPaise } from '@/lib/utils';

export default function BuyerDashboard() {
  const router = useRouter();
  const { items, totalPaise } = useCartStore();
  const cartCount = items.size;

  const stats = [
    { label: 'Products Available', value: '2,400+', icon: Package },
    { label: 'Active Mandates', value: '3', icon: FileText },
    { label: 'Auth Gate Pass Rate', value: '98.4%', icon: Shield },
  ];

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Dashboard</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Overview of your commerce activity</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {stats.map((s) => (
          <div key={s.label} className="border border-zinc-800 rounded-lg bg-zinc-900 p-4">
            <div className="flex items-center gap-2 mb-3">
              <s.icon className="w-4 h-4 text-zinc-500" />
              <span className="text-xs text-zinc-500">{s.label}</span>
            </div>
            <p className="text-2xl font-semibold text-white">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {[
          { label: 'Search Products', href: '/buyer/search' },
          { label: 'Create Mandate', href: '/buyer/mandate' },
          { label: 'View Cart', href: '/buyer/cart' },
        ].map((a) => (
          <button
            key={a.label}
            onClick={() => router.push(a.href)}
            className="text-left p-4 border border-zinc-800 rounded-lg bg-zinc-900 hover:border-zinc-700 transition-colors group"
          >
            <span className="text-sm font-medium text-white">{a.label}</span>
            <ArrowRight className="w-3.5 h-3.5 text-zinc-600 mt-2 group-hover:text-zinc-400 transition-colors" />
          </button>
        ))}
      </div>

      {/* Cart Banner */}
      {cartCount > 0 && (
        <div className="flex items-center justify-between p-4 border border-zinc-800 rounded-lg bg-zinc-900">
          <div className="flex items-center gap-3">
            <ShoppingCart className="w-4 h-4 text-zinc-400" />
            <span className="text-sm text-zinc-300">
              {cartCount} item{cartCount !== 1 ? 's' : ''} · {formatPaise(totalPaise)}
            </span>
          </div>
          <button
            onClick={() => router.push('/buyer/cart')}
            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            View cart →
          </button>
        </div>
      )}

      {/* Process */}
      <div className="border border-zinc-800 rounded-lg bg-zinc-900 p-5">
        <h2 className="text-sm font-medium text-white mb-4">How it works</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { step: '1', title: 'Set Mandate', desc: 'Define spending limits' },
            { step: '2', title: 'AI Proposes', desc: 'Agent searches and negotiates' },
            { step: '3', title: 'Gate Verifies', desc: '16 predicates checked' },
            { step: '4', title: 'Evidence Proof', desc: 'SHA-256 audit trail' },
          ].map((s) => (
            <div key={s.step}>
              <span className="text-xs font-mono text-zinc-600">{s.step}.</span>
              <p className="text-sm font-medium text-zinc-300 mt-1">{s.title}</p>
              <p className="text-xs text-zinc-600 mt-0.5">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
