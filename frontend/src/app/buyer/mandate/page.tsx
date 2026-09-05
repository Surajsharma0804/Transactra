'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { FileText, Calendar, IndianRupee, Tag, Store, ArrowRight, Check } from 'lucide-react';
import toast from 'react-hot-toast';
import { useRouter } from 'next/navigation';
import { mandatesApi } from '@/lib/api';
import { useAuthStore, useCartStore } from '@/lib/store';
import { formatPaise, generateUUID, cn } from '@/lib/utils';

export default function MandatePage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { totalPaise } = useCartStore();
  const [mandateType, setMandateType] = useState<string>('one_time');
  const [maxAmount, setMaxAmount] = useState(totalPaise ? String(totalPaise / 100) : '');
  const [categories, setCategories] = useState('');
  const [validDays, setValidDays] = useState('7');
  const [loading, setLoading] = useState(false);
  const [created, setCreated] = useState(false);

  const mandateTypes = [
    { value: 'one_time', label: 'One Time', desc: 'Single transaction' },
    { value: 'daily', label: 'Daily', desc: 'Daily spending limit' },
    { value: 'weekly', label: 'Weekly', desc: 'Weekly budget' },
    { value: 'monthly', label: 'Monthly', desc: 'Monthly allowance' },
  ];

  const handleCreate = async () => {
    if (!maxAmount || parseFloat(maxAmount) <= 0) {
      toast.error('Enter a valid maximum amount');
      return;
    }

    setLoading(true);
    try {
      const mandate = await mandatesApi.create({
        user_id: user?.id || generateUUID(),
        agent_id: generateUUID(),
        mandate_type: mandateType,
        max_amount_paise: Math.round(parseFloat(maxAmount) * 100),
        currency: 'INR',
        allowed_categories: categories ? categories.split(',').map(c => c.trim()) : [],
        valid_until: new Date(Date.now() + parseInt(validDays) * 86400000).toISOString(),
      });
      setCreated(true);
      toast.success('Mandate created! Budget is now bounded.');
    } catch (err: any) {
      toast.error(err.detail || 'Failed to create mandate');
    } finally {
      setLoading(false);
    }
  };

  if (created) {
    return (
      <div className="max-w-2xl mx-auto">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card p-12 text-center"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
            className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-6 glow-green"
          >
            <Check className="w-10 h-10 text-emerald-400" />
          </motion.div>
          <h2 className="text-2xl font-bold text-white mb-2">Mandate Created!</h2>
          <p className="text-gray-400 mb-2">
            Your spending is now bounded to{' '}
            <span className="text-white font-semibold">{formatPaise(Math.round(parseFloat(maxAmount) * 100))}</span>
          </p>
          <p className="text-gray-500 text-sm mb-8">
            The 16-predicate authorization gate will enforce these limits deterministically.
          </p>
          <button
            onClick={() => router.push('/buyer/orders')}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-semibold glow-blue hover:from-blue-500 hover:to-blue-400 transition-all"
          >
            Continue to Orders →
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Create Mandate</h1>
        <p className="text-gray-400 mt-1">
          Set spending boundaries for your AI agent
        </p>
      </div>

      <div className="glass-card p-6 space-y-6">
        {/* Mandate Type */}
        <div>
          <label className="block text-sm text-gray-400 mb-3">Mandate Type</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {mandateTypes.map((type) => (
              <button
                key={type.value}
                onClick={() => setMandateType(type.value)}
                className={cn(
                  'p-3 rounded-xl border text-left transition-all',
                  mandateType === type.value
                    ? 'border-blue-500/50 bg-blue-500/10 text-blue-400'
                    : 'border-gray-700 bg-gray-800/30 text-gray-400 hover:border-gray-600'
                )}
              >
                <p className="text-sm font-medium">{type.label}</p>
                <p className="text-xs text-gray-500 mt-0.5">{type.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Max Amount */}
        <div>
          <label className="block text-sm text-gray-400 mb-1.5">Maximum Amount (₹)</label>
          <div className="relative">
            <IndianRupee className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="number"
              value={maxAmount}
              onChange={(e) => setMaxAmount(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-all"
              placeholder="e.g. 5000"
              min="1"
            />
          </div>
          {totalPaise > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Cart total: {formatPaise(totalPaise)}
            </p>
          )}
        </div>

        {/* Categories */}
        <div>
          <label className="block text-sm text-gray-400 mb-1.5">
            Allowed Categories <span className="text-gray-600">(comma-separated, empty = all)</span>
          </label>
          <div className="relative">
            <Tag className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={categories}
              onChange={(e) => setCategories(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-all"
              placeholder="electronics, clothing"
            />
          </div>
        </div>

        {/* Validity */}
        <div>
          <label className="block text-sm text-gray-400 mb-1.5">Valid For (days)</label>
          <div className="relative">
            <Calendar className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="number"
              value={validDays}
              onChange={(e) => setValidDays(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-all"
              min="1"
              max="365"
            />
          </div>
        </div>

        {/* Submit */}
        <motion.button
          onClick={handleCreate}
          disabled={loading}
          className="w-full py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold flex items-center justify-center gap-2 hover:from-blue-500 hover:to-purple-500 transition-all disabled:opacity-50"
          whileHover={{ scale: loading ? 1 : 1.01 }}
          whileTap={{ scale: loading ? 1 : 0.99 }}
        >
          {loading ? 'Creating...' : 'Create Mandate'}
          <ArrowRight className="w-4 h-4" />
        </motion.button>
      </div>

      {/* Explainer */}
      <div className="glass-card p-5 border-l-4 border-purple-500">
        <p className="text-sm text-gray-400">
          <span className="text-purple-400 font-semibold">What is a mandate?</span>{' '}
          A mandate defines exactly what your AI agent is allowed to spend. It sets the
          maximum amount, allowed categories, and time window. The 16-predicate
          authorization gate will deterministically enforce these limits — no exceptions.
        </p>
      </div>
    </div>
  );
}
