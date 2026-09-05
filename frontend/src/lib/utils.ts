/**
 * Transactra — Utility Functions
 *
 * Formatters, validators, and helpers used across the frontend.
 */

// ── Money Formatting ────────────────────────────────

/**
 * Format paise to Indian Rupee display string.
 * 100000 → "₹1,000.00"
 */
export function formatPaise(paise: number): string {
  const rupees = paise / 100;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(rupees);
}

/**
 * Format paise to compact form.
 * 100000 → "₹1K"
 */
export function formatPaiseCompact(paise: number): string {
  const rupees = paise / 100;
  if (rupees >= 10_000_000) return `₹${(rupees / 10_000_000).toFixed(1)}Cr`;
  if (rupees >= 100_000) return `₹${(rupees / 100_000).toFixed(1)}L`;
  if (rupees >= 1_000) return `₹${(rupees / 1_000).toFixed(1)}K`;
  return `₹${rupees.toFixed(0)}`;
}

/**
 * Convert rupees string to paise integer.
 * "1000.50" → 100050
 */
export function rupeesToPaise(rupees: string | number): number {
  const num = typeof rupees === 'string' ? parseFloat(rupees) : rupees;
  return Math.round(num * 100);
}

// ── Date/Time Formatting ────────────────────────────

/**
 * Format ISO timestamp to human-readable string.
 */
export function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

/**
 * Format ISO timestamp to relative time.
 * "2 hours ago", "just now", etc.
 */
export function formatRelativeTime(iso: string): string {
  const now = Date.now();
  const then = new Date(iso).getTime();
  const diffMs = now - then;
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec < 60) return 'just now';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  if (diffSec < 604800) return `${Math.floor(diffSec / 86400)}d ago`;
  return formatTimestamp(iso);
}

// ── String Utilities ────────────────────────────────

/**
 * Truncate hash for display.
 * "abc123def456" → "abc1...f456"
 */
export function truncateHash(hash: string, chars = 4): string {
  if (hash.length <= chars * 2 + 3) return hash;
  return `${hash.slice(0, chars)}...${hash.slice(-chars)}`;
}

/**
 * Capitalize first letter.
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Generate a UUID v4.
 */
export function generateUUID(): string {
  return crypto.randomUUID();
}

// ── Validation ──────────────────────────────────────

export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function isValidPassword(password: string): boolean {
  return password.length >= 8;
}

// ── Status Colors ───────────────────────────────────

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    active: 'text-emerald-400 bg-emerald-400/10',
    approved: 'text-emerald-400 bg-emerald-400/10',
    completed: 'text-emerald-400 bg-emerald-400/10',
    paid: 'text-emerald-400 bg-emerald-400/10',
    captured: 'text-emerald-400 bg-emerald-400/10',

    pending: 'text-amber-400 bg-amber-400/10',
    initiated: 'text-amber-400 bg-amber-400/10',
    payment_pending: 'text-amber-400 bg-amber-400/10',
    created: 'text-blue-400 bg-blue-400/10',

    failed: 'text-red-400 bg-red-400/10',
    denied: 'text-red-400 bg-red-400/10',
    revoked: 'text-red-400 bg-red-400/10',
    cancelled: 'text-red-400 bg-red-400/10',
    expired: 'text-gray-400 bg-gray-400/10',
    exhausted: 'text-orange-400 bg-orange-400/10',
  };
  return colors[status.toLowerCase()] || 'text-gray-400 bg-gray-400/10';
}

// ── Trust Score Color ───────────────────────────────

export function getTrustColor(score: number): string {
  if (score >= 0.8) return 'text-emerald-400';
  if (score >= 0.6) return 'text-amber-400';
  return 'text-red-400';
}

// ── Class Name Merge ────────────────────────────────

export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(' ');
}
