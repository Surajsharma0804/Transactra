'use client';

import { motion } from 'framer-motion';
import {
  TrendingUp, Package, ShoppingBag, Star,
  ArrowUpRight, IndianRupee, BarChart3, Shield,
} from 'lucide-react';
import { useRouter } from 'next/navigation';

const stats = [
  { label: 'Total Revenue', value: '₹2,45,000', change: '+18%', icon: IndianRupee, color: 'emerald' },
  { label: 'Products Listed', value: '12', change: '3 new', icon: Package, color: 'blue' },
  { label: 'Orders', value: '47', change: '+8 this week', icon: ShoppingBag, color: 'purple' },
  { label: 'Trust Score', value: '0.94', change: 'Excellent', icon: Star, color: 'amber' },
];

const recentOrders = [
  { id: 'ORD-001', buyer: 'Rahul S.', amount: 15000, status: 'paid', time: '2h ago' },
  { id: 'ORD-002', buyer: 'Priya M.', amount: 8500, status: 'payment_pending', time: '4h ago' },
  { id: 'ORD-003', buyer: 'Amit K.', amount: 32000, status: 'fulfilled', time: '1d ago' },
];

const stagger = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

export default function MerchantDashboard() {
  const router = useRouter();

  const statusColors: Record<string, string> = {
    paid: 'text-emerald-400 bg-emerald-400/10',
    payment_pending: 'text-amber-400 bg-amber-400/10',
    fulfilled: 'text-blue-400 bg-blue-400/10',
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">Merchant Dashboard</h1>
        <p className="text-gray-400 mt-1">Track revenue, orders, and trust score</p>
      </div>

      {/* Stats */}
      <motion.div variants={stagger} initial="hidden" animate="show" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <motion.div key={stat.label} variants={fadeUp} className="glass-card p-5">
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Orders */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white">Recent Orders</h2>
            <button
              onClick={() => router.push('/merchant/orders')}
              className="text-sm text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1"
            >
              View All <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>
          <div className="space-y-3">
            {recentOrders.map((order) => (
              <div key={order.id} className="flex items-center justify-between p-3 rounded-xl bg-gray-800/30 hover:bg-gray-800/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-purple-500/10 flex items-center justify-center">
                    <ShoppingBag className="w-4 h-4 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-white text-sm font-medium">{order.id}</p>
                    <p className="text-gray-500 text-xs">{order.buyer} · {order.time}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-white text-sm font-medium">₹{(order.amount / 100).toLocaleString()}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-md ${statusColors[order.status] || 'text-gray-400 bg-gray-800'}`}>
                    {order.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Trust Score Card */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white">Trust Evidence</h2>
            <button
              onClick={() => router.push('/merchant/trust')}
              className="text-sm text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-1"
            >
              Details <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>

          {/* Trust Score Circle */}
          <div className="flex items-center gap-8 mb-6">
            <div className="relative w-28 h-28">
              <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="#1f2937" strokeWidth="8" />
                <circle
                  cx="50" cy="50" r="42" fill="none" stroke="url(#trustGradient)" strokeWidth="8"
                  strokeDasharray={`${0.94 * 264} ${264}`}
                  strokeLinecap="round"
                />
                <defs>
                  <linearGradient id="trustGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#8b5cf6" />
                    <stop offset="100%" stopColor="#10b981" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold text-white">0.94</span>
              </div>
            </div>
            <div className="space-y-2 flex-1">
              {[
                { label: 'Fulfillment Rate', value: '96%', color: 'emerald' },
                { label: 'On-Time Delivery', value: '92%', color: 'blue' },
                { label: 'Dispute Rate', value: '1.2%', color: 'amber' },
                { label: 'Chain Integrity', value: '100%', color: 'purple' },
              ].map((m) => (
                <div key={m.label} className="flex items-center justify-between text-sm">
                  <span className="text-gray-400">{m.label}</span>
                  <span className={`text-${m.color}-400 font-medium`}>{m.value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-400" />
              <p className="text-xs text-emerald-400">
                All evidence chains verified — zero tampering detected
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
