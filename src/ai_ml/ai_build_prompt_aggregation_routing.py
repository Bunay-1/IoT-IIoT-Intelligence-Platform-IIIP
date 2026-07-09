"""
AI Agent Orchestration and Prompt Engineering Module

This module implements an intelligent system for routing user requests to a
registry of specialized "Expert Agents". It analyzes user intent, dynamically
constructs tailored prompts, and can orchestrate multi-agent "chains of thought"
to resolve complex tasks.
"""
import asyncio
import random
import time
from typing import Any, Dict, List, Optional, Type
from collections import defaultdict
import re

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# --- Base Expert Agent Definition ---

class ExpertAgent:
    """
    Base class for a specialized AI agent. Each agent encapsulates its
    capabilities, prompt templates, and the LLM model it uses.
    """
    def __init__(self, model_id: str, cost_per_1k_tokens: float, base_latency_ms: int):
        self.model_id = model_id
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.base_latency_ms = base_latency_ms
        self.performance_metrics = {"total_cost": 0.0, "avg_latency_ms": 0.0, "requests": 0}

    def get_capabilities(self) -> List[str]:
        """Returns a list of keywords defining the agent's expertise."""
        raise NotImplementedError

    def construct_prompt(self, user_query: str, context: Optional[Dict] = None) -> str:
        """Constructs a tailored, high-quality prompt for the LLM."""
        return user_query # Default behavior is to pass the query directly

    async def execute(self, user_query: str, context: Optional[Dict] = None) -> Dict:
        """Simulates executing the prompt against the agent's model."""
        full_prompt = self.construct_prompt(user_query, context)

        # Simulate API call latency and cost
        latency_ms = self.base_latency_ms + random.uniform(-50, 100)
        await asyncio.sleep(latency_ms / 1000.0)

        response_tokens = len(full_prompt.split()) * 1.5 # Simulate a response length
        cost = (len(full_prompt.split()) + response_tokens) / 1000 * self.cost_per_1k_tokens

        # Update metrics
        total_reqs = self.performance_metrics['requests'] + 1
        self.performance_metrics['total_cost'] += cost
        self.performance_metrics['avg_latency_ms'] = ((self.performance_metrics['avg_latency_ms'] * (total_reqs - 1)) + latency_ms) / total_reqs
        self.performance_metrics['requests'] = total_reqs

        return {
            "response": f"Response from {self.model_id} ({self.__class__.__name__}): Processed query for '{user_query[:30]}...'",
            "cost": cost,
            "latency_ms": latency_ms,
            "agent_used": self.__class__.__name__
        }

# --- Concrete Agent Implementations ---

class CodeGeneratorAgent(ExpertAgent):
    """Specialized in generating high-quality code."""
    def get_capabilities(self) -> List[str]:
        return ['code', 'python', 'javascript', 'function', 'class', 'script', 'algorithm']

    def construct_prompt(self, user_query: str, context: Optional[Dict] = None) -> str:
        return (
            "You are a senior software engineer. Your task is to provide a robust, well-documented code solution.\n"
            f"User request: '{user_query}'\n"
            "Please provide the code within a markdown block and include a brief explanation."
        )

class DataAnalysisAgent(ExpertAgent):
    """Specialized in data analysis, summarization, and extraction."""
    def get_capabilities(self) -> List[str]:
        return ['analyze', 'summarize', 'data', 'extract', 'sentiment', 'report']

    def construct_prompt(self, user_query: str, context: Optional[Dict] = None) -> str:
        prompt = (
            "As a data scientist, your task is to analyze the provided information.\n"
            f"User request: '{user_query}'\n"
        )
        if context and 'data' in context:
            prompt += f"Dataset to analyze: \n---\n{context['data']}\n---"
        return prompt

class CreativeWriterAgent(ExpertAgent):
    """Specialized in creative writing tasks."""
    def get_capabilities(self) -> List[str]:
        return ['write', 'poem', 'story', 'marketing', 'slogan', 'creative']

    def construct_prompt(self, user_query: str, context: Optional[Dict] = None) -> str:
        style = context.get('style', 'a professional and engaging') if context else 'a professional and engaging'
        return (
            f"You are a creative writer. Adopt {style} tone.\n"
            f"Task: '{user_query}'"
        )

# --- Intelligent Router and Orchestrator ---

