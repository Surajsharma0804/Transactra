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
        <h1 className="text-2xl font-semibold mb-6" style={{ color: 'var(--text)' }}>Cart</h1>
        <div className="card p-14 text-center">
          <ShoppingBag className="w-10 h-10 mx-auto mb-3" style={{ color: 'var(--border)' }} />
          <p className="text-sm mb-4" style={{ color: 'var(--text-muted)' }}>Your cart is empty</p>
          <button onClick={() => router.push('/buyer/search')} className="text-sm font-medium" style={{ color: 'var(--accent)' }}>
            Browse products →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold" style={{ color: 'var(--text)' }}>Cart</h1>
          <p className="text-sm mt-0.5" style={{ color: 'var(--text-secondary)' }}>{cartItems.length} item{cartItems.length !== 1 ? 's' : ''}</p>
        </div>
        <button onClick={clearCart} className="text-xs" style={{ color: 'var(--text-muted)' }}>Clear all</button>
      </div>

      <div className="space-y-2">
        {cartItems.map(item => (
          <div key={item.product.sku} className="card flex items-center gap-3 p-4">
            <div className="w-11 h-11 rounded-lg flex items-center justify-center text-lg shrink-0" style={{ background: 'var(--bg-subtle)' }}>
              {item.product.category === 'electronics' ? '📱' : item.product.category === 'clothing' ? '👕' : '📦'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate" style={{ color: 'var(--text)' }}>{item.product.title}</p>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{formatPaise(item.product.price_paise)}</p>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <button onClick={() => updateQuantity(item.product.sku, item.quantity - 1)} className="btn-secondary" style={{ padding: '4px', borderRadius: '6px' }}>
                <Minus className="w-3 h-3" />
              </button>
              <span className="w-7 text-center text-sm font-medium" style={{ color: 'var(--text)' }}>{item.quantity}</span>
              <button onClick={() => updateQuantity(item.product.sku, item.quantity + 1)} className="btn-secondary" style={{ padding: '4px', borderRadius: '6px' }}>
                <Plus className="w-3 h-3" />
              </button>
            </div>
            <span className="text-sm font-medium w-20 text-right shrink-0" style={{ color: 'var(--text)' }}>
              {formatPaise(item.product.price_paise * item.quantity)}
            </span>
            <button onClick={() => removeItem(item.product.sku)} style={{ color: 'var(--text-muted)' }} className="shrink-0 hover:opacity-70">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      <div className="card p-5 space-y-4">
        <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
          <Hash className="w-3 h-3" />
          <span className="hash-display truncate">{cartHash || 'computing...'}</span>
        </div>
        <div className="flex items-center justify-between pt-4" style={{ borderTop: '1px solid var(--border)' }}>
          <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>Total</span>
          <span className="text-xl font-semibold" style={{ color: 'var(--text)' }}>{formatPaise(totalPaise)}</span>
        </div>
        <button onClick={() => router.push('/buyer/mandate')} className="btn-primary w-full">
          Proceed to mandate setup <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
