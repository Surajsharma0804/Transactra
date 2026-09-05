'use client';

import { ShieldCheck, Store, ShoppingBag, ArrowRight } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

export default function LandingPage() {
  const router = useRouter();
  const { isAuthenticated, role, setRole } = useAuthStore();

  if (isAuthenticated && role) {
    router.push(`/${role}`);
    return null;
  }

  const handleRoleSelect = (selectedRole: 'buyer' | 'merchant') => {
    setRole(selectedRole);
    router.push('/auth/login');
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2.5 mb-4">
          <ShieldCheck className="w-8 h-8 text-blue-500" />
          <h1 className="text-3xl font-semibold tracking-tight text-white">
            Transactra
          </h1>
        </div>
        <p className="text-zinc-400 text-base max-w-md mx-auto">
          Trust infrastructure for agentic commerce.
          AI proposes, infrastructure verifies.
        </p>
      </div>

      {/* Role Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-xl w-full mb-12">
        <button
          onClick={() => handleRoleSelect('buyer')}
          className="text-left p-6 rounded-lg border border-zinc-800 bg-zinc-900 hover:border-zinc-600 hover:bg-zinc-800/80 transition-colors group"
        >
          <ShoppingBag className="w-5 h-5 text-zinc-400 mb-4 group-hover:text-white transition-colors" />
          <h2 className="text-base font-medium text-white mb-1">Buyer</h2>
          <p className="text-sm text-zinc-500 leading-relaxed">
            Search products, set mandates, negotiate prices, pay with verified authorization.
          </p>
          <span className="inline-flex items-center gap-1 text-xs text-zinc-500 mt-3 group-hover:text-zinc-300 transition-colors">
            Continue <ArrowRight className="w-3 h-3" />
          </span>
        </button>

        <button
          onClick={() => handleRoleSelect('merchant')}
          className="text-left p-6 rounded-lg border border-zinc-800 bg-zinc-900 hover:border-zinc-600 hover:bg-zinc-800/80 transition-colors group"
        >
          <Store className="w-5 h-5 text-zinc-400 mb-4 group-hover:text-white transition-colors" />
          <h2 className="text-base font-medium text-white mb-1">Merchant</h2>
          <p className="text-sm text-zinc-500 leading-relaxed">
            Manage products, track orders, build trust score, grow revenue.
          </p>
          <span className="inline-flex items-center gap-1 text-xs text-zinc-500 mt-3 group-hover:text-zinc-300 transition-colors">
            Continue <ArrowRight className="w-3 h-3" />
          </span>
        </button>
      </div>

      {/* Footer */}
      <p className="text-xs text-zinc-600">
        16-predicate authorization · SHA-256 evidence chain · Razorpay payments
      </p>
    </div>
  );
}
