'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { ShieldCheck, Mail, Lock, ArrowLeft, Eye, EyeOff } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuthStore } from '@/lib/store';
import { authApi } from '@/lib/api';
import { cn } from '@/lib/utils';

export default function LoginPage() {
  const router = useRouter();
  const { role, setAuth, setRole } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }
    if (isRegister && !name) {
      toast.error('Please enter your name');
      return;
    }

    setLoading(true);
    try {
      let response;
      if (isRegister) {
        response = await authApi.register(email, password, name, role || 'buyer');
        toast.success('Account created successfully!');
      } else {
        response = await authApi.login(email, password);
        toast.success(`Welcome back, ${response.user.name}!`);
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
  const roleColor = role === 'merchant' ? 'purple' : 'blue';

  return (
    <div className="relative min-h-screen flex items-center justify-center px-4 gradient-mesh">
      {/* Background effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className={`absolute -top-40 -right-40 w-96 h-96 rounded-full ${
            role === 'merchant' ? 'bg-purple-500/10' : 'bg-blue-500/10'
          } blur-[120px]`}
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 8, repeat: Infinity }}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Back Button */}
        <motion.button
          onClick={() => { setRole(null); router.push('/'); }}
          className="flex items-center gap-2 text-gray-400 hover:text-white mb-8 transition-colors"
          whileHover={{ x: -4 }}
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm">Choose Different Role</span>
        </motion.button>

        {/* Login Card */}
        <div className="glass-card p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <motion.div
              className={`inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 ${
                role === 'merchant'
                  ? 'bg-purple-500/10 glow-purple'
                  : 'bg-blue-500/10 glow-blue'
              }`}
              initial={{ scale: 0.5, rotate: -10 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 200 }}
            >
              <ShieldCheck className={`w-8 h-8 ${
                role === 'merchant' ? 'text-purple-400' : 'text-blue-400'
              }`} />
            </motion.div>
            <h1 className="text-2xl font-bold text-white mb-1">
              {isRegister ? 'Create Account' : 'Welcome Back'}
            </h1>
            <p className="text-gray-400 text-sm">
              {isRegister ? 'Register' : 'Sign in'} as{' '}
              <span className={cn(
                'font-semibold',
                role === 'merchant' ? 'text-purple-400' : 'text-blue-400'
              )}>
                {roleLabel}
              </span>
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {isRegister && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                <label className="block text-sm text-gray-400 mb-1.5">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-all"
                  placeholder="Your full name"
                />
              </motion.div>
            )}

            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-11 pr-4 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-all"
                  placeholder="you@example.com"
                  autoComplete="email"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-11 pr-12 py-3 rounded-xl bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-all"
                  placeholder="••••••••"
                  autoComplete={isRegister ? 'new-password' : 'current-password'}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <motion.button
              type="submit"
              disabled={loading}
              className={cn(
                'w-full py-3.5 rounded-xl font-semibold text-white transition-all',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                role === 'merchant'
                  ? 'bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 glow-purple'
                  : 'bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 glow-blue'
              )}
              whileHover={{ scale: loading ? 1 : 1.01 }}
              whileTap={{ scale: loading ? 1 : 0.99 }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <motion.span
                    className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
                  />
                  {isRegister ? 'Creating Account...' : 'Signing In...'}
                </span>
              ) : (
                isRegister ? 'Create Account' : 'Sign In'
              )}
            </motion.button>
          </form>

          {/* Toggle Register/Login */}
          <div className="mt-6 text-center">
            <button
              onClick={() => setIsRegister(!isRegister)}
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              {isRegister ? (
                <>Already have an account? <span className="text-blue-400">Sign in</span></>
              ) : (
                <>Don&apos;t have an account? <span className="text-blue-400">Register</span></>
              )}
            </button>
          </div>
        </div>

        {/* Security badge */}
        <div className="mt-6 text-center text-xs text-gray-600 flex items-center justify-center gap-2">
          <Lock className="w-3 h-3" />
          <span>Secured with JWT + CSRF double-submit cookies</span>
        </div>
      </motion.div>
    </div>
  );
}
