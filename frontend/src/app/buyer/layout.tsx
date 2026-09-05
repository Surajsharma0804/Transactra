'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldCheck, Search, ShoppingCart, FileText,
  Handshake, Package, LogOut, ChevronLeft, ChevronRight, Mic,
} from 'lucide-react';
import { useAuthStore, useUIStore } from '@/lib/store';
import { cn } from '@/lib/utils';

const buyerNav = [
  { label: 'Dashboard', href: '/buyer', icon: Package },
  { label: 'Search', href: '/buyer/search', icon: Search },
  { label: 'Cart', href: '/buyer/cart', icon: ShoppingCart },
  { label: 'Mandates', href: '/buyer/mandate', icon: FileText },
  { label: 'Negotiate', href: '/buyer/negotiate', icon: Handshake },
  { label: 'Orders', href: '/buyer/orders', icon: Package },
];

export default function BuyerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, logout, role } = useAuthStore();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  // Protect route — redirect if not buyer
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login');
    } else if (role === 'merchant') {
      router.push('/merchant');
    }
  }, [isAuthenticated, role, router]);

  if (!isAuthenticated || role === 'merchant') return null;

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
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 h-16 border-b border-gray-800/50">
          <div className="w-9 h-9 rounded-xl gradient-primary flex items-center justify-center shrink-0">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <AnimatePresence>
            {sidebarOpen && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent overflow-hidden whitespace-nowrap"
              >
                Transactra
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {/* Nav Items */}
        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {buyerNav.map((item) => {
            const isActive = pathname === item.href;
            return (
              <motion.button
                key={item.href}
                onClick={() => router.push(item.href)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-sm',
                  isActive
                    ? 'bg-blue-500/10 text-blue-400 font-medium'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                )}
                whileHover={{ x: 2 }}
                whileTap={{ scale: 0.98 }}
              >
                <item.icon className={cn('w-5 h-5 shrink-0', isActive && 'text-blue-400')} />
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
                {isActive && (
                  <motion.div
                    layoutId="buyer-active"
                    className="absolute left-0 w-1 h-6 rounded-r-full bg-blue-400"
                  />
                )}
              </motion.button>
            );
          })}
        </nav>

        {/* Toggle + Logout */}
        <div className="border-t border-gray-800/50 p-2 space-y-1">
          <button
            onClick={toggleSidebar}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800/50 transition-all text-sm"
          >
            {sidebarOpen ? (
              <>
                <ChevronLeft className="w-5 h-5 shrink-0" />
                <span>Collapse</span>
              </>
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
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  Sign Out
                </motion.span>
              )}
            </AnimatePresence>
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main
        className={cn(
          'flex-1 transition-all duration-300',
          sidebarOpen ? 'ml-[260px]' : 'ml-[72px]'
        )}
      >
        {/* Top Bar */}
        <header className="sticky top-0 z-30 h-16 flex items-center justify-between px-6 border-b border-gray-800/30 bg-[#030712]/80 backdrop-blur-xl">
          <div>
            <h2 className="text-sm font-medium text-gray-400">
              Welcome back, <span className="text-white">{user?.name || 'Buyer'}</span>
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <button className="w-9 h-9 rounded-xl bg-gray-800/50 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-700/50 transition-all">
              <Mic className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Page Content */}
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
