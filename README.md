# Personal Research Analyst

A production-grade cognitive agent system for autonomous research with deterministic orchestration, typed contracts, and bounded reasoning.

## Overview

Personal Research Analyst is a sophisticated AI agent designed to conduct iterative, transparent research workflows. Unlike simple chatbots or one-shot summarizers, this agent implements a genuine cognitive architecture with separate layers for perception, decision, action, and memory - all communicating through strictly typed contracts.

The system is designed to be:
- **Deterministic**: Predictable behavior with bounded iterations
- **Typed**: All layer boundaries use Pydantic v2 models
- **Modular**: Clear separation of concerns between cognitive layers
- **Convergent**: Guaranteed to finish within maximum iterations
- **Observable**: Complete tracing of all internal states
- **Maintainable**: Clean, production-grade code structure

## Architecture

The agent implements exactly four cognitive layers plus an orchestrator:

```
User Query
    ↓
Perception Layer  → Understands intent, identifies knowledge gaps
    ↓
Decision Layer    → Selects exactly ONE next action
    ↓
Action Layer      → Executes tools (search, crawl, memory)
    ↓
Observation       → Results from action execution
    ↓
Memory Layer      → Updates durable storage
    ↓
Repeat (max 6 iterations) until done
```

### Layers

1. **Memory Layer** (`memory.py`) - Durable storage of user preferences and facts using JSON persistence
2. **Perception Layer** (`perception.py`) - Understands user intent, summarizes known facts, identifies knowledge gaps
3. **Decision Layer** (`decision.py`) - Selects exactly one next action to minimize iterations and avoid repetition
4. **Action Layer** (`action.py`) - Executes MCP tools and performs side effects (the only layer allowed to do so)
5. **Orchestrator** (`agent6.py`) - Implements the main cognitive loop

## Key Features

- **Durable Memory**: Remembers user preferences across sessions (e.g., "Remember I prefer Python-first frameworks")
- **Bounded Reasoning**: Maximum 6 iterations prevents runaway execution
- **Duplicate Action Protection**: Tracks action fingerprints to prevent infinite loops
- **Structured LLM Calls**: All LLM interactions go through llm_gatewayV3 with schema validation
- **MCP Tool Integration**: Uses existing mcp_server.py for web search and crawling
- **Production Observability**: Complete trace logging to state/traces/
- **Typed Contracts**: Pydantic v2 models at every layer boundary
- **Deterministic Temperatures**: Perception (0.1), Decision (0.0) for predictable outputs

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- API keys for OpenAI and Tavily

### Installation

1. Clone or copy this repository
2. Install dependencies:
   ```bash
   uv sync
   ```

3. Create your `.env` file from the example:
   ```bash
   cp .env.example .env
   # Edit .env to add your API keys:
   ```

### MCP Server Setup

The system uses the existing MCP server for tool execution:

```bash
# In one terminal, start the MCP server:
uv run python mcp_server.py

# In another terminal, run the agent:
uv run python agent6.py "Your research query here"
```

## Usage Examples

### Basic Research Query

```bash
uv run python agent6.py "Find the latest open-source browser agents and compare architectures."
```

### Using Durable Memory

First session:
```bash
uv run python agent6.py "Remember I prefer Python-first frameworks."
```

Second session:
```bash
uv run python agent6.py "What framework should I use for my new web project?"
# The agent will recall your Python preference and recommend accordingly
```

### Complex Research Tasks

```bash
uv run python agent6.py "Which browser agent supports multimodal planning?"
uv run python agent6.py "What changed in AI coding agents this week?"
uv run python agent6.py "Compare OpenHands vs Devin vs Cursor."
```

## Output and Tracing

The agent saves detailed traces of its reasoning process:

- **Traces**: Located in `state/traces/` as JSON files
- **Memory**: Persistent storage in `state/memory.json`
- **Each trace contains**:
  - Perception layer output (understanding, gaps, confidence)
  - Decision layer output (chosen action, reasoning)
  - Action execution results
  - Memory state before/after
  - Conversation history

## Project Structure

```
personal-research-analyst/
│
├── agent6.py              # Main orchestrator
├── schemas.py             # All Pydantic v2 contracts
├── memory.py              # Durable memory layer
├── perception.py          # Perception layer
├── decision.py            # Decision layer
├── action.py              # Action layer (MCP tool execution)
├── llm_gateway.py         # Wrapper for llm_gatewayV3
├── mcp_server.py          # Existing MCP server (reused and extended)
├── pyproject.toml         # Project configuration and dependencies
├── README.md              # This file
├── .env.example           # Template for environment variables
│
├── prompts/               # Layer-specific prompts
│   ├── perception.md
│   └── decision.md
│
├── state/                 # Runtime state (gitignored)
│   ├── memory.json        # Durable memory storage
│   └── traces/            # Execution trace logs
│
└── llm_gatewayV3/         # Existing LLM gateway (reused)
    ├── gateway.py
    ├── main.py
    ├── schemas.py
    └── ...
```

