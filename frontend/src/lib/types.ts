/**
 * Transactra — TypeScript Type Definitions
 *
 * Shared interfaces for the entire frontend.
 * Maps 1:1 with the FastAPI Pydantic models.
 */

// ── Auth ────────────────────────────────────────────

export type UserRole = 'buyer' | 'merchant';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  role: UserRole;
}

// ── Products ────────────────────────────────────────

export interface Product {
  sku: string;
  title: string;
  description: string;
  price_paise: number;
  currency: string;
  category: string;
  merchant_id: string;
  merchant_name: string;
  in_stock: boolean;
  image_url?: string;
}

export interface ProductSearchResult {
  products: Product[];
  total: number;
  query: string;
}

// ── Cart ────────────────────────────────────────────

export interface CartItem {
  product: Product;
  quantity: number;
}

export interface Cart {
  items: CartItem[];
  total_paise: number;
  cart_hash: string;
}

// ── Mandate ─────────────────────────────────────────

export type MandateType = 'one_time' | 'daily' | 'weekly' | 'monthly';
export type MandateStatus = 'active' | 'exhausted' | 'expired' | 'revoked';

export interface Mandate {
  mandate_id: string;
  user_id: string;
  agent_id: string;
  mandate_type: MandateType;
  status: MandateStatus;
  max_amount_paise: number;
  used_amount_paise: number;
  remaining_paise: number;
  currency: string;
  allowed_categories: string[];
  allowed_merchant_ids: string[] | null;
  valid_from: string;
  valid_until: string | null;
  created_at: string;
}

export interface CreateMandateRequest {
  user_id: string;
  agent_id: string;
  mandate_type: MandateType;
  max_amount_paise: number;
  currency: string;
  allowed_categories: string[];
  allowed_merchant_ids?: string[];
  valid_from?: string;
  valid_until?: string;
}

// ── Consent ─────────────────────────────────────────

export interface Consent {
  consent_id: string;
  user_id: string;
  mandate_id: string;
  cart_hash: string;
  amount_paise: number;
  currency: string;
  status: string;
  created_at: string;
}

// ── Orders ──────────────────────────────────────────

export type OrderStatus = 'created' | 'payment_pending' | 'paid' | 'fulfilled' | 'cancelled';

export interface Order {
  order_id: string;
  user_id: string;
  status: OrderStatus;
  total_paise: number;
  currency: string;
  cart_hash: string;
  created_at: string;
  evidence_chain_length: number;
}

export interface Payment {
  payment_id: string;
  order_id: string;
  amount_paise: number;
  currency: string;
  local_state: string;
  provider_confirmed_state: string | null;
  provider_order_id: string | null;
  is_paid: boolean;
  needs_reconciliation: boolean;
  created_at: string;
}

// ── Authorization ───────────────────────────────────

export interface PredicateResult {
  rule_id: string;
  passed: boolean;
  reason: string;
}

export interface AuthorizationDecision {
  decision_id: string;
  request_id: string;
  allowed: boolean;
  failed_rule_id: string | null;
  failed_reason: string | null;
  rule_count: number;
  rule_trail: PredicateResult[];
  snapshot: Record<string, unknown>;
  timestamp: string;
}

// ── Negotiation ─────────────────────────────────────

export interface NegotiationOffer {
  product_sku: string;
  offer_price_paise: number;
  message: string;
}

export interface NegotiationResult {
  accepted: boolean;
  counter_price_paise: number | null;
  message: string;
  savings_paise: number;
}

// ── Trust Evidence ──────────────────────────────────

export interface TrustEvidence {
  merchant_id: string;
  trust_score: number;
  fulfillment_rate: number;
  on_time_rate: number;
  dispute_rate: number;
  chain_integrity_rate: number;
  total_orders: number;
  completed_orders: number;
  computed_at: string;
}

// ── Evidence Chain ──────────────────────────────────

export interface EvidenceRecord {
  index: number;
  event_type: string;
  timestamp: string;
  data: Record<string, unknown>;
  hash: string;
  prev_hash: string;
}

export interface EvidenceProof {
  order_id: string;
  chain_length: number;
  chain_valid: boolean;
  records: EvidenceRecord[];
  root_hash: string;
}

// ── MCP Tools ───────────────────────────────────────

export interface MCPTool {
  name: string;
  description: string;
  required_capabilities: string[];
  max_results: number;
  timeout_seconds: number;
  idempotent: boolean;
  destructive: boolean;
  parameters: Array<{
    name: string;
    type: string;
    description: string;
    required: boolean;
  }>;
}

// ── Razorpay ────────────────────────────────────────

export interface RazorpayConfig {
  key_id: string;
  configured: boolean;
}

// ── Utility Types ───────────────────────────────────

/** Format paise to human-readable INR string */
export type PaiseAmount = number;

/** ISO 8601 timestamp string */
export type ISOTimestamp = string;
