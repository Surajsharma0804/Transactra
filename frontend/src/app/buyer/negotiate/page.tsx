'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Handshake, Send, TrendingDown, Check, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { formatPaise, cn } from '@/lib/utils';

export default function NegotiatePage() {
  const [productName, setProductName] = useState('');
  const [listPrice, setListPrice] = useState('');
  const [offerPrice, setOfferPrice] = useState('');
  const [message, setMessage] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!listPrice || !offerPrice) {
      toast.error('Enter both list price and offer price');
      return;
    }
    const list = parseFloat(listPrice) * 100;
    const offer = parseFloat(offerPrice) * 100;
    if (offer >= list) {
      toast.error('Offer must be less than list price');
      return;
    }

    setLoading(true);
    // Simulate negotiation engine response
    setTimeout(() => {
      const ratio = offer / list;
      const accepted = ratio >= 0.80;
      const counterPrice = accepted ? null : Math.round(list * 0.85);
      setResult({
        accepted,
        counter_price_paise: counterPrice,
        savings_paise: accepted ? list - offer : 0,
        message: accepted
          ? 'Offer accepted! Great deal for both parties.'
          : `Counter-offer: ${formatPaise(counterPrice!)}. The minimum acceptable is 85% of list price.`,
      });
      setLoading(false);
    }, 1200);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Negotiate</h1>
        <p className="text-gray-400 mt-1">AI-powered price negotiation with Pareto-optimal offers</p>
      </div>

      <div className="glass-card p-6 space-y-5">
        <div>
          <label className="block text-sm text-gray-400 mb-1.5">Product Name</label>
          <input
            type="text"
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-all"
            placeholder="e.g. Wireless Earbuds Pro"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">List Price (₹)</label>
            <input
              type="number"
              value={listPrice}
              onChange={(e) => {
                setListPrice(e.target.value);
                if (e.target.value) setOfferPrice(String(Math.round(parseFloat(e.target.value) * 0.85)));
              }}
              className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-all"
              placeholder="2000"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Your Offer (₹)</label>
            <input
              type="number"
              value={offerPrice}
              onChange={(e) => setOfferPrice(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-all"
              placeholder="1700"
            />
          </div>
        </div>

        {listPrice && offerPrice && (
          <div className="flex items-center gap-2 text-sm">
            <TrendingDown className="w-4 h-4 text-emerald-400" />
            <span className="text-emerald-400">
              {Math.round((1 - parseFloat(offerPrice) / parseFloat(listPrice)) * 100)}% discount requested
            </span>
          </div>
        )}

        <div>
          <label className="block text-sm text-gray-400 mb-1.5">Message (optional)</label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={3}
            className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-all resize-none"
            placeholder="I'd like to buy in bulk..."
          />
        </div>

        <motion.button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full py-3.5 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-500 text-white font-semibold flex items-center justify-center gap-2 hover:from-emerald-500 hover:to-emerald-400 transition-all disabled:opacity-50"
          whileHover={{ scale: loading ? 1 : 1.01 }}
          whileTap={{ scale: loading ? 1 : 0.99 }}
        >
          {loading ? 'Negotiating...' : 'Submit Offer'}
          <Send className="w-4 h-4" />
        </motion.button>
      </div>

      {/* Result */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={cn(
            'glass-card p-6 border-l-4',
            result.accepted ? 'border-emerald-500' : 'border-amber-500'
          )}
        >
          <div className="flex items-center gap-3 mb-3">
            <div className={cn(
              'w-10 h-10 rounded-xl flex items-center justify-center',
              result.accepted ? 'bg-emerald-500/10' : 'bg-amber-500/10'
            )}>
              {result.accepted ? (
                <Check className="w-5 h-5 text-emerald-400" />
              ) : (
                <Handshake className="w-5 h-5 text-amber-400" />
              )}
            </div>
            <div>
              <p className={cn('font-semibold', result.accepted ? 'text-emerald-400' : 'text-amber-400')}>
                {result.accepted ? 'Offer Accepted!' : 'Counter Offer'}
              </p>
              <p className="text-gray-400 text-sm">{result.message}</p>
            </div>
          </div>
          {result.accepted && result.savings_paise > 0 && (
            <div className="mt-3 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
              <p className="text-sm text-emerald-400">
                You saved <span className="font-bold">{formatPaise(result.savings_paise)}</span> on this deal!
              </p>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
