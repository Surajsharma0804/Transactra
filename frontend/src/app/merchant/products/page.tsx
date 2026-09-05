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
        <h1 className="text-xl font-semibold text-white">Products</h1>
        <p className="text-sm text-zinc-500 mt-0.5">Manage your catalog</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {products.map(p => (
          <div key={p.sku} className="border border-zinc-800 rounded-lg bg-zinc-900 p-4">
            <div className="w-full h-24 rounded-md bg-zinc-800 flex items-center justify-center mb-3">
              <Package className="w-8 h-8 text-zinc-700" />
            </div>
            <h3 className="text-sm font-medium text-white">{p.title}</h3>
            <div className="flex items-center gap-2 mt-1.5 mb-3">
              <span className="text-xs text-zinc-600 capitalize">{p.category}</span>
              <span className={`text-xs ${p.in_stock ? 'text-emerald-400' : 'text-red-400'}`}>
                {p.in_stock ? 'In stock' : 'Out of stock'}
              </span>
            </div>
            <div className="flex items-center justify-between pt-2.5 border-t border-zinc-800">
              <span className="text-base font-semibold text-white">{formatPaise(p.price_paise)}</span>
              <span className="text-xs text-zinc-600 font-mono">{p.sku}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
