'use client';

import { motion } from 'framer-motion';
import { ShieldCheck, Store, ShoppingBag, Zap, Lock, Eye } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

export default function LandingPage() {
  const router = useRouter();
  const { setRole, isAuthenticated, role } = useAuthStore();

  // If already authenticated, redirect to dashboard
  if (isAuthenticated && role) {
    router.push(`/${role}`);
    return null;
  }

  const handleRoleSelect = (selectedRole: 'buyer' | 'merchant') => {
    setRole(selectedRole);
    router.push('/auth/login');
  };

  return (
    <div className="relative min-h-screen overflow-hidden gradient-mesh">
      {/* Animated background orbs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute -top-40 -left-40 w-80 h-80 rounded-full bg-blue-500/10 blur-[100px]"
          animate={{ x: [0, 50, 0], y: [0, 30, 0] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute -bottom-40 -right-40 w-80 h-80 rounded-full bg-purple-500/10 blur-[100px]"
          animate={{ x: [0, -50, 0], y: [0, -30, 0] }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 w-60 h-60 rounded-full bg-emerald-500/5 blur-[80px]"
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4">
        {/* Logo + Title */}
        <motion.div
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="text-center mb-16"
        >
          <motion.div
            className="inline-flex items-center gap-3 mb-6"
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
          >
            <div className="w-14 h-14 rounded-2xl gradient-primary flex items-center justify-center glow-blue">
              <ShieldCheck className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-5xl font-extrabold tracking-tight">
              <span className="bg-gradient-to-r from-blue-400 via-purple-400 to-emerald-400 bg-clip-text text-transparent">
                Transactra
              </span>
            </h1>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed"
          >
            The Trust Infrastructure for Agentic Commerce.
            <br />
            <span className="text-gray-500">
              AI proposes. Deterministic infrastructure verifies.
            </span>
          </motion.p>
        </motion.div>

        {/* Role Selection Cards */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl w-full mb-20"
        >
          {/* Buyer Card */}
          <motion.button
            onClick={() => handleRoleSelect('buyer')}
            className="glass-card glass-card-hover p-8 text-left group cursor-pointer"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="w-14 h-14 rounded-2xl bg-blue-500/10 flex items-center justify-center mb-6 group-hover:bg-blue-500/20 transition-colors">
              <ShoppingBag className="w-7 h-7 text-blue-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-3">I&apos;m a Buyer</h2>
            <p className="text-gray-400 leading-relaxed mb-4">
              Search products, set spending mandates, negotiate prices,
              and make verified payments with full evidence trails.
            </p>
            <div className="flex items-center gap-2 text-blue-400 text-sm font-medium">
              <span>Get started</span>
              <motion.span
                animate={{ x: [0, 4, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                →
              </motion.span>
            </div>
          </motion.button>

          {/* Merchant Card */}
          <motion.button
            onClick={() => handleRoleSelect('merchant')}
            className="glass-card glass-card-hover p-8 text-left group cursor-pointer"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="w-14 h-14 rounded-2xl bg-purple-500/10 flex items-center justify-center mb-6 group-hover:bg-purple-500/20 transition-colors">
              <Store className="w-7 h-7 text-purple-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-3">I&apos;m a Merchant</h2>
            <p className="text-gray-400 leading-relaxed mb-4">
              Manage products, track orders, build trust score,
              and grow revenue through verified agentic commerce.
            </p>
            <div className="flex items-center gap-2 text-purple-400 text-sm font-medium">
              <span>Get started</span>
              <motion.span
                animate={{ x: [0, 4, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                →
              </motion.span>
            </div>
          </motion.button>
        </motion.div>

        {/* Trust Features */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
          className="flex flex-wrap justify-center gap-8 text-sm text-gray-500"
        >
          <div className="flex items-center gap-2">
            <Lock className="w-4 h-4 text-blue-400" />
            <span>16-Predicate Authorization Gate</span>
          </div>
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-purple-400" />
            <span>SHA-256 Evidence Chain</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-emerald-400" />
            <span>Razorpay Verified Payments</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
