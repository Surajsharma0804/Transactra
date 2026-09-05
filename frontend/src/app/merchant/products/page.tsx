'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Package, Plus, IndianRupee, Tag, FileText } from 'lucide-react';
import toast from 'react-hot-toast';
import { productsApi } from '@/lib/api';
import { formatPaise } from '@/lib/utils';

const mockProducts = [
  { sku: 'SKU001', title: 'Wireless Earbuds Pro', price_paise: 299900, category: 'electronics', in_stock: true },
  { sku: 'SKU002', title: 'Organic Cotton T-Shirt', price_paise: 89900, category: 'clothing', in_stock: true },
  { sku: 'SKU003', title: 'Smart Water Bottle', price_paise: 149900, category: 'electronics', in_stock: false },
];

export default function ProductsPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Products</h1>
          <p className="text-gray-400 mt-1">Manage your product catalog</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockProducts.map((product, idx) => (
          <motion.div
            key={product.sku}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.08 }}
            className="glass-card p-5"
          >
            <div className="w-full h-32 rounded-xl bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center mb-4">
              <Package className="w-10 h-10 text-gray-600" />
            </div>
            <h3 className="text-white font-semibold mb-1">{product.title}</h3>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xs px-2 py-0.5 rounded-md bg-gray-800 text-gray-400 capitalize">{product.category}</span>
              <span className={`text-xs px-2 py-0.5 rounded-md ${product.in_stock ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                {product.in_stock ? 'In Stock' : 'Out of Stock'}
              </span>
            </div>
            <div className="flex items-center justify-between pt-3 border-t border-gray-800">
              <span className="text-lg font-bold text-white">{formatPaise(product.price_paise)}</span>
              <span className="text-xs text-gray-500 hash-display">{product.sku}</span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
