/**
 * Transactra — Global State (Zustand)
 *
 * Lightweight, type-safe global state management.
 * Replaces the monolithic AppState object from index.html.
 *
 * Stores:
 * - Auth state (user, token, role)
 * - Cart state (items, total, hash)
 * - UI state (sidebar, theme)
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, UserRole, CartItem, Product, Mandate } from './types';

// ── Auth Store ──────────────────────────────────────

interface AuthState {
  user: User | null;
  token: string | null;
  role: UserRole | null;
  isAuthenticated: boolean;

  setAuth: (user: User, token: string) => void;
  setRole: (role: UserRole | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      role: null,
      isAuthenticated: false,

      setAuth: (user, token) =>
        set({
          user,
          token,
          role: user.role,
          isAuthenticated: true,
        }),

      setRole: (role) => set({ role }),

      logout: () =>
        set({
          user: null,
          token: null,
          role: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'transactra-auth',
      // Only persist non-sensitive fields — token stays in sessionStorage
      partialize: (state) => ({
        role: state.role,
      }),
    }
  )
);

// ── Cart Store ──────────────────────────────────────

interface CartState {
  items: Map<string, CartItem>;
  totalPaise: number;
  cartHash: string;

  addItem: (product: Product, quantity?: number) => void;
  removeItem: (sku: string) => void;
  updateQuantity: (sku: string, quantity: number) => void;
  clearCart: () => void;
  getItemCount: () => number;
}

export const useCartStore = create<CartState>()((set, get) => ({
  items: new Map(),
  totalPaise: 0,
  cartHash: '',

  addItem: (product, quantity = 1) =>
    set((state) => {
      const newItems = new Map(state.items);
      const existing = newItems.get(product.sku);
      if (existing) {
        newItems.set(product.sku, {
          ...existing,
          quantity: existing.quantity + quantity,
        });
      } else {
        newItems.set(product.sku, { product, quantity });
      }
      const totalPaise = calculateTotal(newItems);
      return {
        items: newItems,
        totalPaise,
        cartHash: computeCartHash(newItems),
      };
    }),

  removeItem: (sku) =>
    set((state) => {
      const newItems = new Map(state.items);
      newItems.delete(sku);
      const totalPaise = calculateTotal(newItems);
      return {
        items: newItems,
        totalPaise,
        cartHash: computeCartHash(newItems),
      };
    }),

  updateQuantity: (sku, quantity) =>
    set((state) => {
      const newItems = new Map(state.items);
      const item = newItems.get(sku);
      if (item && quantity > 0) {
        newItems.set(sku, { ...item, quantity });
      } else if (quantity <= 0) {
        newItems.delete(sku);
      }
      const totalPaise = calculateTotal(newItems);
      return {
        items: newItems,
        totalPaise,
        cartHash: computeCartHash(newItems),
      };
    }),

  clearCart: () =>
    set({ items: new Map(), totalPaise: 0, cartHash: '' }),

  getItemCount: () => {
    let count = 0;
    get().items.forEach((item) => (count += item.quantity));
    return count;
  },
}));

// ── UI Store ────────────────────────────────────────

interface UIState {
  sidebarOpen: boolean;
  theme: 'dark' | 'light';
  toggleSidebar: () => void;
  toggleTheme: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'dark',
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      toggleTheme: () =>
        set((s) => ({ theme: s.theme === 'dark' ? 'light' : 'dark' })),
    }),
    { name: 'transactra-ui' }
  )
);

// ── Helper Functions ────────────────────────────────

function calculateTotal(items: Map<string, CartItem>): number {
  let total = 0;
  items.forEach((item) => {
    total += item.product.price_paise * item.quantity;
  });
  return total;
}

function computeCartHash(items: Map<string, CartItem>): string {
  // Deterministic JSON for hashing
  const sorted = Array.from(items.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([sku, item]) => ({
      sku,
      quantity: item.quantity,
      price_paise: item.product.price_paise,
    }));

  const canonical = JSON.stringify(sorted);

  // Synchronous FNV-1a hash (crypto.subtle is async, not usable in Zustand set())
  let hash = 0x811c9dc5;
  for (let i = 0; i < canonical.length; i++) {
    hash ^= canonical.charCodeAt(i);
    hash = (hash * 0x01000193) >>> 0;
  }
  return hash.toString(16).padStart(8, '0');
}
