'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ShoppingCart, Filter, Star, Plus, Mic, MicOff } from 'lucide-react';
import toast from 'react-hot-toast';
import { productsApi } from '@/lib/api';
import { useCartStore } from '@/lib/store';
import { formatPaise, cn } from '@/lib/utils';
import type { Product } from '@/lib/types';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const { addItem } = useCartStore();

  // Load all products on mount
  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const data = await productsApi.getAll();
      setProducts(data.products || []);
    } catch {
      // If API not available, use empty
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      loadProducts();
      return;
    }
    setLoading(true);
    try {
      const data = await productsApi.search(searchQuery);
      setProducts(data.products || []);
    } catch {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = (product: Product) => {
    addItem(product);
    toast.success(`${product.title} added to cart`);
  };

  // Voice input
  const toggleVoice = () => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      toast.error('Voice input not supported in this browser');
      return;
    }
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (isListening) {
      setIsListening(false);
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setQuery(transcript);
      handleSearch(transcript);
    };
    recognition.onend = () => setIsListening(false);
    recognition.start();
    setIsListening(true);
  };

  const categories = [...new Set(products.map((p) => p.category))];
  const filteredProducts = selectedCategory
    ? products.filter((p) => p.category === selectedCategory)
    : products;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Search Products</h1>
        <p className="text-gray-400 mt-1">
          Find products from verified merchants
        </p>
      </div>

      {/* Search Bar */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              handleSearch(e.target.value);
            }}
            className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-all text-sm"
            placeholder="Search products, categories, merchants..."
          />
        </div>
        <motion.button
          onClick={toggleVoice}
          className={cn(
            'w-12 h-12 rounded-xl flex items-center justify-center transition-all shrink-0',
            isListening
              ? 'bg-red-500/20 text-red-400 border border-red-500/30'
              : 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:text-white hover:border-gray-600'
          )}
          whileTap={{ scale: 0.95 }}
        >
          {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
        </motion.button>
      </div>

      {/* Category Filters */}
      {categories.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setSelectedCategory(null)}
            className={cn(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
              !selectedCategory
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                : 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:text-white'
            )}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat === selectedCategory ? null : cat)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize',
                cat === selectedCategory
                  ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  : 'bg-gray-800/50 text-gray-400 border border-gray-700 hover:text-white'
              )}
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      {/* Product Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="glass-card p-5 space-y-4">
              <div className="skeleton h-40 w-full" />
              <div className="skeleton h-5 w-3/4" />
              <div className="skeleton h-4 w-1/2" />
              <div className="skeleton h-8 w-full" />
            </div>
          ))}
        </div>
      ) : (
        <AnimatePresence mode="popLayout">
          <motion.div
            layout
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {filteredProducts.map((product, idx) => (
              <motion.div
                key={product.sku}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ delay: idx * 0.05 }}
                className="glass-card glass-card-hover p-5 flex flex-col"
              >
                {/* Product Image Placeholder */}
                <div className="w-full h-40 rounded-xl bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center mb-4">
                  <span className="text-4xl">
                    {product.category === 'electronics' ? '📱' :
                     product.category === 'clothing' ? '👕' :
                     product.category === 'food' ? '🍕' :
                     product.category === 'books' ? '📚' : '📦'}
                  </span>
                </div>

                {/* Info */}
                <div className="flex-1">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-white font-semibold line-clamp-2">{product.title}</h3>
                  </div>
                  <p className="text-gray-500 text-xs line-clamp-2 mb-3">{product.description}</p>

                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xs px-2 py-0.5 rounded-md bg-gray-800 text-gray-400 capitalize">
                      {product.category}
                    </span>
                    <span className="text-xs text-gray-600">by {product.merchant_name}</span>
                  </div>
                </div>

                {/* Price + Add */}
                <div className="flex items-center justify-between pt-3 border-t border-gray-800">
                  <span className="text-xl font-bold text-white">
                    {formatPaise(product.price_paise)}
                  </span>
                  <motion.button
                    onClick={() => handleAddToCart(product)}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-all text-sm font-medium"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Plus className="w-4 h-4" />
                    Add
                  </motion.button>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </AnimatePresence>
      )}

      {!loading && filteredProducts.length === 0 && (
        <div className="text-center py-20">
          <Search className="w-12 h-12 text-gray-700 mx-auto mb-4" />
          <p className="text-gray-500">No products found. Try a different search.</p>
        </div>
      )}
    </div>
  );
}
