.PHONY: all install test clean lint run push help

# Default target
all: install test

# Install dependencies and package
install:
	pip install -e .

# Install dev dependencies
dev:
	pip install -e ".[test]" pytest pytest-cov black flake8

# Run tests
test:
	pytest -v

# Run tests with coverage
test-cov:
	pytest --cov=tenderctl --cov-report=html --cov-report=term

# Lint code
lint:
	flake8 tenderctl tests
	black --check tenderctl tests

# Format code
fmt:
	black tenderctl tests

# Clean generated files
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run the CLI
run:
	python -m tenderctl.cli --help

# Push to GitHub
push: test
	git add -A
	git commit -m "feat: tenderctl CLI implementation"
	git push origin main

# Show help
help:
	@echo "tenderctl Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  install     Install the package"
	@echo "  dev         Install with dev dependencies"
	@echo "  test        Run tests"
	@echo "  test-cov    Run tests with coverage"
	@echo "  lint        Lint code"
	@echo "  fmt         Format code"
	@echo "  clean       Clean generated files"
	@echo "  run         Run the CLI"
	@echo "  push        Commit and push to GitHub"
	@echo "  help        Show this help"
