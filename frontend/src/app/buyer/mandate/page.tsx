'use client';

import { useState } from 'react';
import { Check, ArrowRight } from 'lucide-react';
import toast from 'react-hot-toast';
import { useRouter } from 'next/navigation';
import { mandatesApi } from '@/lib/api';
import { useAuthStore, useCartStore } from '@/lib/store';
import { formatPaise, generateUUID } from '@/lib/utils';

export default function MandatePage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { totalPaise } = useCartStore();
  const [mandateType, setMandateType] = useState('one_time');
  const [maxAmount, setMaxAmount] = useState(totalPaise ? String(totalPaise / 100) : '');
  const [categories, setCategories] = useState('');
  const [validDays, setValidDays] = useState('7');
  const [loading, setLoading] = useState(false);
  const [created, setCreated] = useState(false);

  const types = [
    { value: 'one_time', label: 'One-time' },
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' },
  ];

  const handleCreate = async () => {
    if (!maxAmount || parseFloat(maxAmount) <= 0) { toast.error('Enter a valid amount'); return; }
    setLoading(true);
    try {
      await mandatesApi.create({
        user_id: user?.id || generateUUID(),
        agent_id: generateUUID(),
        mandate_type: mandateType,
        max_amount_paise: Math.round(parseFloat(maxAmount) * 100),
        currency: 'INR',
        allowed_categories: categories ? categories.split(',').map(c => c.trim()) : [],
        valid_until: new Date(Date.now() + parseInt(validDays) * 86400000).toISOString(),
      });
      setCreated(true);
      toast.success('Mandate created');
    } catch (err: any) { toast.error(err.detail || 'Failed'); }
    finally { setLoading(false); }
  };

  if (created) {
    return (
      <div className="max-w-md">
        <div className="border border-zinc-800 rounded-lg bg-zinc-900 p-8 text-center">
          <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-4">
            <Check className="w-5 h-5 text-emerald-400" />
          </div>
          <h2 className="text-base font-semibold text-white mb-1">Mandate created</h2>
          <p className="text-sm text-zinc-500 mb-6">
            Budget bounded to {formatPaise(Math.round(parseFloat(maxAmount) * 100))}
          </p>
          <button onClick={() => router.push('/buyer/orders')} className="text-xs text-blue-400 hover:text-blue-300">
            Continue to orders →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-white">Create Mandate</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Set spending boundaries for your AI agent</p>
      </div>

      <div className="border border-zinc-800 rounded-lg bg-zinc-900 p-5 space-y-4">
        <div>
          <label className="block text-sm text-zinc-400 mb-2">Type</label>
          <div className="grid grid-cols-4 gap-1.5">
            {types.map(t => (
              <button key={t.value} onClick={() => setMandateType(t.value)}
                className={`py-1.5 rounded-md text-xs font-medium transition-colors ${
                  mandateType === t.value ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'
                }`}
              >{t.label}</button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm text-zinc-400 mb-1.5">Maximum amount (₹)</label>
          <input type="number" value={maxAmount} onChange={e => setMaxAmount(e.target.value)}
            className="w-full px-3 py-2 rounded-md bg-zinc-950 border border-zinc-800 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600"
            placeholder="Enter maximum amount" />
          {totalPaise > 0 && <p className="text-xs text-zinc-600 mt-1">Cart: {formatPaise(totalPaise)}</p>}
        </div>

        <div>
          <label className="block text-sm text-zinc-400 mb-1.5">Allowed categories</label>
          <input type="text" value={categories} onChange={e => setCategories(e.target.value)}
            className="w-full px-3 py-2 rounded-md bg-zinc-950 border border-zinc-800 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600"
            placeholder="Enter categories (comma-separated, or leave empty for all)" />
        </div>

        <div>
          <label className="block text-sm text-zinc-400 mb-1.5">Valid for (days)</label>
          <input type="number" value={validDays} onChange={e => setValidDays(e.target.value)}
            className="w-full px-3 py-2 rounded-md bg-zinc-950 border border-zinc-800 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600"
            placeholder="Enter number of days" min="1" max="365" />
        </div>

        <button onClick={handleCreate} disabled={loading}
          className="w-full py-2 rounded-md bg-white text-zinc-900 text-sm font-medium hover:bg-zinc-200 transition-colors disabled:opacity-40 flex items-center justify-center gap-1.5"
        >
          {loading ? 'Creating...' : 'Create mandate'} <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
