'use client';

import { IndianRupee, Package, ShoppingBag, Star, ArrowRight, Shield, CheckCircle } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { formatPaise, getStatusColor } from '@/lib/utils';

const stats = [
  { label: 'Revenue', value: '₹2,45,000', icon: IndianRupee },
  { label: 'Products', value: '12', icon: Package },
  { label: 'Orders', value: '47', icon: ShoppingBag },
  { label: 'Trust Score', value: '0.94', icon: Star },
];

const recentOrders = [
  { id: 'ORD-A1B2', buyer: 'Rahul S.', amount: 150000, status: 'paid', time: '2h ago' },
  { id: 'ORD-C3D4', buyer: 'Priya M.', amount: 85000, status: 'payment_pending', time: '4h ago' },
  { id: 'ORD-E5F6', buyer: 'Amit K.', amount: 320000, status: 'fulfilled', time: '1d ago' },
];

export default function MerchantDashboard() {
  const router = useRouter();

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-white">Dashboard</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Revenue, orders, and trust overview</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {stats.map(s => (
          <div key={s.label} className="border border-zinc-800 rounded-lg bg-zinc-900 p-4">
            <div className="flex items-center gap-2 mb-3">
              <s.icon className="w-4 h-4 text-zinc-500" />
              <span className="text-xs text-zinc-500">{s.label}</span>
            </div>
            <p className="text-2xl font-semibold text-white">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Recent Orders */}
        <div className="border border-zinc-800 rounded-lg bg-zinc-900 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-white">Recent Orders</h2>
            <button onClick={() => router.push('/merchant/orders')} className="text-xs text-zinc-500 hover:text-zinc-300">
              View all →
            </button>
          </div>
          <div className="space-y-2">
            {recentOrders.map(o => (
              <div key={o.id} className="flex items-center justify-between py-2 border-b border-zinc-800 last:border-0">
                <div>
                  <p className="text-sm text-white">{o.id}</p>
                  <p className="text-xs text-zinc-600">{o.buyer} · {o.time}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-white">{formatPaise(o.amount)}</p>
                  <span className={`text-xs ${getStatusColor(o.status)}`}>{o.status.replace('_', ' ')}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Trust Summary */}
        <div className="border border-zinc-800 rounded-lg bg-zinc-900 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-white">Trust Evidence</h2>
            <button onClick={() => router.push('/merchant/trust')} className="text-xs text-zinc-500 hover:text-zinc-300">
              Details →
            </button>
          </div>
          <div className="flex items-center gap-6 mb-4">
            <div className="relative w-20 h-20">
              <svg className="w-20 h-20 -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="#27272a" strokeWidth="6" />
                <circle cx="50" cy="50" r="42" fill="none" stroke="#3b82f6" strokeWidth="6"
                  strokeDasharray={`${0.94 * 264} ${264}`} strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-lg font-semibold text-white">0.94</span>
              </div>
            </div>
            <div className="space-y-1.5 flex-1 text-sm">
              <div className="flex justify-between"><span className="text-zinc-500">Fulfillment</span><span className="text-zinc-300">96%</span></div>
              <div className="flex justify-between"><span className="text-zinc-500">On-time</span><span className="text-zinc-300">92%</span></div>
              <div className="flex justify-between"><span className="text-zinc-500">Disputes</span><span className="text-zinc-300">1.2%</span></div>
              <div className="flex justify-between"><span className="text-zinc-500">Chain integrity</span><span className="text-zinc-300">100%</span></div>
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-400">
            <Shield className="w-3 h-3" />
            <span>All evidence chains verified</span>
          </div>
        </div>
      </div>
    </div>
  );
}
