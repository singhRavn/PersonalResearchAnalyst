"""
Personal Research Analyst Agent - Main Orchestrator
Implements the cognitive architecture with perception, decision, action, and memory layers.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from schemas import (
    PerceptionInput,
    PerceptionOutput,
    DecisionInput,
    DecisionOutput,
    ToolCall,
    ActionResult,
    Message,
    MemoryRecord
)
from memory import MemoryLayer
from perception import PerceptionLayer
from decision import DecisionLayer
from action import ActionLayer
from llm_gateway import LLMGateway


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PersonalResearchAnalyst:
    """
    Main orchestrator for the Personal Research Analyst agent.
    Implements the cognitive loop: Perception -> Decision -> Action -> Observation -> Memory
    """
    
    def __init__(self):
        # Initialize layers
        self.memory = MemoryLayer()
        self.llm_gateway = LLMGateway()
        self.perception = PerceptionLayer(self.llm_gateway)
        self.decision = DecisionLayer(self.llm_gateway)
        self.action = ActionLayer(self.llm_gateway, self.memory)
        
        # Agent state
        self.max_iterations = 6
        self.conversation_history: List[Message] = []
        self.execution_history: List[dict] = []
        self.traces: List[dict] = []
        
        # Ensure state directories exist
        Path("state/traces").mkdir(parents=True, exist_ok=True)
    
    async def research(self, user_query: str) -> str:
        """
        Main research loop that processes a user query.
        
        Args:
            user_query: The user's research question or request
            
        Returns:
            Final answer string
        """
        logger.info(f"Starting research for query: {user_query}")
        
        # Add user message to conversation history
        user_message = Message(role="user", content=user_query)
        self.conversation_history.append(user_message)
        
        # Main cognitive loop
        for iteration in range(self.max_iterations):
            logger.info(f"Iteration {iteration + 1}/{self.max_iterations}")
            
            try:
                # 1. PERCEPTION LAYER: Understand what we know and what we need to learn
                perception_input = PerceptionInput(
                    user_query=user_query,
                    conversation_history=self.conversation_history.copy(),
                    memory_context=self.memory.read_all()
                )
                
                perception_output = await self.perception.perceive(perception_input)
                logger.debug(f"Perception output: {perception_output}")
                
                # 2. DECISION LAYER: Choose exactly one next action
                decision_input = DecisionInput(
                    perception_output=perception_output,
                    execution_history=self.execution_history.copy(),
                    memory_context=self.memory.read_all()
                )
                
                decision_output = await self.decision.decide(decision_input)
                logger.debug(f"Decision output: {decision_output}")
                
                # 3. ACTION LAYER: Execute the chosen action
                action_result = await self.action.execute(decision_output.tool_call)
                logger.debug(f"Action result: {action_result}")
                
                # 4. Update state based on action result
                await self._update_state(
                    iteration, 
                    perception_output, 
                    decision_output, 
                    action_result
                )
                
                # 5. Check if we should finish
                if decision_output.should_finish or action_result.success and decision_output.tool_call.tool == "finish":
                    logger.info("Agent decided to finish")
                    break
                    
                # 6. Add agent response to conversation history if we got meaningful observation
                if action_result.success and action_result.observation:
                    agent_message = Message(
                        role="assistant", 
                        content=f"Iteration {iteration + 1}: {action_result.observation}"
                    )
                    self.conversation_history.append(agent_message)
                
            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}")
                # Add error to conversation and continue or break
                error_message = Message(
                    role="assistant",
                    content=f"Encountered an error: {str(e)}. Continuing with available information."
                )
                self.conversation_history.append(error_message)
                break
        
        # Generate final answer from accumulated knowledge
        final_answer = await self._generate_final_answer()
        
        # Add final answer to conversation history
        final_message = Message(role="assistant", content=final_answer)
        self.conversation_history.append(final_message)
        
        # Save trace
        await self._save_trace()
        
        logger.info("Research completed")
        return final_answer
    
    async def _update_state(
        self,
        iteration: int,
        perception_output: PerceptionOutput,
        decision_output: DecisionOutput,
        action_result: ActionResult
    ) -> None:
        """Update agent state after each iteration."""
        # Record execution
        execution_record = {
            "iteration": iteration,
            "tool": decision_output.tool_call.tool,
            "args": decision_output.tool_call.args,
            "success": action_result.success,
            "observation": action_result.observation,
            "error": action_result.error,
            "timestamp": datetime.now().isoformat()
        }
        self.execution_history.append(execution_record)
        
        # Record trace for this iteration
        trace_record = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "perception": perception_output.model_dump(),
            "decision": decision_output.model_dump(),
            "action": {
                "tool": decision_output.tool_call.tool,
                "args": decision_output.tool_call.args
            },
            "result": action_result.model_dump(),
            "memory_state": [m.model_dump() for m in self.memory.read_all()],
            "conversation_length": len(self.conversation_history)
        }
        self.traces.append(trace_record)
    
    async def _generate_final_answer(self) -> str:
        """Generate a final answer based on all accumulated knowledge."""
        # Prepare context for final answer generation
        memory_context = self.memory.read_all()
        memory_summary = "\n".join([f"- {m.key}: {m.value}" for m in memory_context]) if memory_context else "No specific memories stored."
        
        # Get recent conversation and observations
        recent_observations = []
        for exec_record in self.execution_history[-5:]:  # Last 5 executions
            if exec_record.get("success") and exec_record.get("observation"):
                recent_observations.append(exec_record["observation"])
        
        # Prepare prompt for final answer synthesis
        system_prompt = """You are the Personal Research Analyst agent synthesizing a final answer.
