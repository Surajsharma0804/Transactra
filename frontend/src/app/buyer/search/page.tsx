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
    try { const d = await productsApi.getAll(); setProducts(d.products || []); }
    catch { setProducts([]); }
    finally { setLoading(false); }
  };

  const handleSearch = async (q: string) => {
    if (!q.trim()) { loadProducts(); return; }
    setLoading(true);
    try { const d = await productsApi.search(q); setProducts(d.products || []); }
    catch { toast.error('Search failed'); }
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
    r.start(); setIsListening(true);
  };

  const categories = [...new Set(products.map(p => p.category))];
  const filtered = selectedCategory ? products.filter(p => p.category === selectedCategory) : products;

  return (
    <div className="max-w-5xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Search Products</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Browse verified merchant catalog</p>
      </div>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-muted)' }} />
          <input
            type="text" value={query}
            onChange={e => { setQuery(e.target.value); handleSearch(e.target.value); }}
            className="input" style={{ paddingLeft: '36px' }}
            placeholder="Search products..."
          />
        </div>
        <button onClick={toggleVoice} className={isListening ? 'btn-primary' : 'btn-secondary'} style={{ padding: '0 12px' }}>
          {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </button>
      </div>

      {categories.length > 0 && (
        <div className="flex gap-1.5 flex-wrap">
          <button onClick={() => setSelectedCategory(null)}
            className={!selectedCategory ? 'badge badge-info' : 'badge badge-neutral'}
            style={{ cursor: 'pointer', padding: '4px 10px', fontSize: '12px' }}
          >All</button>
          {categories.map(c => (
            <button key={c} onClick={() => setSelectedCategory(c === selectedCategory ? null : c)}
              className={c === selectedCategory ? 'badge badge-info' : 'badge badge-neutral'}
              style={{ cursor: 'pointer', padding: '4px 10px', fontSize: '12px', textTransform: 'capitalize' }}
            >{c}</button>
          ))}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1,2,3,4,5,6].map(i => (
            <div key={i} className="card p-5 space-y-3">
              <div className="skeleton h-28 w-full" />
              <div className="skeleton h-4 w-3/4" />
              <div className="skeleton h-4 w-1/2" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(p => (
            <div key={p.sku} className="card p-5 flex flex-col">
              <div className="w-full h-28 rounded-lg flex items-center justify-center mb-3 text-2xl" style={{ background: 'var(--bg-subtle)' }}>
                {p.category === 'electronics' ? '📱' : p.category === 'clothing' ? '👕' : p.category === 'food' ? '🍕' : p.category === 'books' ? '📚' : '📦'}
              </div>
              <h3 className="text-sm font-medium line-clamp-2" style={{ color: 'var(--text)' }}>{p.title}</h3>
              <p className="text-xs mt-1 line-clamp-1" style={{ color: 'var(--text-muted)' }}>{p.merchant_name}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="badge badge-neutral" style={{ textTransform: 'capitalize' }}>{p.category}</span>
              </div>
              <div className="flex items-center justify-between mt-auto pt-4" style={{ borderTop: '1px solid var(--border)', marginTop: '12px' }}>
                <span className="text-base font-semibold" style={{ color: 'var(--text)' }}>{formatPaise(p.price_paise)}</span>
                <button onClick={() => { addItem(p); toast.success('Added to cart'); }} className="btn-secondary" style={{ padding: '5px 10px', fontSize: '12px' }}>
                  <Plus className="w-3.5 h-3.5" /> Add
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-16">
          <Search className="w-10 h-10 mx-auto mb-3" style={{ color: 'var(--border)' }} />
          <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No products found</p>
        </div>
      )}
    </div>
  );
}
