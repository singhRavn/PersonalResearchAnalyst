# Personal Research Analyst - Gemini Quick Start

## Setup (5 minutes)

### 1. Get Gemini API Key
- Visit: https://aistudio.google.com/apikey
- Create a new API key (free tier available)
- Copy the key

### 2. Configure Environment
Edit `.env` and add your key:
```
GOOGLE_API_KEY=your-actual-api-key-here
```

### 3. Install & Test
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -e .
pip install pytest pytest-asyncio

# Run tests
python -m pytest tests/test_layers.py -v
```

## Execution

### Terminal 1: Start LLM Gateway
```bash
source .venv/bin/activate
python -m src.llm_gatewayV3.main
```
Expected output: `INFO: Uvicorn running on http://0.0.0.0:8101`

### Terminal 2: Run Agent
```bash
source .venv/bin/activate
python -m src.agent6
```

## Architecture

The system uses **Gemini only** (no fallback providers):

```
User Query
    ↓
Perception Layer (analyze & extract intent)
    ↓
Memory Layer (retrieve relevant facts)
    ↓
Decision Layer (choose next action)
    ↓
Action Layer (execute tool or finish)
    ↓
Gemini API (via llm_gatewayV3)
```

## Models Used

| Layer | Model | Temperature | Purpose |
|-------|-------|-------------|---------|
| Perception | gemini-2.0-flash | 0.1 | Deterministic analysis |
| Decision | gemini-2.0-flash | 0.0 | Deterministic action choice |
| General | gemini-2.0-flash | 0.7 | Flexible responses |

## Available Tools

The agent can use these tools:
- `search_web` - Search the internet (via Tavily)
- `crawl_url` - Extract content from URLs (via crawl4ai)
- `read_memory` - Retrieve stored facts
- `write_memory` - Store important findings
- `finish` - End research and return answer

## Troubleshooting

### "Could not connect to gateway"
```
Error: Failed to connect to http://localhost:8101
```
Solution: Ensure Terminal 1 is running the gateway and showing "Uvicorn running"

### "Invalid API key"
```
Error: 401 Unauthorized
```
Solution: Check `.env` has correct `GOOGLE_API_KEY` without spaces or quotes

### "Rate limited"
Gemini has free tier limits:
- **Requests Per Minute (RPM)**: 15
- **Requests Per Day (RPD)**: 1,000
- **Tokens Per Minute (TPM)**: 250,000

Solution: Wait before making new requests, or upgrade to paid tier

## Testing

Run unit tests:
```bash
python -m pytest tests/test_layers.py -v
```

Run a single test:
```bash
python -m pytest tests/test_layers.py::TestMemoryLayer::test_memory_set_get -v
```

## Files Changed for Gemini-Only Setup

✓ **Removed**: References to other providers (OpenAI, Anthropic, etc.)
✓ **Added**: `gemini_config.py` - Configuration reference
✓ **Updated**: `.env.example` - Template with GOOGLE_API_KEY only
✓ **Fixed**: 3 duplicate imports in perception.py, decision.py, action.py
✓ **Created**: `tests/test_layers.py` - Unit tests for core layers
✓ **Created**: `run_with_gemini.sh` - Setup script

## Environment Variables

```bash
# Required
GOOGLE_API_KEY=your-api-key

# Optional (defaults set in code)
GATEWAY_V3_PORT=8101          # Default: 8101
LLM_ORDER=gemini              # Default: gemini (only)
ROUTER_ORDER=gemini           # Default: gemini (only)
```

## Next Steps

1. ✓ Code fixed and tested
2. ✓ Gemini-only configuration created
3. → Configure `.env` with your API key
4. → Start gateway in Terminal 1
5. → Run agent in Terminal 2
6. → Ask your research question!

---

**System Design**: Production-grade cognitive architecture with strict separation of concerns, typed contracts, and observable execution flow.
