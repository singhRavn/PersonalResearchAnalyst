"""
LLM Gateway wrapper for Personal Research Analyst.
Provides a simplified interface to llm_gatewayV3 for structured LLM calls.
"""
from __future__ import annotations

import asyncio
import os
import json
import httpx
from typing import Dict, Any, Optional, Type, List, Union
from pathlib import Path

from pydantic import BaseModel

from schemas import (
    PerceptionOutput,
    DecisionOutput
)


class LLMGateway:
    """Wrapper around llm_gatewayV3 for structured LLM calls."""
    
    def __init__(self, gateway_url: str = "http://localhost:8101"):
        self.gateway_url = gateway_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)
        # Use gemini-3.1-flash-lite as the default model (has available free tier quota)
        self.default_model = "gemini-3.1-flash-lite"
    
    async def generate_structured(
        self,
        model: Union[str, List[str]],
        schema: Type[BaseModel],
        system_prompt: str,
        user_input: str,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> BaseModel:
        """
        Generate a structured response from the LLM using llm_gatewayV3.
        
        Args:
            model: Model identifier (used for routing in gateway)
            schema: Pydantic model to validate output against
            system_prompt: System message for the LLM
            user_input: User message/input
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Validated Pydantic model instance
        """
        # Normalize model: always use gemini-2.5-pro unless explicitly overridden
        model_list = []
        if isinstance(model, list):
            model_list = model
        elif isinstance(model, str) and model and model.lower() not in ("auto", "perception", "decision", "gemini"):
            model_list = [model]
        else:
            model_list = [self.default_model, "gemini-3-flash", "gemini-2.5-flash"]

        last_exc: Optional[Exception] = None
        cooldown_attempts = 0
        for attempt, m in enumerate(model_list):
            # Prepare the request for llm_gatewayV3
            request_data = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "model": m,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {
                    "type": "json_schema",
                    "schema": schema.model_json_schema(),
                    "name": schema.__name__,
                    "strict": True
                }
            }

            try:
                response = await self.client.post(f"{self.gateway_url}/v1/chat", json=request_data)
                if response.status_code == 503 and "cooldown" in response.text.lower():
                    cooldown_attempts += 1
                    if cooldown_attempts <= 4:
                        await asyncio.sleep(5)
                        last_exc = Exception(f"LLM gateway cooldown for model {m}: {response.status_code} - {response.text}")
                        continue
                    else:
                        last_exc = Exception(f"LLM gateway cooldown expired for model {m}: {response.status_code} - {response.text}")
                        continue
                if response.status_code != 200:
                    last_exc = Exception(f"LLM gateway error for model {m}: {response.status_code} - {response.text}")
                    continue

                result = response.json()

                # Extract the parsed structured output
                if "parsed" in result and result["parsed"] is not None:
                    return schema.model_validate(result["parsed"])
                else:
                    # Fallback: parse the text response
                    try:
                        parsed_dict = json.loads(result.get("text", "{}"))
                        return schema.model_validate(parsed_dict)
                    except (json.JSONDecodeError, ValueError) as e:
                        last_exc = Exception(
                            f"Failed to parse LLM response from model {m} as {schema.__name__}: {e}\n"
                            f"Response text: {result.get('text', 'No text')}"
                        )
                        continue
            except Exception as e:
                last_exc = e
                continue

        # If we get here, request failed
        raise Exception(f"LLM gateway failed for models {model_list}. Last error: {last_exc}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()