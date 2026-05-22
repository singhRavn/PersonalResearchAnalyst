#!/usr/bin/env python3
"""
Gemini-only configuration for Personal Research Analyst.
Simplified setup using only Google Gemini API.
"""

# LLM Provider order: use ONLY Gemini
LLM_ORDER = "gemini"

# Router order: force Gemini as the only option
ROUTER_ORDER = "gemini"

# Fallback model when no provider specified — prefer Gemini 3.1 Flash Lite
DEFAULT_MODEL = "gemini-3.1-flash-lite"

# Gateway configuration
GATEWAY_URL = "http://localhost:8101"
GATEWAY_V3_PORT = 8101

# Request configuration
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2048

# Perception layer (analysis phase) - prefer lightweight deterministic model
PERCEPTION_MODEL = "gemini-3.1-flash-lite"
PERCEPTION_TEMPERATURE = 0.1  # Deterministic
PERCEPTION_MAX_TOKENS = 1024

# Decision layer (choosing next action) - deterministic
DECISION_MODEL = "gemini-3.1-flash-lite"
DECISION_TEMPERATURE = 0.0  # Deterministic
DECISION_MAX_TOKENS = 512

# Agent configuration
MAX_ITERATIONS = 6
REQUEST_TIMEOUT_SECONDS = 60

print("""
✓ Gemini-Only Configuration Loaded

Configuration:
  - LLM Provider: Gemini (gemini-2.0-flash)
  - Router: Disabled (single provider)
  - Default Temperature: 0.7
  - Perception Temperature: 0.1 (deterministic)
  - Decision Temperature: 0.0 (deterministic)
  - Max Iterations: 6

Required Setup:
  1. Set GOOGLE_API_KEY in .env with your Gemini API key
  2. Start gateway: python -m src.llm_gatewayV3.main
  3. Run agent: python -m src.agent6

Gemini API Key:
  - Get from: https://aistudio.google.com/apikey
  - Free tier available
  - Check quotas for production use
""")