## Design Principles

### Strict Architectural Rules

1. **NO** LangChain, LangGraph, CrewAI, AutoGen, or similar frameworks
2. **NO** regex parsing of LLM outputs - only structured outputs
3. **NO** direct SDK calls outside the LLM gateway
4. **NO** direct tool execution outside MCP - all side effects through action.py
5. **NO** free-form dict communication - only typed Pydantic models
6. **Decision layer emits exactly ONE action** only
7. **Memory must persist across runs** using file-based storage

### Engineering Characteristics

- **Deterministic**: Same inputs produce same observable behavior
- **Typed**: Rigorous contracts between all components
- **Modular**: Each layer has a single, well-defined responsibility
- **Convergent**: Guaranteed to finish within bounded iterations
- **Observable**: Complete internal state available for inspection
- **Maintainable**: Clear separation of concerns, minimal coupling

## How It Works

### Cognitive Loop

On each iteration, the agent:

1. **Perceives**: Analyzes the user query, conversation history, and memory to understand what's known and what's needed
2. **Decides**: Selects exactly one action that will most efficiently progress toward the goal
3. **Acts**: Executes the chosen action via MCP tools (web search, URL crawling, memory operations)
4. **Observes**: Receives and normalizes the results from action execution
5. **Remembers**: Updates durable memory with any new facts or preferences
6. **Repeats**: Continues until confidence is sufficient or max iterations reached

### Memory System

The memory system stores durable user facts as key-value pairs:

- **Storage**: JSON file at `state/memory.json`
- **Operations**: get(key), set(key, value), search(query), read_all()
- **Persistence**: Survives agent restarts and system reboots
- **Use Cases**: Remembering user preferences, learned facts, context from previous sessions

### Tool Integration

The agent uses the existing MCP server for all external interactions:

- **Web Search**: Tavily (primary) with DuckDuckGo fallback
- **Web Crawling**: crawl4ai for clean markdown extraction
- **Memory Operations**: read_memory and write_memory for the agent's own durable storage
- **Transport**: stdio-only MCP communication for security and reliability

All tool calls are tracked to prevent duplicate actions that could cause infinite loops.

## Extending the Agent

While designed to be complete as-is, the agent can be extended:

1. **Add new tools**: Extend mcp_server.py and update action.py to call them
2. **Enhance perception/decision**: Modify the prompt files in prompts/
3. **Adjust parameters**: Change MAX_ITERATIONS in agent6.py or temperatures in llm_gateway calls
4. **Different LLM routing**: Configure llm_gatewayV3 routing preferences

## Example Sessions

### Session 1: Establishing Preference
```
> uv run python agent6.py "Remember I prefer Python-first frameworks."
[Agent stores this preference in memory]
```

### Session 2: Using Stored Preference
```
> uv run python agent6.py "What web framework should I learn for backend development?"
[Agent recalls Python preference and recommends Django/FastAPI/Flask]
```

### Session 3: Complex Research
```
> uv run python agent6.py "Compare the architecture of AutoGPT and BabyAGI"
[Agent searches, crawls relevant sources, compares findings, provides structured answer]
```

## Troubleshooting

### Common Issues

1. **Missing API Keys**: Ensure `.env` contains valid OPENAI_API_KEY and TAVILY_API_KEY
2. **MCP Server Not Running**: Start mcp_server.py in a separate terminal before running agent6.py
3. **Dependency Issues**: Run `uv sync` to ensure all packages are installed
4. **Port Conflicts**: The LLM gateway runs on port 8101 by default - ensure it's available

### Logs and Debugging

- Check console output for agent progress
- Examine `state/traces/` for detailed execution traces
- Verify MCP server is running and accessible
- Ensure API keys have sufficient quota/credits

## Limitations and Boundaries

### Intentional Constraints

- **Maximum 6 iterations** prevents excessive computation
- **Single action per decision** ensures focused progression
- **No recursive reasoning** avoids uncontrolled autonomy
- **Deterministic temperatures** prioritize reliability over creativity
- **Memory is file-based** (not vector DB) for simplicity and reliability

### Not Designed For

- Chit-chat or casual conversation
- Real-time collaboration with humans
- Creative writing or artistic generation
- Unbounded open-ended exploration
- Replace human research entirely

## Contributing

As this is a reference implementation, contributions should focus on:

1. Improving documentation and examples
2. Fixing bugs or edge cases
3. Enhancing observability without changing core architecture
4. Adding utility functions that don't violate layer separation
5. Improving error handling and recovery

## Youtube Video Link

https://youtu.be/PLK82E6Lz6g

## Acknowledgments

Built upon existing infrastructure:
- Reuses mcp_server.py for tool execution
- Leverages llm_gatewayV3 for LLM provider abstraction
- Designed as a natural evolution of the existing repository
# PersonalResearchAnalyst
