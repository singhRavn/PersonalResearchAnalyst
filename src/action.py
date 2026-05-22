"""
Action layer for Personal Research Analyst.
The ONLY layer allowed to call MCP tools, interact with Tavily/crawl4ai,
write memory, and perform side effects.
"""
from __future__ import annotations

import asyncio
import json
from typing import List, Optional, Dict, Any
from pathlib import Path

from schemas import ActionResult, ToolCall, MemoryRecord
from memory import MemoryLayer
from llm_gateway import LLMGateway


class ActionLayer:
    """Executes actions and returns normalized observations."""
    
    def __init__(self, llm_gateway: LLMGateway, memory_layer: MemoryLayer):
        self.llm = llm_gateway
        self.memory = memory_layer
        # Note: In a real implementation, we would connect to the MCP server
        # For now, we'll simulate the MCP tool calls
    
    async def execute(self, tool_call: ToolCall) -> ActionResult:
        """
        Execute a single tool action and return the result.
        
        Args:
            tool_call: The tool to execute with its arguments
            
        Returns:
            ActionResult with observation and any side effects
        """
        try:
            if tool_call.tool == "search_web":
                return await self._search_web(tool_call.args)
            elif tool_call.tool == "crawl_url":
                return await self._crawl_url(tool_call.args)
            elif tool_call.tool == "read_memory":
                return await self._read_memory(tool_call.args)
            elif tool_call.tool == "write_memory":
                return await self._write_memory(tool_call.args)
            elif tool_call.tool == "finish":
                return await self._finish(tool_call.args)
            else:
                return ActionResult(
                    success=False,
                    observation=f"Unknown tool: {tool_call.tool}",
                    error=f"Tool '{tool_call.tool}' is not supported"
                )
        except Exception as e:
            return ActionResult(
                success=False,
                observation=f"Failed to execute {tool_call.tool}",
                error=str(e)
            )
    
    async def _search_web(self, args: Dict[str, Any]) -> ActionResult:
        """Execute web search via MCP server."""
        query = args.get("query", "")
        max_results = args.get("max_results", 5)
        
        if not query:
            return ActionResult(
                success=False,
                observation="Empty search query provided",
                error="Query parameter is required for search_web"
            )
        
        # In a real implementation, we would call the MCP server's web_search tool
        # For now, we'll simulate by returning a structured response
        observation = f"Searched web for: '{query}' (max {max_results} results)"
        
        # Simulate some search results
        if "python" in query.lower():
            observation += "\n- Found: Python is a high-level programming language"
            observation += "\n- Found: Python frameworks include Django, Flask, FastAPI"
            observation += "\n- Found: Python is popular for data science and AI"
        elif "browser agent" in query.lower():
            observation += "\n- Found: OpenHands is an open-source AI agent for software development"
            observation += "\n- Found: Browser agents like BrowserUse enable web automation"
            observation += "\n- Found: Multimodal planning is supported by some vision-enabled agents"
        else:
            observation += "\n- Found: General information about the topic"
            observation += "\n- Found: Multiple sources available for further research"
        
        return ActionResult(
            success=True,
            observation=observation
        )
    
    async def _crawl_url(self, args: Dict[str, Any]) -> ActionResult:
        """Execute URL crawling via MCP server."""
        url = args.get("url", "")
        
        if not url:
            return ActionResult(
                success=False,
                observation="Empty URL provided",
                error="URL parameter is required for crawl_url"
            )
        
        # In a real implementation, we would call the MCP server's fetch_url tool
        observation = f"Crawled URL: {url}"
        
        # Simulate some crawled content
        if "openhands" in url.lower():
            observation += "\n- Content: OpenHands is an open-source AI agent that integrates with VS Code"
            observation += "\n- Content: Supports code editing, debugging, and development workflows"
            observation += "\n- Content: Uses a planner-executor architecture with LLM backend"
        elif "browseruse" in url.lower():
            observation += "\n- Content: BrowserUse is a library for AI agents to interact with web browsers"
            observation += "\n- Content: Provides DOM interaction, form filling, and navigation capabilities"
            observation += "\n- Content: Can be integrated with various LLM backends"
        else:
            observation += "\n- Content: Successfully retrieved and cleaned markdown content"
            observation += "\n- Content: Ready for information extraction"
        
        return ActionResult(
            success=True,
            observation=observation
        )
    
    async def _read_memory(self, args: Dict[str, Any]) -> ActionResult:
        """Read from durable memory."""
        key = args.get("key", "")
        
        if not key:
            # Read all memories if no key specified
            memories = self.memory.read_all()
            observation = f"Read {len(memories)} memory records"
            if memories:
                observation += "\n- " + "\n- ".join([f"{m.key}: {m.value}" for m in memories[:5]])
                if len(memories) > 5:
                    observation += f"\n- ... and {len(memories) - 5} more"
            else:
                observation += "\n- No memories found"
            
            return ActionResult(
                success=True,
                observation=observation
            )
        
        # Read specific key
        value = self.memory.get(key)
        if value is not None:
            observation = f"Read memory '{key}': {value}"
            return ActionResult(
                success=True,
                observation=observation
            )
        else:
            observation = f"No memory found for key: '{key}'"
            return ActionResult(
                success=True,  # Still successful, just not found
                observation=observation
            )
    
    async def _write_memory(self, args: Dict[str, Any]) -> ActionResult:
        """Write to durable memory."""
        key = args.get("key", "")
        value = args.get("value", "")
        
        if not key:
            return ActionResult(
                success=False,
                observation="Empty key provided for memory write",
                error="Key parameter is required for write_memory"
            )
        
        if not value:
            return ActionResult(
                success=False,
                observation="Empty value provided for memory write",
                error="Value parameter is required for write_memory"
            )
        
        self.memory.set(key, value)
        observation = f"Written to memory: '{key}' = '{value}'"
        
        # Also return the memory record for potential use
        memory_record = self.memory._memory[key]  # Access internal for result
        
        return ActionResult(
            success=True,
            observation=observation,
            memory_writes=[memory_record]
        )
    
    async def _finish(self, args: Dict[str, Any]) -> ActionResult:
        """Finish the agent loop and return final answer."""
        summary = args.get("summary", "No summary provided")
        observation = f"Research completed: {summary}"
        
        return ActionResult(
            success=True,
            observation=observation
        )