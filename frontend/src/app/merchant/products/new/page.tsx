'use client';

import { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';

const categories = ['electronics', 'clothing', 'food', 'books', 'home', 'sports'];

export default function NewProductPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [category, setCategory] = useState('electronics');
  const [loading, setLoading] = useState(false);

  const handleCreate = () => {
    if (!title || !price) { toast.error('Title and price required'); return; }
    setLoading(true);
    setTimeout(() => { toast.success('Product created'); router.push('/merchant/products'); }, 600);
  };

  return (
    <div className="max-w-md space-y-5">
      <button onClick={() => router.back()} className="flex items-center gap-1.5 text-zinc-500 hover:text-zinc-300 text-sm">
        <ArrowLeft className="w-3.5 h-3.5" /> Back
      </button>

      <div>
        <h1 className="text-xl font-semibold text-white">Add Product</h1>
        <p className="text-sm text-zinc-500 mt-0.5">List a new product</p>
      </div>

      <div className="border border-zinc-800 rounded-lg bg-zinc-900 p-5 space-y-4">
        <div>
          <label className="block text-sm text-zinc-400 mb-1.5">Title</label>
          <input type="text" value={title} onChange={e => setTitle(e.target.value)}
            className="w-full px-3 py-2 rounded-md bg-zinc-950 border border-zinc-800 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600"
            placeholder="Enter product title" />
        </div>
        <div>
          <label className="block text-sm text-zinc-400 mb-1.5">Description</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} rows={3}
            className="w-full px-3 py-2 rounded-md bg-zinc-950 border border-zinc-800 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600 resize-none"
            placeholder="Enter product description" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm text-zinc-400 mb-1.5">Price (₹)</label>
            <input type="number" value={price} onChange={e => setPrice(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-zinc-950 border border-zinc-800 text-white text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600"
              placeholder="Enter price" />
          </div>
          <div>
            <label className="block text-sm text-zinc-400 mb-1.5">Category</label>
            <select value={category} onChange={e => setCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-md bg-zinc-950 border border-zinc-800 text-white text-sm focus:outline-none focus:border-zinc-600 appearance-none capitalize"
            >
              {categories.map(c => <option key={c} value={c} className="bg-zinc-900">{c}</option>)}
            </select>
          </div>
        </div>
        <button onClick={handleCreate} disabled={loading}
          className="w-full py-2 rounded-md bg-white text-zinc-900 text-sm font-medium hover:bg-zinc-200 transition-colors disabled:opacity-40"
        >{loading ? 'Creating...' : 'Create product'}</button>
      </div>
    </div>
  );
}
