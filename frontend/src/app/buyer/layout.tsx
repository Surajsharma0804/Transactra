'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import {
  ShieldCheck, Search, ShoppingCart, FileText,
  Handshake, Package, LogOut, ChevronLeft, ChevronRight,
} from 'lucide-react';
import { useAuthStore, useUIStore } from '@/lib/store';

const nav = [
  { label: 'Dashboard', href: '/buyer', icon: Package },
  { label: 'Search', href: '/buyer/search', icon: Search },
  { label: 'Cart', href: '/buyer/cart', icon: ShoppingCart },
  { label: 'Mandates', href: '/buyer/mandate', icon: FileText },
  { label: 'Negotiate', href: '/buyer/negotiate', icon: Handshake },
  { label: 'Orders', href: '/buyer/orders', icon: Package },
];

export default function BuyerLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, logout, role } = useAuthStore();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  useEffect(() => {
    if (!isAuthenticated) router.push('/auth/login');
    else if (role === 'merchant') router.push('/merchant');
  }, [isAuthenticated, role, router]);

  if (!isAuthenticated || role === 'merchant') return null;

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside
        className="fixed top-0 left-0 h-screen flex flex-col border-r border-zinc-800 bg-zinc-950 transition-all duration-200"
        style={{ width: sidebarOpen ? 220 : 56 }}
      >
        <div className="flex items-center gap-2 px-3 h-12 border-b border-zinc-800">
          <ShieldCheck className="w-4.5 h-4.5 text-blue-500 shrink-0" />
          {sidebarOpen && <span className="text-sm font-semibold text-white truncate">Transactra</span>}
        </div>

        <nav className="flex-1 py-2 px-1.5 space-y-0.5 overflow-y-auto">
          {nav.map((item) => {
            const active = pathname === item.href;
            return (
              <button
                key={item.href}
                onClick={() => router.push(item.href)}
                className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-md text-sm transition-colors ${
                  active
                    ? 'bg-zinc-800 text-white'
                    : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900'
                }`}
              >
                <item.icon className="w-4 h-4 shrink-0" />
                {sidebarOpen && <span className="truncate">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        <div className="border-t border-zinc-800 p-1.5 space-y-0.5">
          <button
            onClick={toggleSidebar}
            className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-md text-sm text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900 transition-colors"
          >
            {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            {sidebarOpen && <span>Collapse</span>}
          </button>
          <button
            onClick={() => { logout(); router.push('/'); }}
            className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-md text-sm text-zinc-500 hover:text-red-400 hover:bg-zinc-900 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            {sidebarOpen && <span>Sign out</span>}
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 transition-all duration-200" style={{ marginLeft: sidebarOpen ? 220 : 56 }}>
        <header className="sticky top-0 z-30 h-12 flex items-center px-6 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur-sm">
          <span className="text-sm text-zinc-500">
            {user?.name || 'Buyer'}
          </span>
        </header>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
