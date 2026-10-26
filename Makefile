# Without make, run the raw commands:
#   docker compose up -d --build --wait      (make up; copy .env.example to .env first)
#   docker compose down -v                   (make down)
#   docker compose logs -f                   (make logs)
#   docker compose run --rm api bank-credit sla-check   (make sla-check)
#   python3 scripts/smoke.py                  (make smoke; needs the stack up)
#   cd backend && uv sync && uv run pytest   (make install, make test)

.DEFAULT_GOAL := help
.PHONY: help env install lint test test-integration up demo down logs sla-check smoke

COMPOSE := docker compose

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "} /^[a-z-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

env: ## Create .env from .env.example with generated secrets (if missing)
	@test -f .env || { \
	  gen() { openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))"; }; \
	  sk=$$(gen); pw=$$(gen); \
	  sed -e "s/^SECRET_KEY=.*/SECRET_KEY=$$sk/" -e "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$$pw/" .env.example > .env; \
	  echo "Created .env with generated SECRET_KEY and POSTGRES_PASSWORD."; \
	}

install: ## Install backend (uv sync) and frontend (npm ci) dependencies
	cd backend && uv sync
	cd frontend && npm ci

lint: ## Run the CI lint checks (ruff, mypy, eslint, tsc)
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .
	cd backend && uv run mypy
	cd frontend && npm run lint
	cd frontend && npm run typecheck

test: ## Run the backend unit tests
	cd backend && uv run pytest

test-integration: env ## Run the Postgres integration tests against the compose postgres service
	@set -e; set -a; . ./.env; set +a; \
	trap '$(COMPOSE) stop postgres' EXIT; \
	$(COMPOSE) up -d --wait postgres; \
	$(COMPOSE) exec -T postgres sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -tc "SELECT 1 FROM pg_database WHERE datname = '"'"'bank_credit_test'"'"'" | grep -q 1 || psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -c "CREATE DATABASE bank_credit_test"'; \
	port=$$($(COMPOSE) port postgres 5432 | sed 's/.*://'); \
	cd backend && TEST_DATABASE_URL="postgresql+psycopg://$$POSTGRES_USER:$$POSTGRES_PASSWORD@127.0.0.1:$$port/bank_credit_test" uv run pytest -m integration -ra

up: env ## Build and start postgres, api and web, waiting for the healthchecks
	$(COMPOSE) up -d --build --wait

demo: up ## Same as up, then print the URLs and demo logins
	@echo "Web:  http://localhost:8080"
	@echo "API:  http://localhost:8000/docs"
	@echo "Demo logins: admin@example.com and the other seeded users; the password is DEMO_PASSWORD in .env."

down: ## Stop everything and delete the database volume
	$(COMPOSE) down -v

logs: ## Follow the logs of all services
	$(COMPOSE) logs -f

sla-check: ## Run the SLA check job once in the api image
	$(COMPOSE) run --rm api bank-credit sla-check

smoke: ## Register a customer and approve a request through all stages (stack must be up)
	@set -a; [ ! -f .env ] || . ./.env; set +a; python3 scripts/smoke.py
