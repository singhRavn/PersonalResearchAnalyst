#!/bin/bash
# Installation and test execution script for Personal Research Analyst

set -e  # Exit on error

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=========================================="
echo "Personal Research Analyst - Setup & Test"
echo "=========================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python: $python_version"
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "✓ Activating existing virtual environment..."
    source .venv/bin/activate
else
    echo "✓ Creating new virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
fi
echo ""

# Upgrade pip
echo "✓ Upgrading pip..."
pip install --upgrade pip --quiet
echo ""

# Install dependencies
echo "✓ Installing project dependencies..."
pip install -e . --quiet
echo "  Dependencies installed:"
pip list | grep -E "pydantic|httpx|tavily|crawl4ai|ddgs|python-dotenv|openai|mcp" || echo "  (core packages ready)"
echo ""

# Install dev dependencies
echo "✓ Installing dev dependencies..."
pip install pytest pytest-asyncio --quiet
echo ""

# Create necessary directories
echo "✓ Creating state directories..."
mkdir -p state/traces
echo ""

# Run tests
echo "=========================================="
echo "Running Tests"
echo "=========================================="
echo ""

if [ -f "tests/test_layers.py" ]; then
    echo "✓ Running unit tests..."
    python -m pytest tests/test_layers.py -v --tb=short
    echo ""
else
    echo "⚠ No test file found at tests/test_layers.py"
fi

echo ""
echo "=========================================="
echo "Setup Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Set up your LLM gateway at http://localhost:8101"
echo "2. Configure .env with API keys (see .env.example)"
echo "3. Run the agent with: python -m src.agent6"
echo ""
echo "Virtual environment: source .venv/bin/activate"
echo ""
