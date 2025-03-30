# Justfile for scrollshot2pdf project

# Default recipe to run when just is called without arguments
default:
    @just --list

# Install dependencies and pre-commit hooks
setup:
    uv sync --frozen
    uv run --dev pre-commit install

# Run all checks: linting, type checking, and tests
check: lint typecheck test
    @echo "All checks passed!"

# Format code with ruff
format:
    uv run --dev ruff format .
    uv run --dev ruff check --fix-only .

# Like format, but also shows unfixable issues that need manual attention
fix:
    uv run --dev ruff format .
    uv run --dev ruff check --fix --unsafe-fixes .

# Verify code quality without modifying files
lint:
    uv run --dev ruff check .

# Run tests with pytest
test *ARGS:
    uv run --dev pytest {{ARGS}}

# Run type checking with pyright
typecheck:
    uv run --dev pyright .
