'use client';

import { useState } from 'react';
import { Send, Check, Handshake } from 'lucide-react';
import toast from 'react-hot-toast';
import { formatPaise } from '@/lib/utils';

export default function NegotiatePage() {
  const [productName, setProductName] = useState('');
  const [listPrice, setListPrice] = useState('');
  const [offerPrice, setOfferPrice] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = () => {
    if (!listPrice || !offerPrice) { toast.error('Enter both prices'); return; }
    const list = parseFloat(listPrice) * 100, offer = parseFloat(offerPrice) * 100;
    if (offer >= list) { toast.error('Offer must be less than list price'); return; }
    setLoading(true);
    setTimeout(() => {
      const accepted = offer / list >= 0.80;
      setResult({
        accepted,
        counter_price_paise: accepted ? null : Math.round(list * 0.85),
        savings_paise: accepted ? list - offer : 0,
        message: accepted ? 'Offer accepted.' : `Counter-offer: ${formatPaise(Math.round(list * 0.85))}`,
      });
      setLoading(false);
    }, 800);
  };

  return (
    <div className="max-w-md space-y-5">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Negotiate</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Submit a price offer</p>
      </div>
      <div className="card p-6 space-y-4">
        <div>
          <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>Product name</label>
          <input type="text" value={productName} onChange={e => setProductName(e.target.value)} className="input" placeholder="Enter product name" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>List price (₹)</label>
            <input type="number" value={listPrice} onChange={e => { setListPrice(e.target.value); if (e.target.value) setOfferPrice(String(Math.round(parseFloat(e.target.value) * 0.85))); }} className="input" placeholder="Enter list price" />
          </div>
          <div>
            <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>Your offer (₹)</label>
            <input type="number" value={offerPrice} onChange={e => setOfferPrice(e.target.value)} className="input" placeholder="Enter your offer" />
          </div>
        </div>
        {listPrice && offerPrice && (
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
            {Math.round((1 - parseFloat(offerPrice) / parseFloat(listPrice)) * 100)}% discount requested
          </p>
        )}
        <button onClick={handleSubmit} disabled={loading} className="btn-primary w-full">
          {loading ? 'Negotiating...' : 'Submit offer'} <Send className="w-4 h-4" />
        </button>
      </div>
      {result && (
        <div className="card p-5" style={{ borderLeft: `3px solid ${result.accepted ? '#10b981' : 'var(--border-hover)'}` }}>
          <div className="flex items-center gap-2 mb-1">
            {result.accepted ? <Check className="w-4 h-4" style={{ color: '#10b981' }} /> : <Handshake className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />}
            <span className="text-sm font-medium" style={{ color: result.accepted ? '#10b981' : 'var(--text)' }}>
              {result.accepted ? 'Accepted' : 'Counter offer'}
            </span>
          </div>
          <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{result.message}</p>
          {result.accepted && result.savings_paise > 0 && (
            <p className="text-xs mt-2" style={{ color: '#10b981' }}>Saved {formatPaise(result.savings_paise)}</p>
          )}
        </div>
      )}
    </div>
  );
}
