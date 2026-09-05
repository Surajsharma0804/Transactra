/**
 * Transactra — API Client
 *
 * Centralized HTTP client that handles:
 * - JWT bearer token attachment
 * - CSRF double-submit cookie
 * - Auto-logout on 401
 * - Consistent error handling
 * - Base URL configuration
 *
 * All API calls go through this client.
 */

import { useAuthStore } from './store';
import type { AuthTokens } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

// ── Error class ─────────────────────────────────────

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

// ── Core fetch wrapper ──────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = useAuthStore.getState().token;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  // Attach JWT bearer token if authenticated
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Attach CSRF token from cookie if available
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: 'include', // Send cookies for CSRF
  });

  // Auto-logout on 401
  if (response.status === 401) {
    useAuthStore.getState().logout();
    throw new ApiError(401, 'Session expired. Please login again.');
  }

  // Handle non-JSON error responses
  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const errorBody = await response.json();
      detail = errorBody.detail || detail;
    } catch {
      // Response wasn't JSON
    }
    throw new ApiError(response.status, detail);
  }

  // Parse JSON response
  return response.json();
}

// ── CSRF token from cookie ──────────────────────────

function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : null;
}

// ── Auth API ────────────────────────────────────────

export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<AuthTokens>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (email: string, password: string, name: string, role: string) =>
    apiFetch<AuthTokens>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name, role }),
    }),

  logout: () =>
    apiFetch<void>('/auth/logout', { method: 'POST' }),

  refresh: () =>
    apiFetch<AuthTokens>('/auth/refresh', { method: 'POST' }),
};

// ── Products API ────────────────────────────────────

export const productsApi = {
  search: (query: string, maxResults = 20) =>
    apiFetch<{ products: any[]; total: number }>(`/catalog/search?q=${encodeURIComponent(query)}&max_results=${maxResults}`),

  getAll: () =>
    apiFetch<{ products: any[]; total: number }>('/catalog/products'),

  create: (product: any) =>
    apiFetch<any>('/catalog/products', {
      method: 'POST',
      body: JSON.stringify(product),
    }),
};

// ── Mandates API ────────────────────────────────────

export const mandatesApi = {
  create: (mandate: any) =>
    apiFetch<any>('/mandates', {
      method: 'POST',
      body: JSON.stringify(mandate),
    }),

  get: (mandateId: string) =>
    apiFetch<any>(`/mandates/${mandateId}`),

  createConsent: (mandateId: string, consent: any) =>
    apiFetch<any>(`/mandates/${mandateId}/consent`, {
      method: 'POST',
      body: JSON.stringify(consent),
    }),
};

// ── Orders API ──────────────────────────────────────

export const ordersApi = {
  create: (order: any) =>
    apiFetch<any>('/orders', {
      method: 'POST',
      body: JSON.stringify(order),
    }),

  get: (orderId: string) =>
    apiFetch<any>(`/orders/${orderId}`),

  initiatePayment: (orderId: string, payment: any) =>
    apiFetch<any>(`/orders/${orderId}/payment`, {
      method: 'POST',
      body: JSON.stringify(payment),
    }),

  getProof: (orderId: string) =>
    apiFetch<any>(`/orders/${orderId}/proof`),
};

// ── Authorization API ───────────────────────────────

export const authorizationApi = {
  authorize: (request: any) =>
    apiFetch<any>('/authorize', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  getDecision: (decisionId: string) =>
    apiFetch<any>(`/authorize/${decisionId}`),
};

// ── Negotiation API ─────────────────────────────────

export const negotiationApi = {
  submitOffer: (offer: any) =>
    apiFetch<any>('/negotiate', {
      method: 'POST',
      body: JSON.stringify(offer),
    }),
};

// ── Razorpay Config ─────────────────────────────────

export const configApi = {
  getRazorpay: () =>
    fetch(`${API_BASE.replace('/api/v1', '')}/config/razorpay`)
      .then(r => r.json()),
};

// ── MCP Tools API ───────────────────────────────────

export const mcpApi = {
  listTools: (capabilities = '') =>
    apiFetch<any>(`/mcp/tools?capabilities=${capabilities}`),

  invokeTool: (toolName: string, request: any) =>
    apiFetch<any>(`/mcp/tools/${toolName}/invoke`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),
};
