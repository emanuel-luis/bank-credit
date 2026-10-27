# Without make, run the raw commands:
#   docker compose up -d --build --wait      (make up; copy .env.example to .env first)
#   docker compose down -v                   (make down)
#   docker compose logs -f                   (make logs)
#   docker compose run --rm api bank-credit sla-check   (make sla-check)
#   mkdir -p data/exports && docker compose run --rm --user "$(id -u):$(id -g)" -v "$PWD/data:/app/data" \
#     api bank-credit export --dataset request_events --out data/exports   (make export; AS_OF, FORMAT)
#   python3 scripts/smoke.py                  (make smoke; needs the stack up)
#   cd backend && uv sync && uv run pytest   (make install, make test)
#   d2 --scale 1 docs/diagrams/<name>.d2 docs/diagrams/<name>.svg   (make diagrams; D2 v0.9.0)

# bash for every recipe (the diagram recipes use shopt); no global .SHELLFLAGS, so the older
# recipes keep their own error handling and only the diagram recipes run with set -euo pipefail.
SHELL := bash
.DEFAULT_GOAL := help
.PHONY: help env install lint test test-integration up demo down logs sla-check export smoke \
	d2-install diagrams diagrams-check diagrams-watch

COMPOSE := docker compose
DATASET ?= request_events
FORMAT ?= csv

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

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

export: ## Export DATASET (request_events|stage_intervals|sla_breach_weekly) to ./data/exports; also AS_OF, FORMAT
	@mkdir -p data/exports
	$(COMPOSE) run --rm --user "$$(id -u):$$(id -g)" -v "$(CURDIR)/data:/app/data" api \
	  bank-credit export --dataset $(DATASET) --format $(FORMAT) --out data/exports \
	  $(if $(AS_OF),--as-of "$(AS_OF)")

smoke: ## Register a customer and approve a request through all stages (stack must be up)
	@set -a; [ ! -f .env ] || . ./.env; set +a; python3 scripts/smoke.py

# Diagrams: docs/diagrams/<name>.d2 rendered to <name>.svg (committed). One pinned D2 everywhere.
# Layout engine, themes and padding live in docs/diagrams/_style.d2 (d2-config), so d2 runs in a
# clean environment: D2_* and SCALE variables would override that config. --scale 1 is not a
# d2-config key; it writes the natural width and height, so GitHub never upscales a small diagram.
# These recipes start with `set -euo pipefail` because this Makefile sets no global .SHELLFLAGS
# (the older recipes were written without pipefail; test-integration pipes psql into grep -q).
D2_VERSION := 0.9.0
# sha256 of d2-v$(D2_VERSION)-linux-amd64.tar.gz, from the release's SHA256SUMS
D2_SHA256 := 5669ddc46b99e942cc96078f4a4e36d5e62103348f4c05179ede27802fdd87a9
D2_HOME ?= $(HOME)/.local/share/d2/v$(D2_VERSION)
D2 ?= $(D2_HOME)/bin/d2
D2_RUN = env -i PATH="$$PATH" HOME="$$HOME" "$(D2)" --scale 1
DIAGRAMS := $(filter-out docs/diagrams/_%,$(wildcard docs/diagrams/*.d2))

d2-install: ## Install the pinned D2 (Linux x86_64) into D2_HOME, checksum verified
	@set -euo pipefail; \
	if [ -x "$(D2_HOME)/bin/d2" ]; then echo "D2 v$(D2_VERSION) already in $(D2_HOME)"; exit 0; fi; \
	[ "$$(uname -sm)" = "Linux x86_64" ] || { echo "d2-install covers Linux x86_64 only;" \
		"install D2 v$(D2_VERSION) yourself and pass D2=/path/to/d2" >&2; exit 1; }; \
	tmp="$$(mktemp -d)"; trap 'rm -rf "$$tmp"' EXIT; \
	curl -fsSLo "$$tmp/d2.tar.gz" \
		"https://github.com/terrastruct/d2/releases/download/v$(D2_VERSION)/d2-v$(D2_VERSION)-linux-amd64.tar.gz"; \
	echo "$(D2_SHA256)  $$tmp/d2.tar.gz" | sha256sum --check --strict; \
	tar -xzf "$$tmp/d2.tar.gz" -C "$$tmp"; \
	mkdir -p "$(D2_HOME)/bin"; \
	install -m 0755 "$$tmp/d2-v$(D2_VERSION)/bin/d2" "$(D2_HOME)/bin/d2"; \
	"$(D2_HOME)/bin/d2" --version

diagrams: ## Render docs/diagrams/*.d2 to SVG with the pinned D2 (run make d2-install once)
	@set -euo pipefail; v="$$($(D2_RUN) --version 2>/dev/null || true)"; [ "$$v" = "v$(D2_VERSION)" ] || { \
		echo "need D2 v$(D2_VERSION) at $(D2), found '$${v:-nothing}': run make d2-install" >&2; exit 1; }
	@set -euo pipefail; for f in $(DIAGRAMS); do $(D2_RUN) "$$f" "$${f%.d2}.svg"; done

diagrams-check: diagrams ## Render, then fail if a committed SVG is stale, missing or has no source
	@set -euo pipefail; shopt -s nullglob; for s in docs/diagrams/*.svg; do \
		[ -f "$${s%.svg}.d2" ] || { echo "$$s has no .d2 source" >&2; exit 1; }; done
	@set -euo pipefail; changed="$$(git status --porcelain --untracked-files=all -- 'docs/diagrams/*.svg')"; \
	if [ -n "$$changed" ]; then echo "$$changed" >&2; \
		echo "rendered SVGs differ from the committed ones: run make diagrams and commit" >&2; exit 1; fi

diagrams-watch: ## Live preview in the browser while editing: make diagrams-watch NAME=architecture
	@# NAME only from the command line: WSL exports NAME (the hostname) into every shell.
	@[ "$(origin NAME)" = "command line" ] && [ -f "docs/diagrams/$(NAME).d2" ] || { \
		echo "usage: make diagrams-watch NAME=<one of: $(basename $(notdir $(DIAGRAMS)))>" >&2; exit 1; }
	$(D2_RUN) --watch --browser "$${BROWSER:-0}" docs/diagrams/$(NAME).d2 docs/diagrams/$(NAME).svg