class PromptOrchestrator:
    """
    Analyzes user queries, routes them to the appropriate ExpertAgent,
    and can orchestrate multi-agent chains for complex tasks.
    """
    def __init__(self):
        self.agents: Dict[str, ExpertAgent] = {}
        self._register_default_agents()

    def _register_default_agents(self):
        self.register_agent(CodeGeneratorAgent("gpt-4-turbo", 0.010, 500))
        self.register_agent(DataAnalysisAgent("claude-3-opus", 0.015, 800))
        self.register_agent(CreativeWriterAgent("gemini-1.5-pro", 0.007, 650))

    def register_agent(self, agent_instance: ExpertAgent):
        """Adds a new agent to the orchestrator's registry."""
        self.agents[agent_instance.__class__.__name__] = agent_instance
        logger.info(f"Registered agent: {agent_instance.__class__.__name__}")

    def _route_to_agent(self, user_query: str) -> ExpertAgent:
        """
        Analyzes the user query to select the most appropriate agent.
        Uses a simple keyword-based classification.
        """
        scores: Dict[str, int] = defaultdict(int)
        query_lower = user_query.lower()

        for name, agent in self.agents.items():
            for keyword in agent.get_capabilities():
                if re.search(r'\b' + keyword + r'\b', query_lower):
                    scores[name] += 1

        if not scores:
            logger.warning("No specific agent matched, falling back to the most capable generalist.")
            # Fallback to the most expensive model, assuming it's the most capable.
            return max(self.agents.values(), key=lambda a: a.cost_per_1k_tokens)

        best_agent_name = max(scores, key=scores.get)
        logger.info(f"Routing query to: {best_agent_name} (Score: {scores[best_agent_name]})")
        return self.agents[best_agent_name]

    async def handle_simple_request(self, user_query: str) -> Dict:
        """Handles a single, straightforward request."""
        agent = self._route_to_agent(user_query)
        result = await agent.execute(user_query)
        return result

    async def execute_complex_chain(self, initial_query: str, chain: List[Dict]) -> Dict:
        """
        Executes a multi-step "chain of thought" where the output of one
        agent becomes the input for the next.

        Example chain step: {'agent': 'DataAnalysisAgent', 'task': 'First, summarize the key points.'}
        """
        logger.info(f"Executing complex chain for query: '{initial_query}'")

        current_context = {"data": initial_query}
        intermediate_results = []

        for step in chain:
            agent_name = step.get("agent")
            task_instruction = step.get("task")

            if not agent_name or agent_name not in self.agents:
                return {"error": f"Agent '{agent_name}' not found in registry."}

            agent = self.agents[agent_name]
            logger.info(f"Chain step: Executing '{task_instruction}' with {agent_name}")

            result = await agent.execute(task_instruction, current_context)
            intermediate_results.append(result)

            # The output of this step becomes the input 'data' for the next
            current_context['data'] = result['response']

        final_result = {
            "final_response": current_context['data'],
            "intermediate_steps": intermediate_results
        }
        return final_result

    def get_performance_dashboard(self) -> Dict:
        """Returns performance metrics for all registered agents."""
        return {name: {
            "model_id": agent.model_id,
            "total_cost": round(agent.performance_metrics["total_cost"], 4),
            "avg_latency_ms": round(agent.performance_metrics["avg_latency_ms"]),
            "requests": agent.performance_metrics["requests"]
        } for name, agent in self.agents.items()}


async def main():
    orchestrator = PromptOrchestrator()

    print("\n--- 1. Simple Request: Code Generation ---")
    query1 = "Write a python script to download a file from a URL."
    result1 = await orchestrator.handle_simple_request(query1)
    print(f"Agent '{result1['agent_used']}' responded: {result1['response']}")

    print("\n--- 2. Simple Request: Data Analysis ---")
    query2 = "Summarize the following text: [long text about AI ethics]"
    result2 = await orchestrator.handle_simple_request(query2)
    print(f"Agent '{result2['agent_used']}' responded: {result2['response']}")

    print("\n--- 3. Complex Chain of Thought ---")
    complex_query = "Customer feedback: 'The new interface is sleek, but the analytics dashboard is slow.'"
    chain_of_thought = [
        {"agent": "DataAnalysisAgent", "task": "Extract the main sentiment and key topics from the feedback."},
        {"agent": "CreativeWriterAgent", "task": "Based on the analysis, write a polite, empathetic customer-facing reply."}
    ]
    chain_result = await orchestrator.execute_complex_chain(complex_query, chain_of_thought)

    print("Intermediate Steps:")
    for i, step_result in enumerate(chain_result['intermediate_steps']):
        print(f"  Step {i+1} ({step_result['agent_used']}): {step_result['response']}")
    print("\nFinal Response:")
    print(chain_result['final_response'])

    print("\n--- Performance Dashboard ---")
    print(orchestrator.get_performance_dashboard())

if __name__ == "__main__":
    asyncio.run(main())
