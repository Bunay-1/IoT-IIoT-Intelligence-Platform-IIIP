"""
AI Build Prompt Aggregation and Routing Module

This module implements an intelligent, stateful router for aggregating, processing,
and routing AI prompts to a dynamic registry of language models based on various
strategies like cost, latency, and capability.
"""

import asyncio
import time
import random
from typing import Any, Dict, List, Optional, Literal
from collections import defaultdict
import aiohttp
import logging

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RoutingStrategy = Literal["best_capability", "lowest_cost", "lowest_latency", "balanced"]

class PromptRouter:
    """
    An intelligent, stateful router for AI prompts.
    """
    def __init__(self):
        # Registry of available AI models with their metadata
        self.model_registry: Dict[str, Dict] = {}
        # Performance metrics tracked per model
        self.performance_metrics: Dict[str, Dict] = defaultdict(lambda: {"total_cost": 0.0, "avg_latency_ms": 0.0, "requests": 0})
        # History of routing decisions
        self.routing_history: List[Dict] = []

        # Initialize with some default models
        self._register_default_models()

    def _register_default_models(self):
        """Registers a predefined set of AI models."""
        self.register_model(
            model_id="claude-3-opus",
            capabilities=["complex_reasoning", "text_generation", "code_generation", "summarization"],
            cost_per_1k_tokens=0.015,
            base_latency_ms=800
        )
        self.register_model(
            model_id="gpt-4-turbo",
            capabilities=["text_generation", "code_generation", "json_output"],
            cost_per_1k_tokens=0.010,
            base_latency_ms=500
        )
        self.register_model(
            model_id="gemini-1.5-pro",
            capabilities=["multi_modal", "text_generation", "summarization"],
            cost_per_1k_tokens=0.007,
            base_latency_ms=650
        )
        self.register_model(
            model_id="llama-3-8b",
            capabilities=["text_generation", "fast_response"],
            cost_per_1k_tokens=0.0002,
            base_latency_ms=150
        )

    def register_model(self, model_id: str, capabilities: List[str], cost_per_1k_tokens: float, base_latency_ms: int):
        """Adds a new AI model to the router's registry."""
        self.model_registry[model_id] = {
            "capabilities": set(capabilities),
            "cost_per_1k_tokens": cost_per_1k_tokens,
            "base_latency_ms": base_latency_ms
        }
        logger.info(f"Registered model: {model_id}")

    def _select_model(self, required_capability: str, strategy: RoutingStrategy) -> Optional[str]:
        """Selects the best model based on the required capability and routing strategy."""
        candidate_models = [m_id for m_id, m_data in self.model_registry.items() if required_capability in m_data["capabilities"]]

        if not candidate_models:
            return None

        if strategy == "lowest_cost":
            return min(candidate_models, key=lambda m_id: self.model_registry[m_id]["cost_per_1k_tokens"])

        if strategy == "lowest_latency":
            return min(candidate_models, key=lambda m_id: self.model_registry[m_id]["base_latency_ms"])

        # "best_capability" or "balanced" can have more complex logic; for now, we'll use a simple heuristic
        # A more advanced version might score models based on capability "strength"
        return sorted(candidate_models, key=lambda m_id: self.model_registry[m_id]["cost_per_1k_tokens"], reverse=True)[0]

    async def _mock_model_call(self, model_id: str, prompt: str) -> Dict:
        """Simulates an API call to a language model."""
        model_data = self.model_registry[model_id]
        latency_ms = model_data["base_latency_ms"] + random.uniform(-50, 100)
        await asyncio.sleep(latency_ms / 1000.0)

        response_tokens = len(prompt.split()) * 1.5 # Simulate a response length
        cost = (len(prompt.split()) + response_tokens) / 1000 * model_data["cost_per_1k_tokens"]

        return {
            "response": f"Mock response from {model_id} for prompt: '{prompt[:30]}...'",
            "cost": cost,
            "latency_ms": latency_ms
        }

    def _update_metrics(self, model_id: str, cost: float, latency_ms: float):
        """Updates the performance metrics for a given model."""
        metrics = self.performance_metrics[model_id]
        total_requests = metrics["requests"] + 1
        metrics["total_cost"] += cost
        # Update average latency using a moving average
        metrics["avg_latency_ms"] = ((metrics["avg_latency_ms"] * metrics["requests"]) + latency_ms) / total_requests
        metrics["requests"] = total_requests

    async def route_prompt(self, prompt: str, required_capability: str, strategy: RoutingStrategy) -> Dict:
        """Routes a single prompt to the best model and returns its response."""
        start_time = time.time()
        model_id = self._select_model(required_capability, strategy)

        if not model_id:
            return {"error": f"No model found with capability: {required_capability}"}

        result = await self._mock_model_call(model_id, prompt)

        self._update_metrics(model_id, result["cost"], result["latency_ms"])

        decision = {
            "prompt": prompt,
            "strategy": strategy,
            "selected_model": model_id,
            "result": result,
            "timestamp": time.time()
        }
        self.routing_history.append(decision)

        return decision

    async def route_and_aggregate(self, prompts: List[Dict], final_aggregator_strategy: RoutingStrategy) -> Dict:
        """
        Routes multiple prompts in parallel, then aggregates their responses into a final summary.
        Example prompt: {"prompt": "Summarize this text...", "capability": "summarization", "strategy": "lowest_cost"}
        """
        tasks = [self.route_prompt(p["prompt"], p["capability"], p["strategy"]) for p in prompts]
        results = await asyncio.gather(*tasks)

        # Filter out errors and collect responses
        successful_responses = [r['result']['response'] for r in results if 'error' not in r]

        if not successful_responses:
            return {"error": "All sub-prompts failed.", "details": results}

        # Aggregate the responses using another model call
        aggregation_prompt = "Synthesize the following pieces of information into a single, coherent answer: \n\n" + "\n\n".join(successful_responses)

        final_decision = await self.route_prompt(
            prompt=aggregation_prompt,
            required_capability="complex_reasoning", # Use a powerful model for aggregation
            strategy=final_aggregator_strategy
        )

        return {
            "final_response": final_decision,
            "intermediate_results": results
        }

    def get_performance_dashboard(self) -> Dict:
        """Returns a summary of performance metrics for all models."""
        return {model_id: {
            "total_cost": round(data["total_cost"], 4),
            "avg_latency_ms": round(data["avg_latency_ms"]),
            "requests": data["requests"]
        } for model_id, data in self.performance_metrics.items()}


