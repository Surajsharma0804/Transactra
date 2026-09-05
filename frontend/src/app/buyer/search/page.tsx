'use client';

import { useState, useEffect } from 'react';
import { Search, Plus, Mic, MicOff } from 'lucide-react';
import toast from 'react-hot-toast';
import { productsApi } from '@/lib/api';
import { useCartStore } from '@/lib/store';
import { formatPaise } from '@/lib/utils';
import type { Product } from '@/lib/types';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const { addItem } = useCartStore();

  useEffect(() => { loadProducts(); }, []);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const data = await productsApi.getAll();
      setProducts(data.products || []);
    } catch { setProducts([]); }
    finally { setLoading(false); }
  };

  const handleSearch = async (q: string) => {
    if (!q.trim()) { loadProducts(); return; }
    setLoading(true);
    try {
      const data = await productsApi.search(q);
      setProducts(data.products || []);
    } catch { toast.error('Search failed'); }
    finally { setLoading(false); }
  };

  const toggleVoice = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      toast.error('Voice not supported'); return;
    }
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (isListening) { setIsListening(false); return; }
    const r = new SR();
    r.lang = 'en-IN';
    r.onresult = (e: any) => { const t = e.results[0][0].transcript; setQuery(t); handleSearch(t); };
    r.onend = () => setIsListening(false);
    r.start();
    setIsListening(true);
  };

  const categories = [...new Set(products.map((p) => p.category))];
  const filtered = selectedCategory ? products.filter((p) => p.category === selectedCategory) : products;

  return (
    <div className="max-w-5xl space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-white">Search Products</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Browse verified merchant catalog</p>
      </div>

      {/* Search */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600" />
          <input
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); handleSearch(e.target.value); }}
            className="w-full pl-9 pr-3 py-2 rounded-md bg-zinc-950 border border-zinc-800 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600 transition-colors"
            placeholder="Search products..."
          />
        </div>
        <button
          onClick={toggleVoice}
          className={`w-9 h-9 rounded-md flex items-center justify-center border transition-colors shrink-0 ${
            isListening ? 'border-red-500/40 bg-red-500/10 text-red-400' : 'border-zinc-800 bg-zinc-900 text-zinc-500 hover:text-zinc-300'
          }`}
        >
          {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </button>
      </div>

      {/* Filters */}
      {categories.length > 0 && (
        <div className="flex gap-1.5 flex-wrap">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-2.5 py-1 rounded-md text-xs transition-colors ${
              !selectedCategory ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'
            }`}
          >All</button>
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setSelectedCategory(c === selectedCategory ? null : c)}
              className={`px-2.5 py-1 rounded-md text-xs capitalize transition-colors ${
                c === selectedCategory ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >{c}</button>
          ))}
        </div>
      )}

      {/* Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {[1,2,3,4,5,6].map(i => (
            <div key={i} className="border border-zinc-800 rounded-lg p-4 space-y-3">
              <div className="skeleton h-28 w-full" />
              <div className="skeleton h-4 w-3/4" />
              <div className="skeleton h-4 w-1/2" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map((p) => (
            <div key={p.sku} className="border border-zinc-800 rounded-lg bg-zinc-900 p-4 flex flex-col">
              <div className="w-full h-28 rounded-md bg-zinc-800 flex items-center justify-center mb-3 text-2xl">
                {p.category === 'electronics' ? '📱' : p.category === 'clothing' ? '👕' : p.category === 'food' ? '🍕' : p.category === 'books' ? '📚' : '📦'}
              </div>
              <h3 className="text-sm font-medium text-white line-clamp-2">{p.title}</h3>
              <p className="text-xs text-zinc-600 line-clamp-1 mt-1">{p.merchant_name}</p>
              <div className="flex items-center justify-between mt-auto pt-3">
                <span className="text-base font-semibold text-white">{formatPaise(p.price_paise)}</span>
                <button
                  onClick={() => { addItem(p); toast.success('Added to cart'); }}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-md border border-zinc-700 text-xs text-zinc-300 hover:bg-zinc-800 transition-colors"
                >
                  <Plus className="w-3 h-3" /> Add
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-16">
          <p className="text-sm text-zinc-600">No products found</p>
        </div>
      )}
    </div>
  );
}
