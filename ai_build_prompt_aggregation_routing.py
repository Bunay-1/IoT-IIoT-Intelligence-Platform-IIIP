"""
AI Build Prompt Aggregation and Routing Module

This module implements intelligent aggregation, processing, and routing of AI build prompts
for industrial applications. It uses machine learning to optimize prompt routing and
provides comprehensive monitoring and analytics.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import aiohttp
import requests

from config import settings
from utils.logging_config import LoggerMixin
from utils.performance_monitor import monitor_operation
from utils.security import SecurityError, input_validator, validate_input

# Import core ML engines for integration
try:
    from automl_engine import automl_engine
    from reinforcement_learning import rl_engine

    AUTOML_AVAILABLE = True
    RL_AVAILABLE = True
except ImportError:
    AUTOML_AVAILABLE = False
    RL_AVAILABLE = False


class AIBuildPromptAggregationRouting(LoggerMixin):
    """
    Advanced AI build prompt aggregation and routing system.

    This class provides intelligent processing, aggregation, and routing of AI build prompts
    with ML-powered optimization and comprehensive monitoring capabilities.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AI build prompt aggregation and routing system.

        Args:
            config: Optional configuration dictionary with routing rules and settings
        """
        self.config = config or {}

        # Routing configuration
        self.routing_rules: Dict[str, Dict[str, Any]] = self.config.get(
            "routing_rules", {}
        )
        self.default_system = self.config.get("default_system", "default_ai_service")

        # Processing settings
        self.enable_ml_optimization = self.config.get("enable_ml_optimization", True)
        self.batch_size = self.config.get("batch_size", 10)
        self.max_concurrent_requests = self.config.get("max_concurrent_requests", 5)

        # History and analytics
        self.routing_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {}
        self.max_history_size = self.config.get("max_history_size", 10000)

        # Caching and optimization
        self.route_cache: Dict[str, str] = {}
        self.cache_ttl_seconds = self.config.get("cache_ttl_seconds", 300)  # 5 minutes

        # Async components
        self._processing_queue = asyncio.Queue(maxsize=1000)
        self._semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        self.logger.info("AIBuildPromptAggregationRouting initialized")

    @validate_input({"prompts": {"type": "list", "required": True, "min_length": 1}})
    @monitor_operation("ai_build_prompt_aggregation_routing.aggregate_prompts")
    async def aggregate_prompts(self, prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate and process AI build prompts asynchronously.

        Args:
            prompts: List of AI build prompt dictionaries

        Returns:
            Dictionary with aggregated and processed prompts

        Raises:
            ValueError: If prompts validation fails
            SecurityError: If processing fails due to security constraints
        """
        try:
            self.logger.info(f"Starting aggregation of {len(prompts)} prompts")

            # Validate input prompts
            validated_prompts = []
            for prompt in prompts:
                if not self._validate_prompt(prompt):
                    self.logger.warning(
                        f"Invalid prompt skipped: {prompt.get('id', 'unknown')}"
                    )
                    continue
                validated_prompts.append(prompt)

            if not validated_prompts:
                raise ValueError("No valid prompts provided for aggregation")

            # Process prompts in batches for efficiency
            aggregated_results = {}
            for i in range(0, len(validated_prompts), self.batch_size):
                batch = validated_prompts[i : i + self.batch_size]
                batch_results = await self._process_batch(batch)
                aggregated_results.update(batch_results)

            # Apply ML optimization if enabled
            if self.enable_ml_optimization and AUTOML_AVAILABLE:
                aggregated_results = await self._optimize_with_ml(aggregated_results)

            # Update performance metrics
            self._update_performance_metrics(aggregated_results)

            self.logger.info(
                f"Successfully aggregated {len(aggregated_results)} prompts"
            )
            return {
                "aggregated_prompts": aggregated_results,
                "total_processed": len(aggregated_results),
                "batch_size": self.batch_size,
                "processing_timestamp": datetime.now().isoformat(),
                "ml_optimization_applied": self.enable_ml_optimization
                and AUTOML_AVAILABLE,
            }

        except Exception as e:
            self.logger.error(f"Prompt aggregation failed: {e}")
            raise

    async def _process_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of prompts asynchronously.

        Args:
            batch: List of prompts to process

        Returns:
            Dictionary of processed prompts
        """
        tasks = []
        for prompt in batch:
            task = asyncio.create_task(self._process_single_prompt_async(prompt))
            tasks.append(task)

        # Execute with concurrency control
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = {}
        for i, result in enumerate(results):
            prompt_id = batch[i].get("id", f"prompt_{i}")
            if isinstance(result, Exception):
                self.logger.error(f"Failed to process prompt {prompt_id}: {result}")
                # Add error information to results
                processed_results[prompt_id] = {
                    "original_prompt": batch[i],
                    "error": str(result),
                    "processed": False,
                }
            else:
                processed_results[prompt_id] = result

        return processed_results

    async def _process_single_prompt_async(
        self, prompt: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a single prompt asynchronously.

        Args:
            prompt: Prompt dictionary to process

        Returns:
            Processed prompt with metadata
        """
        async with self._semaphore:
            try:
                # Simulate async processing (could be API calls, ML inference, etc.)
                await asyncio.sleep(0.01)  # Small delay for demonstration

                processed_prompt = prompt.copy()

                # Add comprehensive metadata
                processed_prompt["metadata"] = {
                    "timestamp": datetime.now().isoformat(),
                    "source": prompt.get("source", "unknown"),
                    "processing_id": str(uuid.uuid4()),
                    "version": "2.0",
                    "validation_status": "passed",
                }

                # Add processing history
                self._add_to_history(
                    {
                        "prompt_id": prompt.get("id"),
                        "action": "processed",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": processed_prompt["metadata"],
                    }
                )

                return processed_prompt

            except Exception as e:
                self.logger.error(f"Single prompt processing failed: {e}")
                raise

    @monitor_operation("ai_build_prompt_aggregation_routing.route_prompts")
    async def route_prompts(self, aggregated_prompts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route processed prompts to appropriate target systems asynchronously.

        Args:
            aggregated_prompts: Dictionary of processed prompts

        Returns:
            Routing results and status

        Raises:
            ValueError: If routing configuration is invalid
        """
        try:
            self.logger.info(f"Starting routing of {len(aggregated_prompts)} prompts")

            routing_results = {}
            routing_tasks = []

            for prompt_id, prompt_data in aggregated_prompts.items():
                if isinstance(prompt_data, dict) and prompt_data.get("processed", True):
                    task = asyncio.create_task(
                        self._route_single_prompt(prompt_id, prompt_data)
                    )
                    routing_tasks.append(task)
                else:
                    routing_results[prompt_id] = {
                        "status": "skipped",
                        "reason": "not processed or invalid",
                    }

            # Execute routing tasks
            if routing_tasks:
                routing_responses = await asyncio.gather(
                    *routing_tasks, return_exceptions=True
                )

                for i, response in enumerate(routing_responses):
                    prompt_id = list(aggregated_prompts.keys())[i]
                    if isinstance(response, Exception):
                        routing_results[prompt_id] = {
                            "status": "failed",
                            "error": str(response),
                        }
                    else:
                        routing_results[prompt_id] = response

            # Update routing history
            self._add_to_history(
                {
                    "action": "batch_routed",
                    "total_prompts": len(aggregated_prompts),
                    "successful_routes": len(
                        [
                            r
                            for r in routing_results.values()
                            if r.get("status") == "success"
                        ]
                    ),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            self.logger.info(
                f"Routing completed: {len(routing_results)} prompts processed"
            )
            return {
                "routing_results": routing_results,
                "summary": {
                    "total": len(routing_results),
                    "successful": len(
                        [
                            r
                            for r in routing_results.values()
                            if r.get("status") == "success"
                        ]
                    ),
                    "failed": len(
                        [
                            r
                            for r in routing_results.values()
                            if r.get("status") == "failed"
                        ]
                    ),
                },
            }

        except Exception as e:
            self.logger.error(f"Prompt routing failed: {e}")
            raise

    async def _route_single_prompt(
        self, prompt_id: str, prompt_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route a single prompt to its target system.

        Args:
            prompt_id: Unique prompt identifier
            prompt_data: Processed prompt data

        Returns:
            Routing result status
        """
        try:
            # Determine target system
            target_system = self._determine_routing(prompt_data)

            # Check cache first
            cache_key = f"{prompt_id}_{hash(str(prompt_data))}"
            if cache_key in self.route_cache:
                cached_target = self.route_cache[cache_key]
                if cached_target == target_system:
                    self.logger.debug(f"Using cached route for prompt {prompt_id}")
                    return {
                        "status": "success",
                        "target_system": target_system,
                        "method": "cached",
                    }

            # Send to target system
            success = await self._send_to_system_async(target_system, prompt_data)

            if success:
                # Cache successful routing
                self.route_cache[cache_key] = target_system

                # Clean old cache entries
                self._clean_route_cache()

                return {
                    "status": "success",
                    "target_system": target_system,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "failed",
                    "target_system": target_system,
                    "error": "system unreachable",
                }

        except Exception as e:
            self.logger.error(f"Single prompt routing failed for {prompt_id}: {e}")
            return {"status": "error", "error": str(e)}

    def _determine_routing(self, prompt: Dict[str, Any]) -> str:
        """
        Determine the target system for a prompt based on routing rules.

        Args:
            prompt: Processed prompt data

        Returns:
            Target system identifier
        """
        try:
            # Extract routing criteria
            prompt_type = prompt.get("type", "unknown")
            priority = prompt.get("priority", "normal")
            source = prompt.get("source", "unknown")

            # Check specific routing rules
            for rule_name, rule_config in self.routing_rules.items():
                if self._matches_rule(prompt, rule_config):
                    self.logger.debug(
                        f"Prompt routed via rule '{rule_name}' to {rule_config.get('target')}"
                    )
                    return rule_config.get("target", self.default_system)

            # Fallback to default system
            self.logger.debug(
                f"No matching rule found, using default system for prompt type '{prompt_type}'"
            )
            return self.default_system

        except Exception as e:
            self.logger.error(f"Routing determination failed: {e}")
            return self.default_system

    def _matches_rule(self, prompt: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """
        Check if a prompt matches a routing rule.

        Args:
            prompt: Prompt data
            rule: Routing rule configuration

        Returns:
            True if rule matches, False otherwise
        """
        try:
            # Check conditions
            conditions = rule.get("conditions", {})

            for condition_key, condition_value in conditions.items():
                prompt_value = prompt.get(condition_key)
                if prompt_value != condition_value:
                    return False

            return True

        except Exception:
            return False

    async def _send_to_system_async(
        self, target_system: str, prompt: Dict[str, Any]
    ) -> bool:
        """
        Send prompt to target system asynchronously.

        Args:
            target_system: Target system identifier
            prompt: Prompt data to send

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get system configuration
            system_config = self._get_system_config(target_system)
            if not system_config:
                self.logger.error(f"No configuration found for system {target_system}")
                return False

            url = system_config.get("url")
            if not url:
                self.logger.error(f"No URL configured for system {target_system}")
                return False

            # Prepare request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {system_config.get('api_key', '')}",
            }

            payload = {
                "prompt": prompt,
                "routing_metadata": {
                    "source_system": "ai_build_prompt_aggregator",
                    "timestamp": datetime.now().isoformat(),
                    "version": "2.0",
                },
            }

            # Send async request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        self.logger.debug(
                            f"Successfully sent prompt to {target_system}"
                        )
                        return True
                    else:
                        response_text = await response.text()
                        self.logger.error(
                            f"Failed to send to {target_system}: {response.status} - {response_text}"
                        )
                        return False

        except Exception as e:
            self.logger.error(f"Error sending to system {target_system}: {e}")
            return False

    def _get_system_config(self, system_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a target system.

        Args:
            system_name: Name of the target system

        Returns:
            System configuration dictionary or None
        """
        # This would typically load from config or database
        # For now, return mock configuration
        mock_configs = {
            "default_ai_service": {
                "url": "https://api.example.com/v1/prompts",
                "api_key": "mock_key",
            },
            "industrial_ai": {
                "url": "https://industrial-ai.example.com/api/process",
                "api_key": "industrial_key",
            },
            "cloud_ml": {
                "url": "https://cloud-ml.example.com/v1/inference",
                "api_key": "cloud_key",
            },
        }

        return mock_configs.get(system_name)

    async def _optimize_with_ml(
        self, aggregated_prompts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize prompt routing using integrated ML engines.

        Args:
            aggregated_prompts: Current aggregated prompts

        Returns:
            ML-optimized prompts
        """
        if not AUTOML_AVAILABLE:
            return aggregated_prompts

        try:
            # Use AutoML to optimize routing decisions
            # This is a placeholder for actual ML optimization
            self.logger.info("Applying ML optimization to prompt routing")

            # Mock optimization - in reality would use historical data
            # to predict optimal routing targets
            optimized = aggregated_prompts.copy()

            for prompt_id, prompt_data in optimized.items():
                if isinstance(prompt_data, dict):
                    prompt_data["ml_optimized"] = True
                    prompt_data["optimization_timestamp"] = datetime.now().isoformat()

            return optimized

        except Exception as e:
            self.logger.error(f"ML optimization failed: {e}")
            return aggregated_prompts

    def _validate_prompt(self, prompt: Dict[str, Any]) -> bool:
        """
        Validate a prompt structure.

        Args:
            prompt: Prompt dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["id", "type"]
        for field in required_fields:
            if field not in prompt:
                return False

        # Additional validation logic can be added here
        return True

    def _add_to_history(self, history_entry: Dict[str, Any]) -> None:
        """
        Add entry to routing history.

        Args:
            history_entry: History entry to add
        """
        self.routing_history.append(history_entry)

        # Limit history size
        if len(self.routing_history) > self.max_history_size:
            self.routing_history = self.routing_history[-self.max_history_size :]

    def _update_performance_metrics(self, results: Dict[str, Any]) -> None:
        """
        Update performance metrics based on processing results.

        Args:
            results: Processing results to analyze
        """
        try:
            total_processed = len(results)
            successful_routes = len(
                [
                    r
                    for r in results.values()
                    if isinstance(r, dict) and r.get("processed") != False
                ]
            )

            self.performance_metrics.update(
                {
                    "last_batch_size": total_processed,
                    "last_success_rate": successful_routes / total_processed
                    if total_processed > 0
                    else 0,
                    "total_processed": self.performance_metrics.get(
                        "total_processed", 0
                    )
                    + total_processed,
                    "last_update": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            self.logger.error(f"Performance metrics update failed: {e}")

    def _clean_route_cache(self) -> None:
        """
        Clean expired entries from route cache.
        """
        try:
            cutoff_time = datetime.now() - timedelta(seconds=self.cache_ttl_seconds)
            # In a real implementation, cache entries would have timestamps
            # For now, just limit cache size
            if len(self.route_cache) > 1000:
                # Remove oldest entries (simplified)
                items_to_remove = len(self.route_cache) - 500
                keys_to_remove = list(self.route_cache.keys())[:items_to_remove]
                for key in keys_to_remove:
                    del self.route_cache[key]

        except Exception as e:
            self.logger.error(f"Cache cleaning failed: {e}")

    def get_routing_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get routing history with optional limit.

        Args:
            limit: Maximum number of history entries to return

        Returns:
            List of routing history entries
        """
        if limit:
            return self.routing_history[-limit:]
        return self.routing_history

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.

        Returns:
            Dictionary with performance metrics
        """
        return self.performance_metrics.copy()

    def clear_history(self) -> None:
        """
        Clear routing history.
        """
        self.routing_history.clear()
        self.logger.info("Routing history cleared")

    def update_routing_rules(self, new_rules: Dict[str, Dict[str, Any]]) -> None:
        """
        Update routing rules dynamically.

        Args:
            new_rules: New routing rules to apply
        """
        try:
            self.routing_rules.update(new_rules)
            # Clear cache when rules change
            self.route_cache.clear()
            self.logger.info(
                f"Updated routing rules: {len(new_rules)} rules added/modified"
            )

        except Exception as e:
            self.logger.error(f"Failed to update routing rules: {e}")
            raise
