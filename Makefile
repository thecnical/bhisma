.PHONY: help install install-dev test lint format clean docs docker-build docker-run dashboard setup

PYTHON := python3
PIP := pip3

help:  ## Show this help message
	@echo "Bhisma Framework - Make Commands"
	@echo "================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install Bhisma
	$(PIP) install -e .

install-dev:  ## Install development dependencies
	$(PIP) install -e ".[dev]"
	pre-commit install

test:  ## Run all tests
	pytest -v --tb=short

test-cov:  ## Run tests with coverage
	pytest --cov=bhisma --cov-report=html --cov-report=term

lint:  ## Run linters
	flake8 bhisma/ tests/
	black --check bhisma/ tests/
	isort --check-only bhisma/ tests/

format:  ## Format code
	black bhisma/ tests/
	isort bhisma/ tests/

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docs:  ## Build documentation
	@echo "Documentation is in docs/ directory"
	@echo "Open docs/01-overview.md to start"

setup:  ## Run initial setup
	bhisma setup

dashboard:  ## Launch web dashboard
	bhisma dashboard --port 8080

docker-build:  ## Build Docker image
	docker build -t bhisma:latest .

docker-run:  ## Run Docker container
	docker-compose up -d

docker-stop:  ## Stop Docker container
	docker-compose down

release: clean  ## Prepare release
	$(PYTHON) setup.py sdist bdist_wheel

all: install-dev test lint  ## Full setup and test
