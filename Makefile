# Makefile for testing and development tasks

.PHONY: help test test-unit test-integration test-all test-verbose test-coverage clean lint format install

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install package in development mode
	pip install -e .
	pip install pytest pytest-asyncio pytest-cov

test:  ## Run all unit tests (fast)
	pytest -m "not integration" -v

test-unit:  ## Run unit tests only
	pytest tests/unit_tests/ -v

test-integration:  ## Run integration tests only
	pytest -m integration -v

test-all:  ## Run all tests including integration
	pytest -v

test-verbose:  ## Run tests with maximum verbosity
	pytest -vv -s

test-coverage:  ## Run tests with coverage report
	pytest --cov=src/flow_preprocessor --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

test-watch:  ## Run tests in watch mode (requires pytest-watch)
	pytest-watch

test-file:  ## Run specific test file (usage: make test-file FILE=test_config.py)
	pytest tests/unit_tests/$(FILE) -v

clean:  ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build

lint:  ## Run linting checks
	@command -v ruff >/dev/null 2>&1 && ruff check src/ tests/ || echo "ruff not installed"
	@command -v mypy >/dev/null 2>&1 && mypy src/ || echo "mypy not installed"

format:  ## Format code with black
	@command -v black >/dev/null 2>&1 && black src/ tests/ || echo "black not installed"

check:  ## Run all checks (lint + tests)
	make lint
	make test

.DEFAULT_GOAL := help

