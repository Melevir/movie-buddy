.PHONY: install install-dev test lint format typecheck check clean

install:
	pip3 install -e .

install-dev:
	pip3 install -e ".[dev]"

test:
	python3 -m pytest tests/ -q

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy movie_buddy/

check: lint typecheck test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
