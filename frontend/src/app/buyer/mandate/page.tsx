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
        <div className="card p-10 text-center">
          <div className="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4" style={{ background: 'rgba(16,185,129,0.1)' }}>
            <Check className="w-6 h-6" style={{ color: '#10b981' }} />
          </div>
          <h2 className="text-lg font-semibold mb-1" style={{ color: 'var(--text)' }}>Mandate created</h2>
          <p className="text-sm mb-6" style={{ color: 'var(--text-secondary)' }}>
            Budget bounded to {formatPaise(Math.round(parseFloat(maxAmount) * 100))}
          </p>
          <button onClick={() => router.push('/buyer/orders')} className="text-sm font-medium" style={{ color: 'var(--accent)' }}>
            Continue to orders →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md space-y-5">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Create Mandate</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Set spending boundaries for your AI agent</p>
      </div>

      <div className="card p-6 space-y-4">
        <div>
          <label className="block text-sm mb-2" style={{ color: 'var(--text-secondary)' }}>Type</label>
          <div className="grid grid-cols-4 gap-1.5">
            {types.map(t => (
              <button key={t.value} onClick={() => setMandateType(t.value)}
                className={mandateType === t.value ? 'badge badge-info' : 'badge badge-neutral'}
                style={{ cursor: 'pointer', padding: '6px 0', justifyContent: 'center', display: 'flex', borderRadius: '6px' }}
              >{t.label}</button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>Maximum amount (₹)</label>
          <input type="number" value={maxAmount} onChange={e => setMaxAmount(e.target.value)} className="input" placeholder="Enter maximum amount" />
          {totalPaise > 0 && <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>Cart: {formatPaise(totalPaise)}</p>}
        </div>
        <div>
          <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>Allowed categories</label>
          <input type="text" value={categories} onChange={e => setCategories(e.target.value)} className="input" placeholder="Enter categories (comma-separated, or leave empty for all)" />
        </div>
        <div>
          <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>Valid for (days)</label>
          <input type="number" value={validDays} onChange={e => setValidDays(e.target.value)} className="input" placeholder="Enter number of days" min="1" max="365" />
        </div>
        <button onClick={handleCreate} disabled={loading} className="btn-primary w-full">
          {loading ? 'Creating...' : 'Create mandate'} <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
