import type { Metadata } from 'next';
import { Toaster } from 'react-hot-toast';
import './globals.css';

export const metadata: Metadata = {
  title: 'Transactra — The Trust Infrastructure for Agentic Commerce',
  description:
    'AI proposes, deterministic infrastructure verifies. Bounded authority, auditable trust, real payments.',
  keywords: [
    'agentic commerce',
    'AI payments',
    'trust infrastructure',
    'mandate-based authorization',
  ],
  openGraph: {
    title: 'Transactra',
    description: 'The Trust Infrastructure for Agentic Commerce',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-[#030712] text-gray-100 antialiased">
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#1f2937',
              color: '#f9fafb',
              border: '1px solid #374151',
              borderRadius: '12px',
              fontSize: '14px',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#030712',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#030712',
              },
            },
          }}
        />
        {children}
      </body>
    </html>
  );
}
