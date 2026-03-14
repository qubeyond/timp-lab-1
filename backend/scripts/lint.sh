#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "Running Ruff linter..."
uv run ruff check . --fix

echo "Running Ruff formatter..."
uv run ruff format .

# echo "Running Mypy type check..."
# uv run mypy .

echo "All backend checks passed!"