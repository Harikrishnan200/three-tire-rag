.PHONY: setup up down logs test lint format migrate seed clean

VENV := .venv/bin

setup:
	python3 -m venv .venv
	$(VENV)/pip install --upgrade pip
	$(VENV)/pip install -e ".[dev]"
	$(VENV)/python -m spacy download en_core_web_sm || true

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

test:
	$(VENV)/python -m pytest tests/ -v

lint:
	$(VENV)/ruff check app tests
	$(VENV)/mypy app || true

format:
	$(VENV)/black app tests
	$(VENV)/ruff check --fix app tests

migrate:
	$(VENV)/alembic upgrade head

seed:
	$(VENV)/python scripts/seed_data.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache
