"""
Pydantic v2 schemas for Personal Research Analyst agent.
All boundaries between layers use these typed contracts.
"""
from __future__ import annotations

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Message(BaseModel):
    """Represents a message in the conversation."""
    role: Literal["user", "assistant"] = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp when message was created")


class MemoryRecord(BaseModel):
    """A durable memory record that persists across runs."""
    key: str = Field(..., description="Unique key for the memory record")
    value: str = Field(..., description="Value stored in memory")
    created_at: datetime = Field(default_factory=datetime.now, description="When the memory was created")
    accessed_at: datetime = Field(default_factory=datetime.now, description="When the memory was last accessed")
    access_count: int = Field(default=0, description="Number of times this memory has been accessed")


class PerceptionInput(BaseModel):
    """Input to the perception layer."""
    user_query: str = Field(..., description="The original user query")
    conversation_history: List[Message] = Field(default_factory=list, description="Previous messages in conversation")
    memory_context: List[MemoryRecord] = Field(default_factory=list, description="Relevant facts from durable memory")


class KnowledgeGap(BaseModel):
    """Identifies a specific piece of missing information."""
    description: str = Field(..., description="Description of what we don't know")
    importance: Literal["low", "medium", "high"] = Field(..., description="How critical this gap is to answering the query")
    suggested_action: Literal["search_web", "crawl_url"] = Field(..., description="Recommended tool to fill this gap")


class PerceptionOutput(BaseModel):
    """Output from the perception layer."""
    user_goal: str = Field(..., description="Clear statement of what the user wants to achieve")
    known_facts: List[str] = Field(default_factory=list, description="Facts we already know from memory/conversation")
    knowledge_gaps: List[KnowledgeGap] = Field(default_factory=list, description="Identified gaps in our knowledge")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in current understanding (0-1)")
    needs_more_info: bool = Field(..., description="Whether we need to gather more information")


class ToolCall(BaseModel):
    """Represents a single tool action to be executed."""
    tool: Literal["search_web", "crawl_url", "read_memory", "write_memory", "finish"] = Field(..., description="Tool to execute")
    args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")


class DecisionInput(BaseModel):
    """Input to the decision layer."""
    perception_output: PerceptionOutput = Field(..., description="Output from perception layer")
    execution_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of tool executions")
    memory_context: List[MemoryRecord] = Field(default_factory=list, description="Current memory state")


class DecisionOutput(BaseModel):
    """Output from the decision layer."""
    tool_call: ToolCall = Field(..., description="Single tool action to execute next")
    reasoning: str = Field(..., description="Explanation of why this action was chosen")
    should_finish: bool = Field(False, description="Whether this action should terminate the agent loop")


class ActionResult(BaseModel):
    """Result from executing an action."""
    success: bool = Field(..., description="Whether the action succeeded")
    observation: str = Field(..., description="What we learned from executing the action")
    error: Optional[str] = Field(None, description="Error message if action failed")
    memory_writes: List[MemoryRecord] = Field(default_factory=list, description="Any new memories created during execution")