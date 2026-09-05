'use client';

import { motion } from 'framer-motion';
import { ShoppingBag, Clock, CheckCircle } from 'lucide-react';
import { formatPaise, formatRelativeTime, getStatusColor, cn } from '@/lib/utils';

const orders = [
  { id: 'ORD-A1B2', buyer: 'Rahul Sharma', total_paise: 150000, status: 'paid', items: 2, created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: 'ORD-C3D4', buyer: 'Priya Mehta', total_paise: 85000, status: 'payment_pending', items: 1, created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: 'ORD-E5F6', buyer: 'Amit Kumar', total_paise: 320000, status: 'fulfilled', items: 3, created_at: new Date(Date.now() - 86400000).toISOString() },
  { id: 'ORD-G7H8', buyer: 'Neha Singh', total_paise: 45000, status: 'created', items: 1, created_at: new Date(Date.now() - 172800000).toISOString() },
];

export default function MerchantOrdersPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Incoming Orders</h1>
        <p className="text-gray-400 mt-1">Track and fulfill customer orders</p>
      </div>

      <div className="space-y-3">
        {orders.map((order, idx) => (
          <motion.div
            key={order.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.08 }}
            className="glass-card p-5 flex items-center justify-between"
          >
            <div className="flex items-center gap-4">
              <div className="w-11 h-11 rounded-xl bg-purple-500/10 flex items-center justify-center">
                <ShoppingBag className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-white font-semibold text-sm">{order.id}</span>
                  <span className={cn('text-xs px-2 py-0.5 rounded-md font-medium', getStatusColor(order.status))}>
                    {order.status.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-gray-500 text-xs mt-1">
                  {order.buyer} · {order.items} item{order.items !== 1 ? 's' : ''} · {formatRelativeTime(order.created_at)}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-white font-semibold">{formatPaise(order.total_paise)}</p>
              {order.status === 'paid' && (
                <button className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1 mt-1 ml-auto">
                  <CheckCircle className="w-3 h-3" />
                  Mark Fulfilled
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