if __name__ == '__main__':
    async def main():
        router = PromptRouter()

        print("--- Model Registry ---")
        print(router.model_registry)

        print("\n--- 1. Simple Routing: Find the cheapest model for summarization ---")
        result1 = await router.route_prompt(
            prompt="Summarize the history of the internet in 100 words.",
            required_capability="summarization",
            strategy="lowest_cost"
        )
        print(f"Selected Model: {result1['selected_model']}")
        print(f"Response: {result1['result']['response']}")

        print("\n--- 2. Simple Routing: Find the fastest model for code generation ---")
        result2 = await router.route_prompt(
            prompt="Write a Python function to calculate fibonacci.",
            required_capability="code_generation",
            strategy="lowest_latency"
        )
        print(f"Selected Model: {result2['selected_model']}")
        print(f"Response: {result2['result']['response']}")

        print("\n--- 3. Aggregation: Ask two models for info and a third to synthesize it ---")
        multi_prompts = [
            {"prompt": "What is the capital of France?", "capability": "text_generation", "strategy": "lowest_cost"},
            {"prompt": "What is the population of Paris?", "capability": "text_generation", "strategy": "lowest_latency"}
        ]
        aggregation_result = await router.route_and_aggregate(multi_prompts, final_aggregator_strategy="best_capability")
        print("Final Synthesized Response:")
        print(aggregation_result['final_response']['result']['response'])

        print("\n--- Performance Dashboard ---")
        print(router.get_performance_dashboard())

    asyncio.run(main())
