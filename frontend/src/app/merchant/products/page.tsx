'use client';

import { Package } from 'lucide-react';
import { formatPaise } from '@/lib/utils';

const products = [
  { sku: 'SKU001', title: 'Wireless Earbuds Pro', price_paise: 299900, category: 'electronics', in_stock: true },
  { sku: 'SKU002', title: 'Organic Cotton T-Shirt', price_paise: 89900, category: 'clothing', in_stock: true },
  { sku: 'SKU003', title: 'Smart Water Bottle', price_paise: 149900, category: 'electronics', in_stock: false },
];

export default function ProductsPage() {
  return (
    <div className="max-w-4xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Products</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Manage your catalog</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {products.map(p => (
          <div key={p.sku} className="card p-5">
            <div className="w-full h-24 rounded-lg flex items-center justify-center mb-3" style={{ background: 'var(--bg-subtle)' }}>
              <Package className="w-8 h-8" style={{ color: 'var(--border)' }} />
            </div>
            <h3 className="text-sm font-medium" style={{ color: 'var(--text)' }}>{p.title}</h3>
            <div className="flex items-center gap-2 mt-1.5 mb-3">
              <span className="badge badge-neutral" style={{ textTransform: 'capitalize' }}>{p.category}</span>
              <span className={`badge ${p.in_stock ? 'badge-success' : 'badge-danger'}`}>
                {p.in_stock ? 'In stock' : 'Out of stock'}
              </span>
            </div>
            <div className="flex items-center justify-between pt-3" style={{ borderTop: '1px solid var(--border)' }}>
              <span className="text-base font-semibold" style={{ color: 'var(--text)' }}>{formatPaise(p.price_paise)}</span>
              <span className="hash-display">{p.sku}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
