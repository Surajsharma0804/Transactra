'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  ShoppingCart, FileText, Shield, Package,
  ArrowUpRight, TrendingUp, Zap,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCartStore } from '@/lib/store';
import { formatPaise } from '@/lib/utils';

const stats = [
  {
    label: 'Products Found',
    value: '2,400+',
    change: '+12%',
    icon: Package,
    color: 'blue',
  },
  {
    label: 'Active Mandates',
    value: '3',
    change: 'All valid',
    icon: FileText,
    color: 'purple',
  },
  {
    label: 'Authorization Rate',
    value: '98.4%',
    change: '16/16 pass',
    icon: Shield,
    color: 'emerald',
  },
  {
    label: 'Savings via AI',
    value: '₹12,450',
    change: '-15% avg',
    icon: TrendingUp,
    color: 'amber',
  },
];

const quickActions = [
  {
    label: 'Search Products',
    desc: 'Find from verified merchants',
    href: '/buyer/search',
    icon: Zap,
    gradient: 'from-blue-600 to-blue-400',
  },
  {
    label: 'Create Mandate',
    desc: 'Set spending boundaries',
    href: '/buyer/mandate',
    icon: FileText,
    gradient: 'from-purple-600 to-purple-400',
  },
  {
    label: 'View Cart',
    desc: 'Review & checkout',
    href: '/buyer/cart',
    icon: ShoppingCart,
    gradient: 'from-emerald-600 to-emerald-400',
  },
];

const stagger = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

export default function BuyerDashboard() {
  const router = useRouter();
  const { items, totalPaise } = useCartStore();
  const cartCount = items.size;

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">
          Your agentic commerce command center
        </p>
      </div>

      {/* Stats Grid */}
      <motion.div
        variants={stagger}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {stats.map((stat) => (
          <motion.div
            key={stat.label}
            variants={fadeUp}
            className="glass-card p-5 group"
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`w-10 h-10 rounded-xl bg-${stat.color}-500/10 flex items-center justify-center`}>
                <stat.icon className={`w-5 h-5 text-${stat.color}-400`} />
              </div>
              <span className={`text-xs font-medium text-${stat.color}-400 bg-${stat.color}-500/10 px-2 py-1 rounded-lg`}>
                {stat.change}
              </span>
            </div>
            <p className="text-2xl font-bold text-white">{stat.value}</p>
            <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
          </motion.div>
        ))}
      </motion.div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
        <motion.div
          variants={stagger}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-3 gap-4"
        >
          {quickActions.map((action) => (
            <motion.button
              key={action.label}
              variants={fadeUp}
              onClick={() => router.push(action.href)}
              className="glass-card glass-card-hover p-6 text-left group cursor-pointer"
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${action.gradient} flex items-center justify-center mb-4 shadow-lg`}>
                <action.icon className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-1">{action.label}</h3>
              <p className="text-sm text-gray-400">{action.desc}</p>
              <div className="flex items-center gap-1 text-blue-400 text-sm mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                <span>Go</span>
                <ArrowUpRight className="w-3 h-3" />
              </div>
            </motion.button>
          ))}
        </motion.div>
      </div>

      {/* Cart Summary */}
      {cartCount > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-6 border-l-4 border-blue-500"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center">
                <ShoppingCart className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <p className="text-white font-semibold">
                  {cartCount} item{cartCount !== 1 ? 's' : ''} in cart
                </p>
                <p className="text-gray-400 text-sm">
                  Total: {formatPaise(totalPaise)}
                </p>
              </div>
            </div>
            <button
              onClick={() => router.push('/buyer/cart')}
              className="px-4 py-2 rounded-xl bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors text-sm font-medium"
            >
              View Cart →
            </button>
          </div>
        </motion.div>
      )}

      {/* How It Works */}
      <div className="glass-card p-8">
        <h2 className="text-lg font-semibold text-white mb-6">
          How Transactra Protects You
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[
            { step: '01', title: 'Set Mandate', desc: 'Define spending limits, categories, and time windows' },
            { step: '02', title: 'AI Proposes', desc: 'Agent searches, compares, and negotiates on your behalf' },
            { step: '03', title: 'Gate Verifies', desc: '16 predicates checked deterministically — no exceptions' },
            { step: '04', title: 'Evidence Proof', desc: 'SHA-256 hash chain proves every step was authorized' },
          ].map((item, i) => (
            <motion.div
              key={item.step}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + i * 0.1 }}
              className="text-center"
            >
              <div className="text-3xl font-black bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent mb-3">
                {item.step}
              </div>
              <h3 className="text-white font-semibold mb-1">{item.title}</h3>
              <p className="text-sm text-gray-500">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
