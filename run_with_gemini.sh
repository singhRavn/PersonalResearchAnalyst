#!/bin/bash
# Gemini-only setup and execution guide for Personal Research Analyst

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=========================================="
echo "Personal Research Analyst - Gemini Setup"
echo "=========================================="
echo ""

# Step 1: Check Python
echo "Step 1: Verifying Python environment..."
python3 --version
echo ""

# Step 2: Activate virtual environment
echo "Step 2: Activating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Step 3: Install dependencies
echo "Step 3: Installing dependencies..."
pip install -e . --quiet
pip install pytest pytest-asyncio --quiet
echo "✓ Dependencies installed"
echo ""

# Step 4: Configure Gemini API
echo "Step 4: Gemini API Configuration"
echo ""
echo "  You need a Google Gemini API key:"
echo "  1. Go to: https://aistudio.google.com/apikey"
echo "  2. Create or copy your API key"
echo "  3. Update .env file:"
echo ""
echo "     GOOGLE_API_KEY=your-actual-api-key-here"
echo ""

# Check if .env has been configured
if grep -q "YOUR_GEMINI_API_KEY_HERE\|your-gemini-api-key-here" .env 2>/dev/null; then
    echo "⚠ WARNING: .env not yet configured with your Gemini API key"
    echo ""
    echo "  Edit .env and replace the placeholder with your actual key"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Step 5: Test imports
echo "Step 5: Testing imports..."
python -c "from src.schemas import *; from src.memory import MemoryLayer; print('✓ Core modules import successfully')"
python -c "import httpx; print('✓ HTTP client ready')"
echo ""

# Step 6: Provide execution instructions
echo "=========================================="
echo "Setup Complete - Execution Instructions"
echo "=========================================="
echo ""
echo "To run the Personal Research Analyst with Gemini:"
echo ""
echo "Terminal 1 - Start the LLM Gateway:"
echo "  $ python -m src.llm_gatewayV3.main"
echo ""
echo "Terminal 2 - Run the agent:"
echo "  $ python -m src.agent6"
echo ""
echo "Or run tests:"
echo "  $ python -m pytest tests/test_layers.py -v"
echo ""
echo "Environment:"
echo "  - Activate venv: source .venv/bin/activate"
echo "  - Deactivate: deactivate"
echo ""
echo "Configuration Files:"
echo "  - .env              (your API keys - DO NOT commit)"
echo "  - gemini_config.py  (read-only Gemini settings)"
echo ""
