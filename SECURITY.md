# Security Policy — Transactra

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email: security@transactra.dev (or contact the repository owner directly)
3. Include: description, reproduction steps, impact assessment

## Security Principles

- **Fail closed**: Unknown state → DENY, never ALLOW
- **Least privilege**: Agents get only the capabilities they need
- **Defense in depth**: Multiple layers of validation
- **Explicit trust boundaries**: User → Agent → Kernel → Payment
- **Immutable evidence**: Audit trail cannot be retroactively altered

## What Is Trusted

| Component | Trust Level |
|-----------|-------------|
| Commerce Kernel | Trusted — deterministic authority |
| Constraint Solver | Trusted code — bounded inputs |
| User (for consent) | Trusted for intent/approval |
| Buyer Agent | **Untrusted** for money |
| Merchant Agent | **Untrusted** for money |
| External AI Agent | **Untrusted** — same gates apply |
| Product descriptions | **Untrusted data** — never authority |
| Webhook (before verification) | **Untrusted** until signature verified |

## Secrets

- Never commit `.env`, API keys, or signing keys
- Use `git-secrets` or equivalent pre-commit scanning
- Razorpay Test Mode keys are non-production but still treated as secrets
- JWT secrets must be cryptographically random, minimum 256 bits

## Known Attack Vectors and Mitigations

| Attack | Mitigation |
|--------|-----------|
| Prompt injection via product description | Untrusted-data boundary; descriptions are DATA not authority |
| Budget escalation via agent | Amount bound + 16-predicate authorization gate |
| Forged webhook | Raw-body signature verification before any state mutation |
| Replay attack | Authorization nonce (unique, random, consumed on use) |
| Duplicate payment | Idempotency key (unique DB constraint) |
| Delegation escalation | Subset check: ChildAuthority ⊆ ParentAuthority |
| Expired mandate use | Expiry checked in authorization gate |
| Client-side payment forgery | Only verified webhook sets authoritative payment state |
