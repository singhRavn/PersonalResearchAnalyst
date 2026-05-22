"""
Perception layer for Personal Research Analyst.
Responsible for understanding user intent, summarizing known facts,
identifying knowledge gaps, and estimating confidence.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field
from pathlib import Path

from schemas import (
    PerceptionInput, 
    PerceptionOutput, 
    KnowledgeGap,
    MemoryRecord
)
from llm_gateway import LLMGateway


class PerceptionLayer:
    """Processes user queries to extract intent and identify information needs."""
    
    def __init__(self, llm_gateway: LLMGateway):
        self.llm = llm_gateway
    
    async def perceive(self, input_data: PerceptionInput) -> PerceptionOutput:
        """
        Analyze the user query and context to understand what's needed.
        
        Args:
            input_data: Contains user query, conversation history, and memory context
            
        Returns:
            PerceptionOutput with structured understanding of the situation
        """
        # Prepare the system prompt for perception
        system_prompt = self._load_perception_prompt()
        
        # Format the user input with all available context
        user_input = self._format_perception_input(input_data)
        
        # Call LLM with structured output
        result = await self.llm.generate_structured(
            model="perception",  # This will be routed appropriately by the gateway
            schema=PerceptionOutput,
            system_prompt=system_prompt,
            user_input=user_input,
            temperature=0.1  # Deterministic temperature for perception
        )
        
        return result
    
    def _load_perception_prompt(self) -> str:
        """Load the perception prompt from file."""
        try:
            prompt_path = Path(__file__).parent / "prompts" / "perception.md"
            return prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            # Fallback prompt if file doesn't exist
            return """You are the Perception Layer of a Personal Research Analyst agent.
Your role is to understand user intent, summarize known facts, and identify knowledge gaps.
DO NOT choose tools or answer the user directly.

Analyze the user's query in context of conversation history and known facts from memory.
Extract:
1. The user's core goal or question
2. What facts we already know that are relevant
3. What specific information we're missing (knowledge gaps)
4. How confident we are in our current understanding

Be precise and factual. Focus on identifying what we need to learn to answer the user."""
    
    def _format_perception_input(self, input_data: PerceptionInput) -> str:
        """Format perception input for the LLM."""
        sections = []
        
        # User query
        sections.append(f"USER QUERY:\n{input_data.user_query}")
        
        # Conversation history
        if input_data.conversation_history:
            history_lines = []
            for msg in input_data.conversation_history[-5:]:  # Last 5 messages
                history_lines.append(f"{msg.role.upper()}: {msg.content}")
            sections.append(f"CONVERSATION HISTORY:\n{chr(10).join(history_lines)}")
        
        # Memory context
        if input_data.memory_context:
            memory_lines = []
            for record in input_data.memory_context[:10]:  # Top 10 memory records
                memory_lines.append(f"- {record.key}: {record.value}")
            sections.append(f"KNOWN FACTS FROM MEMORY:\n{chr(10).join(memory_lines)}")
        
        return "\n\n".join(sections)