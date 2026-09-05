'use client';

import { ShoppingCart, FileText, Shield, Package, ArrowRight, TrendingUp } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCartStore } from '@/lib/store';
import { formatPaise } from '@/lib/utils';

export default function BuyerDashboard() {
  const router = useRouter();
  const { items, totalPaise } = useCartStore();
  const cartCount = items.size;

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Dashboard</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
          Your agentic commerce overview
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: 'Products Available', value: '2,400+', icon: Package, change: '+12%' },
          { label: 'Active Mandates', value: '3', icon: FileText, change: 'Valid' },
          { label: 'Auth Gate Pass Rate', value: '98.4%', icon: Shield, change: '16/16' },
        ].map((s) => (
          <div key={s.label} className="card p-5">
            <div className="flex items-center justify-between mb-3">
              <s.icon className="w-4.5 h-4.5" style={{ color: 'var(--text-muted)' }} />
              <span className="badge badge-success">{s.change}</span>
            </div>
            <p className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>{s.value}</p>
            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>{s.label}</p>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-sm font-medium mb-3" style={{ color: 'var(--text)' }}>Quick actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            { label: 'Search Products', desc: 'Find from verified merchants', href: '/buyer/search', icon: Package },
            { label: 'Create Mandate', desc: 'Set spending boundaries', href: '/buyer/mandate', icon: FileText },
            { label: 'View Cart', desc: 'Review and checkout', href: '/buyer/cart', icon: ShoppingCart },
          ].map((a) => (
            <button
              key={a.label}
              onClick={() => router.push(a.href)}
              className="card card-interactive text-left p-5 group"
            >
              <a.icon className="w-5 h-5 mb-3" style={{ color: 'var(--accent)' }} />
              <p className="text-sm font-medium mb-1" style={{ color: 'var(--text)' }}>{a.label}</p>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{a.desc}</p>
              <ArrowRight
                className="w-3.5 h-3.5 mt-3 transition-transform group-hover:translate-x-0.5"
                style={{ color: 'var(--text-muted)' }}
              />
            </button>
          ))}
        </div>
      </div>

      {/* Cart Banner */}
      {cartCount > 0 && (
        <div className="card p-4 flex items-center justify-between" style={{ borderLeft: '3px solid var(--accent)' }}>
          <div className="flex items-center gap-3">
            <ShoppingCart className="w-4.5 h-4.5" style={{ color: 'var(--accent)' }} />
            <span className="text-sm" style={{ color: 'var(--text)' }}>
              {cartCount} item{cartCount !== 1 ? 's' : ''} · {formatPaise(totalPaise)}
            </span>
          </div>
          <button onClick={() => router.push('/buyer/cart')} className="text-sm font-medium" style={{ color: 'var(--accent)' }}>
            View cart →
          </button>
        </div>
      )}

      {/* Process */}
      <div className="card p-6">
        <h2 className="text-sm font-medium mb-5" style={{ color: 'var(--text)' }}>How it works</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
          {[
            { step: '01', title: 'Set Mandate', desc: 'Define spending limits and categories' },
            { step: '02', title: 'AI Proposes', desc: 'Agent searches and negotiates' },
            { step: '03', title: 'Gate Verifies', desc: '16 predicates checked deterministically' },
            { step: '04', title: 'Evidence Proof', desc: 'SHA-256 hash chain proves authorization' },
          ].map((s) => (
            <div key={s.step}>
              <span className="text-xs font-mono font-semibold" style={{ color: 'var(--accent)' }}>{s.step}</span>
              <p className="text-sm font-medium mt-1.5" style={{ color: 'var(--text)' }}>{s.title}</p>
              <p className="text-xs mt-1 leading-relaxed" style={{ color: 'var(--text-muted)' }}>{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
