# Backend linting and formatting scripts

# Format code with black
format:
	black src/ tests/

# Lint with ruff
lint:
	ruff check src/ tests/

# Fix linting issues automatically
lint-fix:
	ruff check --fix src/ tests/

# Run both formatting and linting
check: format lint

# Run all checks and fixes
fix: format lint-fix

# Run tests
test:
	pytest tests/ -v

# Run contract tests only
test-contract:
	pytest tests/contract/ -v

# Run integration tests only
test-integration:
	pytest tests/integration/ -v

.PHONY: format lint lint-fix check fix
