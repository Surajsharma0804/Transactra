'use client';

import { Trash2, Minus, Plus, ShoppingBag, ArrowRight, Hash } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCartStore } from '@/lib/store';
import { formatPaise } from '@/lib/utils';

export default function CartPage() {
  const router = useRouter();
  const { items, totalPaise, cartHash, removeItem, updateQuantity, clearCart } = useCartStore();
  const cartItems = Array.from(items.values());

  if (cartItems.length === 0) {
    return (
      <div className="max-w-3xl">
        <h1 className="text-xl font-semibold text-white mb-6">Cart</h1>
        <div className="border border-zinc-800 rounded-lg bg-zinc-900 p-12 text-center">
          <ShoppingBag className="w-10 h-10 text-zinc-700 mx-auto mb-3" />
          <p className="text-sm text-zinc-500 mb-4">Your cart is empty</p>
          <button onClick={() => router.push('/buyer/search')} className="text-xs text-blue-400 hover:text-blue-300">
            Browse products →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">Cart</h1>
          <p className="text-sm text-zinc-500 mt-0.5">{cartItems.length} item{cartItems.length !== 1 ? 's' : ''}</p>
        </div>
        <button onClick={clearCart} className="text-xs text-zinc-600 hover:text-red-400 transition-colors">Clear all</button>
      </div>

      <div className="space-y-2">
        {cartItems.map((item) => (
          <div key={item.product.sku} className="flex items-center gap-3 p-3 border border-zinc-800 rounded-lg bg-zinc-900">
            <div className="w-10 h-10 rounded-md bg-zinc-800 flex items-center justify-center text-lg shrink-0">
              {item.product.category === 'electronics' ? '📱' : item.product.category === 'clothing' ? '👕' : '📦'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white truncate">{item.product.title}</p>
              <p className="text-xs text-zinc-600">{formatPaise(item.product.price_paise)}</p>
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              <button onClick={() => updateQuantity(item.product.sku, item.quantity - 1)} className="w-6 h-6 rounded bg-zinc-800 flex items-center justify-center text-zinc-400 hover:text-white text-xs">
                <Minus className="w-3 h-3" />
              </button>
              <span className="w-6 text-center text-sm text-white">{item.quantity}</span>
              <button onClick={() => updateQuantity(item.product.sku, item.quantity + 1)} className="w-6 h-6 rounded bg-zinc-800 flex items-center justify-center text-zinc-400 hover:text-white text-xs">
                <Plus className="w-3 h-3" />
              </button>
            </div>
            <span className="text-sm font-medium text-white w-20 text-right shrink-0">
              {formatPaise(item.product.price_paise * item.quantity)}
            </span>
            <button onClick={() => removeItem(item.product.sku)} className="text-zinc-700 hover:text-red-400 transition-colors shrink-0">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>

      <div className="border border-zinc-800 rounded-lg bg-zinc-900 p-4 space-y-3">
        <div className="flex items-center gap-2 text-xs text-zinc-600">
          <Hash className="w-3 h-3" />
          <span className="hash-display truncate">{cartHash || 'computing...'}</span>
        </div>
        <div className="flex items-center justify-between pt-3 border-t border-zinc-800">
          <span className="text-sm text-zinc-400">Total</span>
          <span className="text-lg font-semibold text-white">{formatPaise(totalPaise)}</span>
        </div>
        <button
          onClick={() => router.push('/buyer/mandate')}
          className="w-full py-2 rounded-md bg-white text-zinc-900 text-sm font-medium hover:bg-zinc-200 transition-colors flex items-center justify-center gap-1.5"
        >
          Proceed to mandate setup <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
