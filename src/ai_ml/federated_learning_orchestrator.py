"""
Federated Learning Orchestrator Module

This module implements federated learning capabilities for distributed
model training across multiple factories/locations without sharing raw data.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class FederatedLearningOrchestrator:
    """
    Orchestrator for federated learning across distributed factory locations.

    This enables collaborative model training while maintaining data privacy
    and sovereignty across different manufacturing sites.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the federated learning orchestrator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.logger = get_logger(__name__)

        # Cryptographic keys for secure aggregation
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        self.public_key = self.private_key.public_key()

        # Participant registry
        self.participants: Dict[str, Dict[str, Any]] = {}
        self.active_rounds: Dict[str, Dict[str, Any]] = {}

        # Model registry
        self.global_models: Dict[str, Any] = {}
        self.model_versions: Dict[str, List[Dict[str, Any]]] = {}

        self.logger.info("Federated Learning Orchestrator initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "min_participants": 3,
            "max_rounds": 100,
            "aggregation_method": "fedavg",  # fedavg, fedprox, scaffold
            "privacy_budget": 1.0,
            "secure_aggregation": True,
            "differential_privacy": True,
            "noise_multiplier": 0.1,
            "max_grad_norm": 1.0,
            "round_timeout": 3600,  # 1 hour
            "validation_threshold": 0.8,
        }

    async def register_participant(
        self, participant_id: str, metadata: Dict[str, Any]
    ) -> str:
        """
        Register a new participant in the federated learning network.

        Args:
            participant_id: Unique identifier for the participant
            metadata: Participant metadata (location, capabilities, etc.)

        Returns:
            Registration token for authentication
        """
        try:
            # Generate participant token
            token_data = f"{participant_id}:{asyncio.get_event_loop().time()}"
            signature = self.private_key.sign(
                token_data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )

            registration_token = f"{token_data}:{signature.hex()}"

            # Register participant
            self.participants[participant_id] = {
                "metadata": metadata,
                "registration_time": asyncio.get_event_loop().time(),
                "status": "active",
                "token": registration_token,
                "participation_history": [],
                "reputation_score": 1.0,
            }

            self.logger.info(f"Participant {participant_id} registered successfully")
            return registration_token

        except Exception as e:
            self.logger.error(f"Failed to register participant {participant_id}: {e}")
            raise

    async def create_learning_task(
        self,
        task_id: str,
        model_configuration: Dict[str, Any],
        dataset_config: Dict[str, Any],
        participants: List[str],
    ) -> Dict[str, Any]:
        """
        Create a new federated learning task.

        Args:
            task_id: Unique task identifier
            model_configuration: Model architecture and hyperparameters
            dataset_config: Dataset specifications
            participants: List of participant IDs

        Returns:
            Task configuration and metadata
        """
        try:
            # Validate participants
            active_participants = [
                p
                for p in participants
                if p in self.participants and self.participants[p]["status"] == "active"
            ]

            if len(active_participants) < self.config["min_participants"]:
                raise ValueError(
                    f"Insufficient active participants: {len(active_participants)} < {self.config['min_participants']}"
                )

            # Create task configuration
            task_config = {
                "task_id": task_id,
                "model_configuration": model_configuration,
                "dataset_config": dataset_config,
                "participants": active_participants,
                "round_number": 0,
                "status": "initialized",
                "created_at": asyncio.get_event_loop().time(),
                "global_model": None,
                "rounds": [],
            }

            self.active_rounds[task_id] = task_config

            self.logger.info(
                f"Created federated learning task {task_id} with {len(active_participants)} participants"
            )
            return task_config

        except Exception as e:
            self.logger.error(f"Failed to create learning task {task_id}: {e}")
            raise

    async def start_training_round(
        self, task_id: str, global_model_weights: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a new training round for the specified task.

        Args:
            task_id: Task identifier
            global_model_weights: Global model weights for the round

        Returns:
            Round configuration
        """
        try:
            if task_id not in self.active_rounds:
                raise ValueError(f"Task {task_id} not found")

            task = self.active_rounds[task_id]
            round_number = task["round_number"] + 1

            # Create round configuration
            round_config = {
                "round_number": round_number,
                "task_id": task_id,
                "global_model_weights": global_model_weights,
                "participants": task["participants"].copy(),
                "status": "active",
                "started_at": asyncio.get_event_loop().time(),
                "deadline": asyncio.get_event_loop().time()
                + self.config["round_timeout"],
                "submissions": {},
                "aggregation_status": "pending",
            }

            task["rounds"].append(round_config)
            task["round_number"] = round_number
            task["status"] = "training"

            # Notify participants (in real implementation, this would send messages)
            await self._notify_participants_round_start(task_id, round_config)

            self.logger.info(
                f"Started training round {round_number} for task {task_id}"
            )
            return round_config

        except Exception as e:
            self.logger.error(f"Failed to start training round for task {task_id}: {e}")
            raise

    async def submit_model_update(
        self,
        task_id: str,
        participant_id: str,
        model_update: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> bool:
        """
        Submit model update from a participant.

        Args:
            task_id: Task identifier
            participant_id: Participant identifier
            model_update: Model weights/gradients update
            metadata: Training metadata (loss, accuracy, etc.)

        Returns:
            True if submission accepted
        """
        try:
            if task_id not in self.active_rounds:
                raise ValueError(f"Task {task_id} not found")

            task = self.active_rounds[task_id]
            current_round = task["rounds"][-1] if task["rounds"] else None

            if not current_round or current_round["status"] != "active":
                raise ValueError(f"No active round for task {task_id}")

            if participant_id not in current_round["participants"]:
                raise ValueError(
                    f"Participant {participant_id} not authorized for task {task_id}"
                )

            # Validate submission
            await self._validate_model_update(model_update, metadata)

            # Store submission
            current_round["submissions"][participant_id] = {
                "model_update": model_update,
                "metadata": metadata,
                "submitted_at": asyncio.get_event_loop().time(),
                "validated": True,
            }

            # Update participant reputation
            self.participants[participant_id]["participation_history"].append(
                {
                    "task_id": task_id,
                    "round": current_round["round_number"],
                    "submitted_at": asyncio.get_event_loop().time(),
                }
            )

            self.logger.info(
                f"Accepted model update from {participant_id} for task {task_id}"
            )

            # Check if round is complete
            await self._check_round_completion(task_id, current_round)

            return True

        except Exception as e:
            self.logger.error(
                f"Failed to submit model update for {participant_id}: {e}"
            )
            return False

    async def _validate_model_update(
        self, model_update: Dict[str, Any], metadata: Dict[str, Any]
    ) -> None:
        """Validate submitted model update."""
        # Check required fields
        required_fields = ["weights", "gradients", "num_samples"]
        for field in required_fields:
            if field not in model_update:
                raise ValueError(f"Missing required field: {field}")

        # Validate metadata
        if "loss" not in metadata or "accuracy" not in metadata:
            raise ValueError("Missing training metrics in metadata")

        # Check for malicious updates (basic validation)
        if metadata.get("loss", float("inf")) > 1000:  # Unrealistic loss
            raise ValueError("Suspicious training metrics detected")

    async def _check_round_completion(
        self, task_id: str, round_config: Dict[str, Any]
    ) -> None:
        """Check if training round is complete and trigger aggregation."""
        submissions = round_config["submissions"]
        total_participants = len(round_config["participants"])
        submitted_count = len(submissions)

        min_submissions = max(1, int(total_participants * 0.6))  # 60% minimum

        if submitted_count >= min_submissions:
            self.logger.info(
                f"Round {round_config['round_number']} for task {task_id} is complete ({submitted_count}/{total_participants})"
            )
            await self._aggregate_model_updates(task_id, round_config)

    async def _aggregate_model_updates(
        self, task_id: str, round_config: Dict[str, Any]
    ) -> None:
        """
        Aggregate model updates using federated averaging.

        Args:
            task_id: Task identifier
            round_config: Round configuration
        """
        try:
            submissions = round_config["submissions"]

            if not submissions:
                self.logger.warning(f"No submissions to aggregate for task {task_id}")
                return

            # Secure aggregation (simplified)
            if self.config["secure_aggregation"]:
                aggregated_update = await self._secure_aggregation(submissions)
            else:
                aggregated_update = await self._simple_aggregation(submissions)

            # Update global model
            task = self.active_rounds[task_id]
            task["global_model"] = aggregated_update

            # Mark round as complete
            round_config["status"] = "completed"
            round_config["aggregated_at"] = asyncio.get_event_loop().time()
            round_config["aggregation_status"] = "completed"

            # Check stopping criteria
            await self._check_stopping_criteria(task_id)

            self.logger.info(
                f"Successfully aggregated updates for task {task_id} round {round_config['round_number']}"
            )

        except Exception as e:
            self.logger.error(
                f"Failed to aggregate model updates for task {task_id}: {e}"
            )
            round_config["aggregation_status"] = "failed"

    async def _secure_aggregation(self, submissions: Dict[str, Any]) -> Dict[str, Any]:
        """Perform secure aggregation of model updates."""
        # Simplified secure aggregation (in practice, use cryptographic protocols)
        total_samples = sum(
            sub["model_update"]["num_samples"] for sub in submissions.values()
        )

        # Weighted average based on local dataset sizes
        aggregated_weights = {}
        for participant_id, submission in submissions.items():
            weight = submission["model_update"]["num_samples"] / total_samples
            participant_weights = submission["model_update"]["weights"]

            for layer_name, layer_weights in participant_weights.items():
                if layer_name not in aggregated_weights:
                    aggregated_weights[layer_name] = np.zeros_like(layer_weights)

                # Add differential privacy noise if enabled
                if self.config["differential_privacy"]:
                    noise = np.random.normal(
                        0, self.config["noise_multiplier"], layer_weights.shape
                    )
                    layer_weights = layer_weights + noise

                aggregated_weights[layer_name] += weight * layer_weights

        return {"weights": aggregated_weights, "aggregation_method": "secure_fedavg"}

    async def _simple_aggregation(self, submissions: Dict[str, Any]) -> Dict[str, Any]:
        """Perform simple federated averaging."""
        # Simple average (equal weights)
        participant_weights = [
            sub["model_update"]["weights"] for sub in submissions.values()
        ]

        aggregated_weights = {}
        for layer_name in participant_weights[0].keys():
            layer_weights = [pw[layer_name] for pw in participant_weights]
            aggregated_weights[layer_name] = np.mean(layer_weights, axis=0)

        return {"weights": aggregated_weights, "aggregation_method": "simple_average"}

    async def _check_stopping_criteria(self, task_id: str) -> None:
        """Check if training should stop based on convergence criteria."""
        task = self.active_rounds[task_id]

        # Simple stopping criteria (can be enhanced)
        if task["round_number"] >= self.config["max_rounds"]:
            await self._complete_task(task_id, "max_rounds_reached")
        elif task.get("validation_accuracy", 0) >= self.config["validation_threshold"]:
            await self._complete_task(task_id, "convergence_reached")

    async def _complete_task(self, task_id: str, reason: str) -> None:
        """Complete a federated learning task."""
        task = self.active_rounds[task_id]
        task["status"] = "completed"
        task["completed_at"] = asyncio.get_event_loop().time()
        task["completion_reason"] = reason

        # Save final model
        self.global_models[task_id] = task.get("global_model")

        self.logger.info(f"Completed federated learning task {task_id}: {reason}")

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a federated learning task."""
        return self.active_rounds.get(task_id)

    async def get_participant_stats(
        self, participant_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get statistics for a participant."""
        if participant_id not in self.participants:
            return None

        participant = self.participants[participant_id]
        return {
            "participant_id": participant_id,
            "status": participant["status"],
            "registration_time": participant["registration_time"],
            "participation_count": len(participant["participation_history"]),
            "reputation_score": participant["reputation_score"],
            "metadata": participant["metadata"],
        }

    def get_global_model(self, task_id: str) -> Optional[Any]:
        """Get the global model for a completed task."""
        return self.global_models.get(task_id)
