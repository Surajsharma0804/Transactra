.PHONY: up down build migrate seed test lint typecheck format clean

# ── Stack ────────────────────────────────────────────
up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

# ── Database ─────────────────────────────────────────
migrate:
	docker compose exec api alembic upgrade head

migrate-down:
	docker compose exec api alembic downgrade -1

migrate-create:
	docker compose exec api alembic revision --autogenerate -m "$(MSG)"

seed:
	docker compose exec api python scripts/seed_db.py

# ── Quality ──────────────────────────────────────────
test:
	docker compose exec api pytest tests/unit/ -v

test-all:
	docker compose exec api pytest -v

test-security:
	docker compose exec api pytest tests/security/ -v

test-property:
	docker compose exec api pytest tests/property/ -v

test-benchmark:
	docker compose exec api pytest tests/unit/ --benchmark-only

lint:
	docker compose exec api ruff check .

format:
	docker compose exec api ruff format .

typecheck:
	docker compose exec api mypy backend

# ── Evaluation ───────────────────────────────────────
eval:
	docker compose exec api python scripts/run_eval.py

# ── Cleanup ──────────────────────────────────────────
clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
