'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { ShieldCheck, Package, ShoppingBag, BarChart3, Star, LogOut, ChevronLeft, ChevronRight, Plus, Sun, Moon } from 'lucide-react';
import { useAuthStore, useUIStore } from '@/lib/store';

const nav = [
  { label: 'Dashboard', href: '/merchant', icon: BarChart3 },
  { label: 'Products', href: '/merchant/products', icon: Package },
  { label: 'Orders', href: '/merchant/orders', icon: ShoppingBag },
  { label: 'Trust Score', href: '/merchant/trust', icon: Star },
];

export default function MerchantLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, logout, role } = useAuthStore();
  const { sidebarOpen, toggleSidebar, theme, toggleTheme } = useUIStore();

  useEffect(() => {
    if (!isAuthenticated) router.push('/auth/login');
    else if (role === 'buyer') router.push('/buyer');
  }, [isAuthenticated, role, router]);

  if (!isAuthenticated || role === 'buyer') return null;

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg-subtle)' }}>
      <aside className="fixed top-0 left-0 h-screen flex flex-col transition-all duration-200"
        style={{ width: sidebarOpen ? 240 : 60, background: 'var(--sidebar-bg)', borderRight: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2.5 px-4 h-14" style={{ borderBottom: '1px solid var(--border)' }}>
          <ShieldCheck className="w-5 h-5 shrink-0" style={{ color: 'var(--accent)' }} />
          {sidebarOpen && <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Transactra</span>}
        </div>
        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {nav.map(item => {
            const active = pathname === item.href;
            return (
              <button key={item.href} onClick={() => router.push(item.href)} className={`nav-item ${active ? 'nav-item-active' : ''}`}>
                <item.icon className="w-4 h-4 shrink-0" />
                {sidebarOpen && <span>{item.label}</span>}
              </button>
            );
          })}
        </nav>
        <div className="px-2 pb-3 space-y-0.5" style={{ borderTop: '1px solid var(--border)', paddingTop: '12px' }}>
          <button onClick={toggleTheme} className="nav-item">
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            {sidebarOpen && <span>{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>}
          </button>
          <button onClick={toggleSidebar} className="nav-item">
            {sidebarOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            {sidebarOpen && <span>Collapse</span>}
          </button>
          <button onClick={() => { logout(); router.push('/'); }} className="nav-item" style={{ color: 'var(--text-muted)' }}>
            <LogOut className="w-4 h-4" />{sidebarOpen && <span>Sign out</span>}
          </button>
        </div>
      </aside>
      <main className="flex-1 transition-all duration-200" style={{ marginLeft: sidebarOpen ? 240 : 60 }}>
        <header className="sticky top-0 z-30 h-14 flex items-center justify-between px-6 backdrop-blur-sm"
          style={{ background: 'var(--bg-subtle)', borderBottom: '1px solid var(--border)' }}>
          <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            Welcome, <span style={{ color: 'var(--text)', fontWeight: 500 }}>{user?.name || 'Merchant'}</span>
          </span>
          <button onClick={() => router.push('/merchant/products/new')} className="btn-secondary">
            <Plus className="w-3.5 h-3.5" /> Add product
          </button>
        </header>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
