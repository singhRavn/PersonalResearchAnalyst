"""
Decision layer for Personal Research Analyst.
Responsible for selecting ONE next action, minimizing iteration count,
avoiding repeated actions, and deciding when enough information exists.
"""
from __future__ import annotations

from typing import List, Optional, Tuple, Set
from pathlib import Path
from pydantic import BaseModel, Field

from schemas import (
    DecisionInput, 
    DecisionOutput, 
    ToolCall,
    PerceptionOutput,
    MemoryRecord
)
from llm_gateway import LLMGateway


class DecisionLayer:
    """Selects the single best next action based on perception output and history."""
    
    def __init__(self, llm_gateway: LLMGateway):
        self.llm = llm_gateway
        self._action_fingerprints: Set[Tuple[str, str]] = set()
    
    async def decide(self, input_data: DecisionInput) -> DecisionOutput:
        """
        Choose exactly one next action based on perception and history.
        
        Args:
            input_data: Contains perception output, execution history, and memory context
            
        Returns:
            DecisionOutput with exactly one tool call to execute
        """
        # Update action fingerprints from execution history
        self._update_fingerprints(input_data.execution_history)
        
        # Prepare the system prompt for decision
        system_prompt = self._load_decision_prompt()
        
        # Format the user input with all available context
        user_input = self._format_decision_input(input_data)
        
        # Call LLM with structured output
        result = await self.llm.generate_structured(
            model="decision",  # This will be routed appropriately by the gateway
            schema=DecisionOutput,
            system_prompt=system_prompt,
            user_input=user_input,
            temperature=0.0  # Deterministic temperature for decision
        )
        
        # Validate that we don't repeat actions (defensive check)
        if self._is_repeated_action(result.tool_call):
            # Force a finish action if we're about to repeat
            result.tool_call = ToolCall(tool="finish", args={"summary": "Stopping to avoid repeated actions"})
            result.reasoning = "Avoided repeated action by forcing finish"
            result.should_finish = True
        
        return result
    
    def _update_fingerprints(self, execution_history: List[Dict[str, Any]]) -> None:
        """Update the set of action fingerprints from execution history."""
        self._action_fingerprints.clear()
        for execution in execution_history:
            tool = execution.get("tool", "")
            args = execution.get("args", {})
            # Create a fingerprint: (tool_name, sorted_json_string_of_args)
            import json
            args_str = json.dumps(args, sort_keys=True)
            fingerprint = (tool, args_str)
            self._action_fingerprints.add(fingerprint)
    
    def _is_repeated_action(self, tool_call: ToolCall) -> bool:
        """Check if a tool call would be a repeated action."""
        import json
        args_str = json.dumps(tool_call.args, sort_keys=True)
        fingerprint = (tool_call.tool, args_str)
        return fingerprint in self._action_fingerprints
    
    def _load_decision_prompt(self) -> str:
        """Load the decision prompt from file."""
        try:
            prompt_path = Path(__file__).parent / "prompts" / "decision.md"
            return prompt_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            # Fallback prompt if file doesn't exist
            return """You are the Decision Layer of a Personal Research Analyst agent.
Your role is to select exactly ONE next action to take, minimizing iterations and avoiding repeated actions.

Analyze the perception output and execution history to decide:
1. What single action will most efficiently move us toward answering the user's query
2. Whether we have enough information to finish
3. Which tool (search_web, crawl_url, read_memory, write_memory, or finish) to use

Choose actions that:
- Address the highest priority knowledge gaps identified by perception
- Avoid repeating actions we've already tried
- Minimize the total number of iterations needed
- Lead to convergence within bounded iterations

If enough information exists to answer the user, choose the finish tool with a summary."""
    
    def _format_decision_input(self, input_data: DecisionInput) -> str:
        """Format decision input for the LLM."""
        sections = []
        
        # Perception output
        perception = input_data.perception_output
        sections.append(f"USER GOAL: {perception.user_goal}")
        sections.append(f"CONFIDENCE: {perception.confidence:.2f}")
        
        if perception.known_facts:
            sections.append(f"KNOWN FACTS:\n{chr(10).join('- ' + f for f in perception.known_facts)}")
        
        if perception.knowledge_gaps:
            gaps_lines = []
            for gap in perception.knowledge_gaps:
                gaps_lines.append(f"- [{gap.importance}] {gap.description} -> Suggested: {gap.suggested_action}")
            sections.append(f"KNOWLEDGE GAPS:\n{chr(10).join(gaps_lines)}")
        
        # Execution history
        if input_data.execution_history:
            history_lines = []
            for i, exec_record in enumerate(input_data.execution_history[-5:]):  # Last 5 executions
                tool = exec_record.get("tool", "unknown")
                args = exec_record.get("args", {})
                success = exec_record.get("success", False)
                status = "✓" if success else "✗"
                history_lines.append(f"{i+1}. {status} {tool}({args})")
            sections.append(f"RECENT EXECUTION HISTORY:\n{chr(10).join(history_lines)}")
        
        # Memory context
        if input_data.memory_context:
            memory_lines = []
            for record in input_data.memory_context[:10]:  # Top 10 memory records
                memory_lines.append(f"- {record.key}: {record.value}")
            sections.append(f"CURRENT MEMORY STATE:\n{chr(10).join(memory_lines)}")
        
        return "\n\n".join(sections)