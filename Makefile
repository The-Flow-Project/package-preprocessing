# Makefile for testing and development tasks

.PHONY: help install install-dev install-docs install-all test test-fast coverage lint format fix check clean build docs docs-serve

# Tools (run inside the uv-managed venv)
PYTEST := uv run pytest
BLACK  := uv run black
RUFF   := uv run ruff
MYPY   := uv run mypy
SPHINX := uv run sphinx-build

# Directories
SRC_DIR        := src/flow_preprocessing
TEST_DIR       := tests
DOCS_DIR       := docs
DOCS_BUILD_DIR := $(DOCS_DIR)/_build

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:
	uv sync

install-dev:
	uv sync --extra dev

install-docs:
	uv sync --extra docs

install-all:
	uv sync --all-extras

test:
	$(PYTEST) $(TEST_DIR)

test-fast:
	$(PYTEST) $(TEST_DIR) -n auto

coverage:
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term --cov-report=xml

lint:
	@echo "Running ruff..."
	$(RUFF) check $(SRC_DIR) $(TEST_DIR)
	@echo ""
	@echo "Running mypy..."
	$(MYPY) $(SRC_DIR)

format:
	@echo "Running black..."
	$(BLACK) $(SRC_DIR) $(TEST_DIR)

fix:
	@echo "Auto-fixing with ruff..."
	$(RUFF) check --fix $(SRC_DIR) $(TEST_DIR)
	@echo ""
	@echo "Running black..."
	$(BLACK) $(SRC_DIR) $(TEST_DIR)

check:
	@echo "Checking format with black..."
	$(BLACK) --check $(SRC_DIR) $(TEST_DIR)
	@echo ""
	@echo "Checking with ruff..."
	$(RUFF) check $(SRC_DIR) $(TEST_DIR)

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	rm -rf $(DOCS_BUILD_DIR)
	rm -rf logs/*.log 2>/dev/null || true
	@echo "Clean complete!"

build: clean
	uv build

docs:
	@echo "Generating documentation..."
	$(SPHINX) -b html $(DOCS_DIR) $(DOCS_BUILD_DIR)/html
	@echo "Documentation generated in $(DOCS_BUILD_DIR)/html"

docs-serve: docs
	@echo "Serving documentation on http://localhost:8000"
	cd $(DOCS_BUILD_DIR)/html && uv run python -m http.server 8000

