# Transactra
## The Trust Infrastructure for Agentic Commerce

> **Core thesis:** AI proposes; deterministic infrastructure verifies authority, policy, consent, exact-cart binding, idempotency and provider evidence before any financial effect can occur.

### Architecture

```
USER → BUYER AGENT → TYPED INTENT → AUTHORIZATION GATE → PAYMENT ADAPTER → RAZORPAY
                                          ↑
                         Commerce Kernel (deterministic)
                    Policy · Consent · State · Idempotency · Evidence
```

**Intelligence is replaceable; authority is deterministic.**

### Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/Surajsharma0804/Transactra.git
cd Transactra
cp .env.example .env
# Fill in your API keys in .env

# 2. Boot the stack
docker compose up --build

# 3. Run migrations
make migrate

# 4. Seed demo data
make seed

# 5. Run tests
make test
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ · FastAPI · Pydantic v2 |
| Database | PostgreSQL 16 · pgvector |
| Cache | Redis 7 |
| Payments | Razorpay Test Mode |
| AI | OpenAI (structured output) |
| Frontend | Next.js · TypeScript |
| Infra | Docker Compose · GitHub Actions |

### Non-Negotiable Invariants

1. Financial amounts are integers in paise — no floating point
2. Every money action has authenticated principal + active authority
3. Every decision is ALLOW/DENY with rule IDs and reasons
4. Expired/revoked agents cannot authorize
5. Child authority ⊆ parent authority (delegation never escalates)
6. Cart change invalidates consent
7. Payment idempotency enforced by database uniqueness
8. Order state and payment state are separate machines
9. Only verified provider webhook can transition to paid
10. Replay/simulation cannot reach payment execution

### Security

See [SECURITY.md](SECURITY.md) for threat model and responsible disclosure.

### License

MIT
