'use client';

import { motion } from 'framer-motion';
import { Trash2, Minus, Plus, ShoppingBag, ArrowRight, Hash } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCartStore } from '@/lib/store';
import { formatPaise, truncateHash } from '@/lib/utils';

export default function CartPage() {
  const router = useRouter();
  const { items, totalPaise, cartHash, removeItem, updateQuantity, clearCart } = useCartStore();
  const cartItems = Array.from(items.values());

  if (cartItems.length === 0) {
    return (
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-2">Cart</h1>
        <div className="glass-card p-16 text-center mt-8">
          <ShoppingBag className="w-16 h-16 text-gray-700 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-400 mb-2">Your cart is empty</h2>
          <p className="text-gray-600 mb-6">Search for products to add to your cart</p>
          <button
            onClick={() => router.push('/buyer/search')}
            className="px-6 py-3 rounded-xl bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-all font-medium"
          >
            Browse Products →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Cart</h1>
          <p className="text-gray-400 mt-1">{cartItems.length} item{cartItems.length !== 1 ? 's' : ''}</p>
        </div>
        <button
          onClick={clearCart}
          className="text-sm text-gray-500 hover:text-red-400 transition-colors"
        >
          Clear All
        </button>
      </div>

      {/* Cart Items */}
      <div className="space-y-3">
        {cartItems.map((item, idx) => (
          <motion.div
            key={item.product.sku}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.05 }}
            className="glass-card p-4 flex items-center gap-4"
          >
            {/* Product icon */}
            <div className="w-16 h-16 rounded-xl bg-gray-800 flex items-center justify-center shrink-0">
              <span className="text-2xl">
                {item.product.category === 'electronics' ? '📱' :
                 item.product.category === 'clothing' ? '👕' : '📦'}
              </span>
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <h3 className="text-white font-medium truncate">{item.product.title}</h3>
              <p className="text-gray-500 text-xs">{item.product.merchant_name}</p>
              <p className="text-blue-400 font-semibold mt-1">
                {formatPaise(item.product.price_paise)}
              </p>
            </div>

            {/* Quantity Controls */}
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => updateQuantity(item.product.sku, item.quantity - 1)}
                className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-700 transition-all"
              >
                <Minus className="w-3 h-3" />
              </button>
              <span className="w-8 text-center text-white font-medium">{item.quantity}</span>
              <button
                onClick={() => updateQuantity(item.product.sku, item.quantity + 1)}
                className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-700 transition-all"
              >
                <Plus className="w-3 h-3" />
              </button>
            </div>

            {/* Line Total */}
            <div className="w-24 text-right shrink-0">
              <p className="text-white font-semibold">
                {formatPaise(item.product.price_paise * item.quantity)}
              </p>
            </div>

            {/* Remove */}
            <button
              onClick={() => removeItem(item.product.sku)}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-600 hover:text-red-400 hover:bg-red-500/5 transition-all shrink-0"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </motion.div>
        ))}
      </div>

      {/* Cart Summary */}
      <div className="glass-card p-6 space-y-4">
        {/* Cart Hash */}
        <div className="flex items-center gap-2 p-3 rounded-xl bg-gray-800/50 border border-gray-700">
          <Hash className="w-4 h-4 text-purple-400 shrink-0" />
          <div className="min-w-0">
            <p className="text-xs text-gray-500 mb-0.5">Cart SHA-256 Hash</p>
            <p className="hash-display truncate">{cartHash || 'Computing...'}</p>
          </div>
        </div>

        {/* Total */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-800">
          <span className="text-gray-400 font-medium">Total</span>
          <span className="text-2xl font-bold text-white">{formatPaise(totalPaise)}</span>
        </div>

        {/* Checkout */}
        <motion.button
          onClick={() => router.push('/buyer/mandate')}
          className="w-full py-3.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white font-semibold flex items-center justify-center gap-2 glow-blue hover:from-blue-500 hover:to-blue-400 transition-all"
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
        >
          Proceed to Mandate Setup
          <ArrowRight className="w-4 h-4" />
        </motion.button>

        <p className="text-xs text-gray-600 text-center">
          Next step: Set spending limits before payment authorization
        </p>
      </div>
    </div>
  );
}
