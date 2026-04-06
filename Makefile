.PHONY: install dev-install run test lint format clean docker-build docker-up docker-down

install:
	pip install -r requirements.txt

dev-install:
	pip install -e ".[dev]"

run:
	streamlit run src/app.py

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff check --fix src/ tests/
	ruff format src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf htmlcov .coverage dist build *.egg-info

docker-build:
	docker build -t local-llm-chatbot .

docker-up:
	docker compose up -d

docker-down:
	docker compose down
