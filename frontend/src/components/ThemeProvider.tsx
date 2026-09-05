'use client';

import { useEffect } from 'react';
import { useUIStore } from '@/lib/store';

/**
 * Syncs the Zustand theme to the <html> class.
 * Renders nothing — pure side-effect component.
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useUIStore((s) => s.theme);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  return <>{children}</>;
}
