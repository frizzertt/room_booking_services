.PHONY: up down test seed install

up:
	docker compose up --build

down:
	docker compose down -v

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements-dev.txt

test:
	.venv/bin/pytest -q --cov=app --cov-report=term-missing

seed:
	docker compose exec api python -m scripts.seed
