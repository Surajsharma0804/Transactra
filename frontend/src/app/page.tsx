'use client';

import { ShieldCheck, Store, ShoppingBag, ArrowRight, Zap, Lock, Eye, Sun, Moon } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuthStore, useUIStore } from '@/lib/store';

export default function LandingPage() {
  const router = useRouter();
  const { isAuthenticated, role, setRole } = useAuthStore();
  const { theme, toggleTheme } = useUIStore();

  if (isAuthenticated && role) {
    router.push(`/${role}`);
    return null;
  }

  const handleRoleSelect = (selectedRole: 'buyer' | 'merchant') => {
    setRole(selectedRole);
    router.push('/auth/login');
  };

  return (
    <div className="min-h-screen hero-gradient">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-4 max-w-5xl mx-auto">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5" style={{ color: 'var(--accent)' }} />
          <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Transactra</span>
        </div>
        <button
          onClick={toggleTheme}
          className="btn-secondary"
          style={{ padding: '6px 10px' }}
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </header>

      {/* Hero */}
      <main className="flex flex-col items-center pt-20 pb-16 px-4">
        <div className="text-center mb-14 max-w-lg">
          <div
            className="badge badge-info mb-4 mx-auto"
            style={{ fontSize: '12px', padding: '4px 12px' }}
          >
            <Zap className="w-3 h-3 mr-1" /> Built for agentic commerce
          </div>

          <h1 className="text-4xl font-bold tracking-tight mb-4" style={{ color: 'var(--text)', lineHeight: '1.15' }}>
            Trust infrastructure
            <br />
            <span style={{ color: 'var(--accent)' }}>for AI commerce</span>
          </h1>

          <p className="text-base leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            AI proposes transactions. Deterministic infrastructure verifies
            every step with bounded authority, auditable evidence, and real payments.
          </p>
        </div>

        {/* Role Selection Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 max-w-xl w-full mb-16">
          <button
            onClick={() => handleRoleSelect('buyer')}
            className="card card-interactive text-left p-6 group"
          >
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center mb-5"
              style={{ background: 'var(--accent-subtle)' }}
            >
              <ShoppingBag className="w-5 h-5" style={{ color: 'var(--accent)' }} />
            </div>
            <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>Buyer</h2>
            <p className="text-sm leading-relaxed mb-4" style={{ color: 'var(--text-secondary)' }}>
              Search products, set spending mandates, negotiate prices, and pay with verified authorization.
            </p>
            <span className="inline-flex items-center gap-1 text-sm font-medium" style={{ color: 'var(--accent)' }}>
              Get started <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
            </span>
          </button>

          <button
            onClick={() => handleRoleSelect('merchant')}
            className="card card-interactive text-left p-6 group"
          >
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center mb-5"
              style={{ background: 'rgba(139, 92, 246, 0.08)' }}
            >
              <Store className="w-5 h-5" style={{ color: '#8b5cf6' }} />
            </div>
            <h2 className="text-lg font-semibold mb-2" style={{ color: 'var(--text)' }}>Merchant</h2>
            <p className="text-sm leading-relaxed mb-4" style={{ color: 'var(--text-secondary)' }}>
              Manage products, track orders, build trust score, and grow revenue through verified commerce.
            </p>
            <span className="inline-flex items-center gap-1 text-sm font-medium" style={{ color: '#8b5cf6' }}>
              Get started <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
            </span>
          </button>
        </div>

        {/* Trust features */}
        <div className="flex flex-wrap justify-center gap-6 text-xs" style={{ color: 'var(--text-muted)' }}>
          <div className="flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5" />
            <span>16-predicate authorization</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Eye className="w-3.5 h-3.5" />
            <span>SHA-256 evidence chain</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5" />
            <span>Razorpay verified payments</span>
          </div>
        </div>
      </main>
    </div>
  );
}
