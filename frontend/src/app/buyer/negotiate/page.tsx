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
    const list = parseFloat(listPrice) * 100;
    const offer = parseFloat(offerPrice) * 100;
    if (offer >= list) { toast.error('Offer must be less than list price'); return; }

    setLoading(true);
    setTimeout(() => {
      const accepted = offer / list >= 0.80;
      setResult({
        accepted,
        counter_price_paise: accepted ? null : Math.round(list * 0.85),
        savings_paise: accepted ? list - offer : 0,
        message: accepted ? 'Offer accepted.' : `Counter-offer: ${formatPaise(Math.round(list * 0.85))}. Minimum is 85% of list.`,
      });
      setLoading(false);
    }, 800);
  };

  return (
    <div className="max-w-md space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-white">Negotiate</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Submit a price offer</p>
      </div>

      <div className="border border-zinc-800 rounded-lg bg-zinc-900 p-5 space-y-4">
        <div>
          <label className="block text-sm text-zinc-400 mb-1.5">Product name</label>
          <input type="text" value={productName} onChange={e => setProductName(e.target.value)}
            className="w-full px-3 py-2 rounded-md bg-zinc-950 border border-zinc-800 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600"
            placeholder="Enter product name" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm text-zinc-400 mb-1.5">List price (₹)</label>
            <input type="number" value={listPrice} onChange={e => { setListPrice(e.target.value); if (e.target.value) setOfferPrice(String(Math.round(parseFloat(e.target.value) * 0.85))); }}
              className="w-full px-3 py-2 rounded-md bg-zinc-950 border border-zinc-800 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600"
              placeholder="Enter list price" />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1.5">Your offer (₹)</label>
            <input type="number" value={offerPrice} onChange={e => setOfferPrice(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-zinc-950 border border-zinc-800 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600"
              placeholder="Enter your offer" />
          </div>
        </div>
        {listPrice && offerPrice && (
          <p className="text-xs text-zinc-500">
            {Math.round((1 - parseFloat(offerPrice) / parseFloat(listPrice)) * 100)}% discount requested
          </p>
        )}
        <button onClick={handleSubmit} disabled={loading}
          className="w-full py-2 rounded-md bg-white text-zinc-900 text-sm font-medium hover:bg-zinc-200 transition-colors disabled:opacity-40 flex items-center justify-center gap-1.5"
        >{loading ? 'Negotiating...' : 'Submit offer'} <Send className="w-3.5 h-3.5" /></button>
      </div>

      {result && (
        <div className={`border rounded-lg p-4 ${result.accepted ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-zinc-700 bg-zinc-900'}`}>
          <div className="flex items-center gap-2 mb-1">
            {result.accepted ? <Check className="w-4 h-4 text-emerald-400" /> : <Handshake className="w-4 h-4 text-zinc-400" />}
            <span className={`text-sm font-medium ${result.accepted ? 'text-emerald-400' : 'text-zinc-300'}`}>
              {result.accepted ? 'Accepted' : 'Counter offer'}
            </span>
          </div>
          <p className="text-xs text-zinc-500">{result.message}</p>
          {result.accepted && result.savings_paise > 0 && (
            <p className="text-xs text-emerald-400 mt-2">Saved {formatPaise(result.savings_paise)}</p>
          )}
        </div>
      )}
    </div>
  );
}