Based on the research conducted, provide a comprehensive, accurate, and well-sourced answer to the user's original question.
Use only the information gathered during research. If uncertain, express that uncertainty.
Do not make up facts or pretend to know things you didn't discover in your research."""
        
        user_input = f"""ORIGINAL USER QUERY:
{self.conversation_history[0].content if self.conversation_history else 'Unknown'}

MEMORY CONTENT (enduring facts learned):
{memory_summary}

RECENT OBSERVATIONS FROM RESEARCH:
{chr(10).join(recent_observations) if recent_observations else 'No observations recorded'}

TOTAL ITERATIONS: {len(self.execution_history)}
CONVERSATION TURNS: {len(self.conversation_history)}

Please provide a final answer to the user's original question based on what you've learned."""
        
        try:
            # Use the LLM to generate a cohesive final answer
            # For final answer, we want text, not necessarily structured output
            response = await self.llm_gateway.client.post(
                f"{self.llm_gateway.gateway_url}/v1/chat",
                json={
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                    "model": self.llm_gateway.default_model,
                    "temperature": 0.3,
                    "max_tokens": 1024
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM gateway error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get("text", "No response text")
                
        except Exception as e:
            logger.error(f"Failed to generate final answer: {e}")
            # Fallback: create answer from memory and observations
            answer_parts = [
                f"Based on my research of: {self.conversation_history[0].content if self.conversation_history else 'the query'},",
                f"I gathered the following information:"
            ]
            
            if memory_context:
                answer_parts.append("\nKey facts remembered:")
                answer_parts.extend([f"• {m.key}: {m.value}" for m in memory_context])
            
            if recent_observations:
                answer_parts.append("\nResearch observations:")
                answer_parts.extend([f"• {obs}" for obs in recent_observations])
            
            if not memory_context and not recent_observations:
                answer_parts.append("I was unable to gather specific information on this topic.")
            
            return "\n".join(answer_parts)
    
    async def _save_trace(self) -> None:
        """Save the execution trace to disk."""
        if not self.traces:
            return
        
        trace_data = {
            "session_start": self.conversation_history[0].model_dump() if self.conversation_history else None,
            "total_iterations": len(self.traces),
            "traces": self.traces,
            "final_memory_state": [m.model_dump() for m in self.memory.read_all()],
            "conversation_history": [m.model_dump() for m in self.conversation_history],
            "execution_summary": {
                "total_executions": len(self.execution_history),
                "successful_executions": len([e for e in self.execution_history if e.get("success")]),
                "failed_executions": len([e for e in self.execution_history if not e.get("success")])
            }
        }
        
        # Save trace file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_file = Path(f"state/traces/trace_{timestamp}.json")
        trace_file.write_text(
            json.dumps(trace_data, indent=2, default=str),
            encoding="utf-8"
        )
        logger.info(f"Trace saved to {trace_file}")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.llm_gateway.close()


# Convenience function for running the agent
async def run_research(query: str) -> str:
    """
    Convenience function to run research on a query.
    
    Args:
        query: The research question
        
    Returns:
        Final answer string
    """
    agent = PersonalResearchAnalyst()
    try:
        result = await agent.research(query)
        return result
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    # Allow running directly for testing
    import sys
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your research query: ")
    
    async def main():
        agent = PersonalResearchAnalyst()
        try:
            answer = await agent.research(query)
            print("\n" + "="*60)
            print("FINAL ANSWER:")
            print("="*60)
            print(answer)
        finally:
            await agent.cleanup()
    
    asyncio.run(main())