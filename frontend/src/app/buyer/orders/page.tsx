'use client';

import { motion } from 'framer-motion';
import { Package, Eye, Shield, Clock } from 'lucide-react';
import { formatPaise, formatRelativeTime, getStatusColor, cn } from '@/lib/utils';

const mockOrders = [
  { order_id: 'a1b2c3d4', status: 'paid', total_paise: 150000, cart_hash: 'f4a2e8...3c91', created_at: new Date(Date.now() - 7200000).toISOString(), evidence_chain_length: 5 },
  { order_id: 'e5f6g7h8', status: 'payment_pending', total_paise: 85000, cart_hash: '7b3d19...a4f2', created_at: new Date(Date.now() - 14400000).toISOString(), evidence_chain_length: 3 },
  { order_id: 'i9j0k1l2', status: 'fulfilled', total_paise: 320000, cart_hash: 'c9e1f5...8d72', created_at: new Date(Date.now() - 86400000).toISOString(), evidence_chain_length: 8 },
];

export default function OrdersPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Orders</h1>
        <p className="text-gray-400 mt-1">Your transaction history with evidence trails</p>
      </div>

      <div className="space-y-3">
        {mockOrders.map((order, idx) => (
          <motion.div
            key={order.order_id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.08 }}
            className="glass-card p-5 flex items-center justify-between hover:border-gray-600 transition-all cursor-pointer"
          >
            <div className="flex items-center gap-4">
              <div className="w-11 h-11 rounded-xl bg-blue-500/10 flex items-center justify-center">
                <Package className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-white font-semibold text-sm">ORD-{order.order_id.slice(0, 8).toUpperCase()}</span>
                  <span className={cn('text-xs px-2 py-0.5 rounded-md font-medium', getStatusColor(order.status))}>
                    {order.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatRelativeTime(order.created_at)}
                  </span>
                  <span className="hash-display">{order.cart_hash}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className="text-right">
                <p className="text-white font-semibold">{formatPaise(order.total_paise)}</p>
                <div className="flex items-center gap-1 text-xs text-emerald-400 mt-0.5">
                  <Shield className="w-3 h-3" />
                  <span>{order.evidence_chain_length} evidence records</span>
                </div>
              </div>
              <button className="w-8 h-8 rounded-lg bg-gray-800/50 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-700/50 transition-all">
                <Eye className="w-4 h-4" />
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
