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
      <button onClick={() => router.back()} className="flex items-center gap-1.5 text-sm" style={{ color: 'var(--text-secondary)' }}>
        <ArrowLeft className="w-3.5 h-3.5" /> Back
      </button>
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Add Product</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>List a new product</p>
      </div>
      <div className="card p-6 space-y-4">
        <div>
          <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>Title</label>
          <input type="text" value={title} onChange={e => setTitle(e.target.value)} className="input" placeholder="Enter product title" />
        </div>
        <div>
          <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>Description</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} rows={3}
            className="input" style={{ resize: 'none' }} placeholder="Enter product description" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>Price (₹)</label>
            <input type="number" value={price} onChange={e => setPrice(e.target.value)} className="input" placeholder="Enter price" />
          </div>
          <div>
            <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>Category</label>
            <select value={category} onChange={e => setCategory(e.target.value)} className="input" style={{ appearance: 'none', textTransform: 'capitalize' }}>
              {categories.map(c => <option key={c} value={c} style={{ textTransform: 'capitalize' }}>{c}</option>)}
            </select>
          </div>
        </div>
        <button onClick={handleCreate} disabled={loading} className="btn-primary w-full">
          {loading ? 'Creating...' : 'Create product'}
        </button>
      </div>
    </div>
  );
}
