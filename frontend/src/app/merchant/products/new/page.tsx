'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, IndianRupee, Tag, FileText, Check } from 'lucide-react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';

export default function NewProductPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [category, setCategory] = useState('electronics');
  const [loading, setLoading] = useState(false);

  const categories = ['electronics', 'clothing', 'food', 'books', 'home', 'sports'];

  const handleCreate = async () => {
    if (!title || !price) {
      toast.error('Title and price are required');
      return;
    }
    setLoading(true);
    setTimeout(() => {
      toast.success('Product created successfully!');
      router.push('/merchant/products');
    }, 800);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Products
      </button>

      <div>
        <h1 className="text-3xl font-bold text-white">Add Product</h1>
        <p className="text-gray-400 mt-1">List a new product in your catalog</p>
      </div>

      <div className="glass-card p-6 space-y-5">
        <div>
          <label className="block text-sm text-gray-400 mb-1.5">Product Title</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-all"
            placeholder="e.g. Premium Wireless Earbuds"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1.5">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-all resize-none"
            placeholder="Describe your product..."
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Price (₹)</label>
            <div className="relative">
              <IndianRupee className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-all"
                placeholder="999"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white focus:outline-none focus:border-purple-500 transition-all appearance-none"
            >
              {categories.map((c) => (
                <option key={c} value={c} className="bg-gray-800">{c}</option>
              ))}
            </select>
          </div>
        </div>

        <motion.button
          onClick={handleCreate}
          disabled={loading}
          className="w-full py-3.5 rounded-xl bg-gradient-to-r from-purple-600 to-purple-500 text-white font-semibold hover:from-purple-500 hover:to-purple-400 transition-all disabled:opacity-50"
          whileHover={{ scale: loading ? 1 : 1.01 }}
          whileTap={{ scale: loading ? 1 : 0.99 }}
        >
          {loading ? 'Creating...' : 'Create Product'}
        </motion.button>
      </div>
    </div>
  );
}
