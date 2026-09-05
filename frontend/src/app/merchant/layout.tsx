'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldCheck, Package, ShoppingBag, BarChart3,
  Star, LogOut, ChevronLeft, ChevronRight, Plus,
} from 'lucide-react';
import { useAuthStore, useUIStore } from '@/lib/store';
import { cn } from '@/lib/utils';

const merchantNav = [
  { label: 'Dashboard', href: '/merchant', icon: BarChart3 },
  { label: 'Products', href: '/merchant/products', icon: Package },
  { label: 'Orders', href: '/merchant/orders', icon: ShoppingBag },
  { label: 'Trust Score', href: '/merchant/trust', icon: Star },
];

export default function MerchantLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, logout, role } = useAuthStore();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
    } else if (role === 'buyer') {
      router.push('/buyer');
    }
  }, [isAuthenticated, role, router]);

  if (!isAuthenticated || role === 'buyer') return null;

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <div className="flex min-h-screen bg-[#030712]">
      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: sidebarOpen ? 260 : 72 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        className="fixed top-0 left-0 h-screen z-40 flex flex-col border-r border-gray-800/50 bg-[#0a0e1a]/80 backdrop-blur-xl"
      >
        <div className="flex items-center gap-3 px-4 h-16 border-b border-gray-800/50">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-600 to-purple-400 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <AnimatePresence>
            {sidebarOpen && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="text-lg font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent overflow-hidden whitespace-nowrap"
              >
                Transactra
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {merchantNav.map((item) => {
            const isActive = pathname === item.href;
            return (
              <motion.button
                key={item.href}
                onClick={() => router.push(item.href)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-sm',
                  isActive
                    ? 'bg-purple-500/10 text-purple-400 font-medium'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                )}
                whileHover={{ x: 2 }}
                whileTap={{ scale: 0.98 }}
              >
                <item.icon className={cn('w-5 h-5 shrink-0', isActive && 'text-purple-400')} />
                <AnimatePresence>
                  {sidebarOpen && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="overflow-hidden whitespace-nowrap"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.button>
            );
          })}
        </nav>

        <div className="border-t border-gray-800/50 p-2 space-y-1">
          <button
            onClick={toggleSidebar}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all text-sm"
          >
            {sidebarOpen ? (
              <><ChevronLeft className="w-5 h-5 shrink-0" /><span>Collapse</span></>
            ) : (
              <ChevronRight className="w-5 h-5 shrink-0" />
            )}
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-400 hover:text-red-400 hover:bg-red-500/5 transition-all text-sm"
          >
            <LogOut className="w-5 h-5 shrink-0" />
            <AnimatePresence>
              {sidebarOpen && (
                <motion.span initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  Sign Out
                </motion.span>
              )}
            </AnimatePresence>
          </button>
        </div>
      </motion.aside>

      <main className={cn('flex-1 transition-all duration-300', sidebarOpen ? 'ml-[260px]' : 'ml-[72px]')}>
        <header className="sticky top-0 z-30 h-16 flex items-center justify-between px-6 border-b border-gray-800/30 bg-[#030712]/80 backdrop-blur-xl">
          <h2 className="text-sm font-medium text-gray-400">
            Welcome, <span className="text-white">{user?.name || 'Merchant'}</span>
          </h2>
          <button
            onClick={() => router.push('/merchant/products/new')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 transition-all text-sm font-medium"
          >
            <Plus className="w-4 h-4" />
            Add Product
          </button>
        </header>

        <motion.div
          key={pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="p-6"
        >
          {children}
        </motion.div>
      </main>
    </div>
  );
}
