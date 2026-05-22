"""
Unit tests for Personal Research Analyst layers.
Tests perception, decision, memory, and schema contracts.
"""
import asyncio
import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from schemas import (
    Message, MemoryRecord, PerceptionInput, PerceptionOutput,
    DecisionInput, DecisionOutput, ActionResult, ToolCall, KnowledgeGap
)
from memory import MemoryLayer
from datetime import datetime


class TestMemoryLayer:
    """Tests for the memory persistence layer."""
    
    def setup_method(self):
        """Set up test memory instance."""
        self.memory = MemoryLayer(memory_file="state/test_memory.json")
        self.memory.clear()
    
    def test_memory_set_get(self):
        """Test basic set/get operations."""
        self.memory.set("test_key", "test_value")
        result = self.memory.get("test_key")
        assert result == "test_value"
    
    def test_memory_nonexistent_key(self):
        """Test retrieving nonexistent key returns None."""
        result = self.memory.get("nonexistent")
        assert result is None
    
    def test_memory_update(self):
        """Test updating existing memory."""
        self.memory.set("key", "value1")
        self.memory.set("key", "value2")
        result = self.memory.get("key")
        assert result == "value2"
    
    def test_memory_search(self):
        """Test memory search functionality."""
        self.memory.set("python_facts", "Python is a programming language")
        self.memory.set("python_tools", "FastAPI and Django are Python frameworks")
        self.memory.set("javascript_facts", "JavaScript runs in browsers")
        
        results = self.memory.search("python")
        assert len(results) == 2
        # Verify key matches score higher (python_facts should be first)
        assert "python_facts" in results[0].key
    
    def test_memory_read_all(self):
        """Test reading all memory records."""
        self.memory.set("fact1", "value1")
        self.memory.set("fact2", "value2")
        
        all_records = self.memory.read_all()
        assert len(all_records) == 2
    
    def cleanup_method(self):
        """Clean up test files."""
        test_file = Path("state/test_memory.json")
        if test_file.exists():
            test_file.unlink()


class TestSchemas:
    """Tests for Pydantic schema contracts."""
    
    def test_perception_output_validation(self):
        """Test PerceptionOutput schema."""
        gap = KnowledgeGap(
            description="What is Python used for?",
            importance="high",
            suggested_action="search_web"
        )
        
        output = PerceptionOutput(
            user_goal="Learn about Python",
            known_facts=["Python is a programming language"],
            knowledge_gaps=[gap],
            confidence=0.5,
            needs_more_info=True
        )
        
        assert output.user_goal == "Learn about Python"
        assert output.confidence == 0.5
        assert len(output.knowledge_gaps) == 1
    
    def test_tool_call_validation(self):
        """Test ToolCall schema."""
        tool_call = ToolCall(
            tool="search_web",
            args={"query": "python programming", "max_results": 5}
        )
        
        assert tool_call.tool == "search_web"
        assert tool_call.args["query"] == "python programming"
    
    def test_message_with_timestamp(self):
        """Test Message schema with auto timestamp."""
        msg = Message(role="user", content="What is Python?")
        
        assert msg.role == "user"
        assert msg.content == "What is Python?"
        assert isinstance(msg.timestamp, datetime)
    
    def test_action_result_validation(self):
        """Test ActionResult schema."""
        result = ActionResult(
            success=True,
            observation="Found 5 results about Python",
            error=None,
            memory_writes=[]
        )
        
        assert result.success is True
        assert "Python" in result.observation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
