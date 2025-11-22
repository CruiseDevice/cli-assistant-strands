#!/bin/bash
# Run all tests with coverage

set -e

echo "🧪 Running test suite..."

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Run ./scripts/setup.sh first"
    exit 1
fi

# Run linting
echo "Running flake8..."
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true

# Run type checking
echo "Running mypy..."
mypy cli_assistant.py --ignore-missing-imports || true

# Run tests
echo "Running pytest..."
pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

# Check coverage threshold
coverage_percentage=$(coverage report | tail -1 | awk '{print $NF}' | sed 's/%//')

if (( $(echo "$coverage_percentage < 70" | bc -l 2>/dev/null || echo "0") )); then
    echo "⚠️  Coverage is below 70%: ${coverage_percentage}%"
else
    echo "✅ Coverage OK: ${coverage_percentage}%"
fi

echo ""
echo "View detailed coverage report: open htmlcov/index.html"
