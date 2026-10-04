.DEFAULT_GOAL := help
UV ?= uv
PNPM ?= pnpm
DOCKER ?= docker
RUN = $(UV) run --frozen --offline

.PHONY: help setup dev-db dev-api dev-web lint typecheck test-unit check-contract check \
        migrate dev-worker schema test-integration test-e2e benchmark release-check

help:
	@echo MS-001: setup dev-db dev-api lint typecheck test-unit check-contract check
	@echo Requires uv 0.12.23, Python 3.12, Node 22.12+ or 24, pnpm 10.32.1, GNU Make.
	@echo Docker Compose is required for dev-db. Configure local secrets in .env.
	@echo Web shell MS-004, migrations MS-007, workers MS-016 and release gates are later tasks.

setup:
	$(UV) sync --frozen --python 3.12
	$(PNPM) --dir frontend install --frozen-lockfile
	@echo Installed frozen dependencies. Set POSTGRES_PASSWORD in .env, then make dev-db.
	@echo Development API has no routes until MS-003. No provider is enabled by default.

dev-db:
	$(DOCKER) compose up --detach --wait postgres

dev-api:
	$(RUN) uvicorn benefitbridge.main:create_app --factory --reload --host 127.0.0.1 --port 8000

dev-web:
	$(RUN) python -c "from pathlib import Path; import sys; sys.exit('BLOCKED: web shell belongs to MS-004') if not Path('frontend/index.html').is_file() else None"
	$(PNPM) --dir frontend dev

lint:
	$(RUN) ruff check backend tests
	$(RUN) ruff format --check backend tests
	$(PNPM) --dir frontend lint

typecheck:
	$(RUN) mypy
	$(PNPM) --dir frontend typecheck

test-unit:
	$(RUN) pytest tests/foundation/test_config.py tests/foundation/test_main.py
	$(PNPM) --dir frontend test

# MS-002/003/005 extend this gate with generated domain and route contracts.
check-contract:
	$(RUN) pytest tests/foundation/test_scaffold.py

check: lint typecheck test-unit check-contract

# Absent work is a failing gate, never a successful no-op.
migrate dev-worker schema test-integration test-e2e benchmark release-check:
	$(RUN) python -c "import sys; sys.exit('BLOCKED: $@ requires its owning downstream sprint; see agent.md and sprints.md')"
