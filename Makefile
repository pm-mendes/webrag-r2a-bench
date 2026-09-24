.DEFAULT_GOAL := help
UV ?= uv
WORKERS ?= 2

.PHONY: help install lint format typecheck test cov check dry-run demo clean

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

install: ## Create .venv from uv.lock and install pre-commit hooks
	$(UV) sync --locked
	$(UV) run pre-commit install

lint: ## Ruff lint and format check
	$(UV) run ruff check .
	$(UV) run ruff format --check .

format: ## Apply ruff formatting and safe fixes
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

typecheck: ## mypy (strict)
	$(UV) run mypy

test: ## Unit and integration tests
	$(UV) run pytest -q

cov: ## Tests with coverage report
	$(UV) run pytest -q --cov

check: lint typecheck test ## Everything CI runs, except the dry run

dry-run: ## 5 tasks x 2 conditions, stub generator
	$(UV) run webrag-bench run config/plans/dry-run.yaml --workers $(WORKERS)

demo: ## Every factor, 600 episodes, stub generator
	$(UV) run webrag-bench run config/plans/demo-factors.yaml --workers $(WORKERS)

clean: ## Remove run outputs and caches
	rm -rf runs .pytest_cache .mypy_cache .ruff_cache .coverage
