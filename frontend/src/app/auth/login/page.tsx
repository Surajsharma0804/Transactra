'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ShieldCheck, ArrowLeft, Eye, EyeOff, Sun, Moon } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuthStore, useUIStore } from '@/lib/store';
import { authApi } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const { role, setAuth, setRole } = useAuthStore();
  const { theme, toggleTheme } = useUIStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) { toast.error('Please fill in all fields'); return; }
    if (isRegister && !name) { toast.error('Please enter your name'); return; }

    setLoading(true);
    try {
      let response;
      if (isRegister) {
        response = await authApi.register(email, password, name, role || 'buyer');
        toast.success('Account created');
      } else {
        response = await authApi.login(email, password);
        toast.success(`Welcome back, ${response.user.name}`);
      }
      setAuth(response.user, response.access_token);
      router.push(`/${response.user.role}`);
    } catch (err: any) {
      toast.error(err.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const roleLabel = role === 'merchant' ? 'Merchant' : 'Buyer';

  return (
    <div className="min-h-screen hero-gradient flex flex-col">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-4 max-w-5xl mx-auto w-full">
        <button
          onClick={() => { setRole(null); router.push('/'); }}
          className="flex items-center gap-1.5 text-sm"
          style={{ color: 'var(--text-secondary)' }}
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back
        </button>
        <button onClick={toggleTheme} className="btn-secondary" style={{ padding: '6px 10px' }}>
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </header>

      {/* Form */}
      <main className="flex-1 flex items-center justify-center px-4 pb-16">
        <div className="w-full max-w-sm">
          <div className="card p-8">
            {/* Header */}
            <div className="text-center mb-6">
              <div
                className="inline-flex items-center justify-center w-12 h-12 rounded-xl mb-4"
                style={{ background: 'var(--accent-subtle)' }}
              >
                <ShieldCheck className="w-6 h-6" style={{ color: 'var(--accent)' }} />
              </div>
              <h1 className="text-xl font-semibold" style={{ color: 'var(--text)' }}>
                {isRegister ? 'Create account' : 'Welcome back'}
              </h1>
              <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
                {isRegister ? 'Register' : 'Sign in'} as{' '}
                <span className="font-medium" style={{ color: 'var(--accent)' }}>{roleLabel}</span>
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {isRegister && (
                <div>
                  <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="input"
                    placeholder="Enter your full name"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input"
                  placeholder="Enter your email"
                  autoComplete="email"
                />
              </div>

              <div>
                <label className="block text-sm mb-1.5" style={{ color: 'var(--text-secondary)' }}>Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input"
                    style={{ paddingRight: '38px' }}
                    placeholder="Enter your password"
                    autoComplete={isRegister ? 'new-password' : 'current-password'}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2"
                    style={{ color: 'var(--text-muted)' }}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading
                  ? (isRegister ? 'Creating account...' : 'Signing in...')
                  : (isRegister ? 'Create account' : 'Sign in')
                }
              </button>
            </form>

            <div className="mt-5 text-center">
              <button
                onClick={() => setIsRegister(!isRegister)}
                className="text-sm"
                style={{ color: 'var(--text-muted)' }}
              >
                {isRegister
                  ? <>Have an account? <span style={{ color: 'var(--accent)' }}>Sign in</span></>
                  : <>No account? <span style={{ color: 'var(--accent)' }}>Create one</span></>
                }
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
