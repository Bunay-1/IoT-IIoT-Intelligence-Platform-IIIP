"""
Edge AI Optimization Module

This module implements AI optimization for edge computing including:
- Model compression and quantization
- Edge-specific model optimization
- Resource-aware model deployment
- Dynamic model adaptation
- Federated learning support
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from utils.logging_config import get_logger

logger = get_logger(__name__)


class EdgeAIOptimizer:
    """Edge AI optimization system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.optimized_models = {}
        self.model_performance = {}
        self.edge_deployments = {}
        self.federated_learning_sessions = {}
        self.optimization_history = []
        
    def _default_config(self) -> Dict[str, Any]:
        """Default edge AI optimization configuration."""
        return {
            "optimization_techniques": [
                "quantization",
                "pruning",
                "knowledge_distillation",
                "neural_architecture_search"
            ],
            "compression_targets": {
                "model_size_reduction": 0.5,  # 50% reduction
                "inference_latency_target": 50,  # ms
                "memory_usage_target": 512  # MB
            },
            "edge_constraints": {
                "max_model_size_mb": 100,
                "max_inference_time_ms": 100,
                "max_memory_usage_mb": 256,
                "min_accuracy_threshold": 0.85
            },
            "federated_learning": {
                "enabled": True,
                "aggregation_method": "fedavg",
                "privacy_budget": 1.0,
                "min_clients": 3,
                "max_rounds": 100
            },
            "adaptive_optimization": {
                "enabled": True,
                "performance_monitoring": True,
                "auto_retraining": True,
                "model_versioning": True
            }
        }
    
    async def optimize_model_for_edge(
        self,
        model_id: str,
        model_config: Dict[str, Any],
        edge_requirements: Dict[str, Any],
        optimization_targets: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Optimize AI model for edge deployment."""
        try:
            # Validate model and requirements
            validation_result = await self._validate_model_for_optimization(
                model_id, model_config, edge_requirements
            )
            
            if not validation_result["valid"]:
                return {"error": f"Model validation failed: {validation_result['reason']}"}
            
            # Set optimization targets
            targets = optimization_targets or self.config["compression_targets"]
            
            # Create optimization session
            optimization_session = {
                "model_id": model_id,
                "original_config": model_config,
                "edge_requirements": edge_requirements,
                "optimization_targets": targets,
                "techniques_used": [],
                "optimization_results": {},
                "start_time": datetime.now(),
                "status": "in_progress"
            }
            
            # Apply optimization techniques
            optimized_config = model_config.copy()
            
            for technique in self.config["optimization_techniques"]:
                if await self._should_apply_technique(technique, optimized_config, edge_requirements):
                    logger.info(f"Applying optimization technique: {technique}")
                    
                    result = await self._apply_optimization_technique(
                        technique, optimized_config, edge_requirements, targets
                    )
                    
                    if result["success"]:
                        optimized_config = result["optimized_config"]
                        optimization_session["techniques_used"].append(technique)
                        optimization_session["optimization_results"][technique] = result["metrics"]
                    else:
                        logger.warning(f"Optimization technique {technique} failed: {result['error']}")
            
            # Validate optimized model
            validation_result = await self._validate_optimized_model(
                optimized_config, edge_requirements
            )
            
            optimization_session["validation_result"] = validation_result
            optimization_session["end_time"] = datetime.now()
            optimization_session["status"] = "completed"
            
            # Store optimized model
            self.optimized_models[model_id] = {
                "optimized_config": optimized_config,
                "optimization_session": optimization_session,
                "deployment_ready": validation_result["meets_requirements"],
                "created_at": datetime.now()
            }
            
            # Add to optimization history
            self.optimization_history.append(optimization_session)
            
            # Limit history size
            if len(self.optimization_history) > 1000:
                self.optimization_history = self.optimization_history[-500:]
            
            logger.info(f"Model optimized for edge: {model_id}")
            
            return {
                "model_id": model_id,
                "optimized_config": optimized_config,
                "optimization_summary": {
                    "techniques_used": optimization_session["techniques_used"],
                    "results": optimization_session["optimization_results"],
                    "validation": validation_result,
                    "optimization_time": str(optimization_session["end_time"] - optimization_session["start_time"])
                }
            }
            
        except Exception as e:
            logger.error(f"Model optimization failed: {e}")
            return {"error": f"Optimization failed: {e}"}
    
    async def _validate_model_for_optimization(
        self,
        model_id: str,
        model_config: Dict[str, Any],
        edge_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate model for edge optimization."""
        try:
            # Check model type
            model_type = model_config.get("model_type")
            if not model_type:
                return {"valid": False, "reason": "Model type not specified"}
            
            # Check model architecture
            architecture = model_config.get("architecture")
            if not architecture:
                return {"valid": False, "reason": "Model architecture not specified"}
            
            # Check if model is compatible with edge optimization
            compatible_types = ["cnn", "rnn", "transformer", "mlp", "custom"]
            if model_type.lower() not in compatible_types:
                return {"valid": False, "reason": f"Model type {model_type} not supported"}
            
            # Check edge requirements
            required_constraints = edge_requirements.get("constraints", {})
            if not required_constraints:
                return {"valid": False, "reason": "Edge constraints not specified"}
            
            return {"valid": True, "reason": "Model validation passed"}
            
        except Exception as e:
            return {"valid": False, "reason": f"Validation error: {e}"}
    
    async def _should_apply_technique(
        self,
        technique: str,
        model_config: Dict[str, Any],
        edge_requirements: Dict[str, Any]
    ) -> bool:
        """Determine if optimization technique should be applied."""
        constraints = edge_requirements.get("constraints", {})
        
        if technique == "quantization":
            # Apply quantization if model size is large
            model_size = model_config.get("size_mb", 0)
            return model_size > constraints.get("max_model_size_mb", 100) * 0.8
        
        elif technique == "pruning":
            # Apply pruning if model has many parameters
            parameters = model_config.get("parameters", 0)
            return parameters > 1000000  # 1M parameters
        
        elif technique == "knowledge_distillation":
            # Apply distillation if accuracy requirements are high
            accuracy_target = constraints.get("min_accuracy_threshold", 0.85)
            return accuracy_target > 0.9
        
        elif technique == "neural_architecture_search":
            # Apply NAS if deployment constraints are strict
            latency_target = constraints.get("max_inference_time_ms", 100)
            return latency_target < 50
        
        return False
    
    async def _apply_optimization_technique(
        self,
        technique: str,
        model_config: Dict[str, Any],
        edge_requirements: Dict[str, Any],
        targets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply specific optimization technique."""
        try:
            if technique == "quantization":
                return await self._apply_quantization(model_config, edge_requirements, targets)
            elif technique == "pruning":
                return await self._apply_pruning(model_config, edge_requirements, targets)
            elif technique == "knowledge_distillation":
                return await self._apply_knowledge_distillation(model_config, edge_requirements, targets)
            elif technique == "neural_architecture_search":
                return await self._apply_neural_architecture_search(model_config, edge_requirements, targets)
            else:
                return {"success": False, "error": f"Unknown technique: {technique}"}
                
        except Exception as e:
            return {"success": False, "error": f"Technique application failed: {e}"}
    
    async def _apply_quantization(
        self,
        model_config: Dict[str, Any],
        edge_requirements: Dict[str, Any],
        targets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply model quantization."""
        # Simulate quantization process
        original_size = model_config.get("size_mb", 100)
        original_accuracy = model_config.get("accuracy", 0.95)
        
        # Quantization reduces model size by ~75% with minimal accuracy loss
        quantization_factor = 0.25
        accuracy_loss = 0.02  # 2% accuracy loss
        
        optimized_config = model_config.copy()
        optimized_config["size_mb"] = original_size * quantization_factor
        optimized_config["accuracy"] = original_accuracy - accuracy_loss
        optimized_config["quantized"] = True
        optimized_config["bit_precision"] = 8  # INT8 quantization
        
        metrics = {
            "original_size_mb": original_size,
            "optimized_size_mb": optimized_config["size_mb"],
            "size_reduction": (original_size - optimized_config["size_mb"]) / original_size,
            "original_accuracy": original_accuracy,
            "optimized_accuracy": optimized_config["accuracy"],
            "accuracy_loss": accuracy_loss,
            "bit_precision": 8
        }
        
        return {
            "success": True,
            "optimized_config": optimized_config,
            "metrics": metrics
        }
    
    async def _apply_pruning(
        self,
        model_config: Dict[str, Any],
        edge_requirements: Dict[str, Any],
        targets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply model pruning."""
        # Simulate pruning process
        original_parameters = model_config.get("parameters", 1000000)
        original_size = model_config.get("size_mb", 100)
        original_accuracy = model_config.get("accuracy", 0.95)
        
        # Pruning removes ~50% of parameters with small accuracy loss
        pruning_ratio = 0.5
        accuracy_loss = 0.01  # 1% accuracy loss
        
        optimized_config = model_config.copy()
        optimized_config["parameters"] = int(original_parameters * (1 - pruning_ratio))
        optimized_config["size_mb"] = original_size * (1 - pruning_ratio * 0.8)  # Size reduction is less than parameter reduction
        optimized_config["accuracy"] = original_accuracy - accuracy_loss
        optimized_config["pruned"] = True
        optimized_config["pruning_ratio"] = pruning_ratio
        
        metrics = {
            "original_parameters": original_parameters,
            "optimized_parameters": optimized_config["parameters"],
            "parameter_reduction": pruning_ratio,
            "original_size_mb": original_size,
            "optimized_size_mb": optimized_config["size_mb"],
            "size_reduction": (original_size - optimized_config["size_mb"]) / original_size,
            "original_accuracy": original_accuracy,
            "optimized_accuracy": optimized_config["accuracy"],
            "accuracy_loss": accuracy_loss
        }
        
        return {
            "success": True,
            "optimized_config": optimized_config,
            "metrics": metrics
        }
    
    async def _apply_knowledge_distillation(
        self,
        model_config: Dict[str, Any],
        edge_requirements: Dict[str, Any],
        targets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply knowledge distillation."""
        # Simulate knowledge distillation process
        original_size = model_config.get("size_mb", 100)
        original_accuracy = model_config.get("accuracy", 0.95)
        
        # Distillation creates smaller student model
        student_size_ratio = 0.3  # Student model is 30% of teacher size
        accuracy_retention = 0.97  # Student retains 97% of teacher accuracy
        
        optimized_config = model_config.copy()
        optimized_config["size_mb"] = original_size * student_size_ratio
        optimized_config["accuracy"] = original_accuracy * accuracy_retention
        optimized_config["distilled"] = True
        optimized_config["model_type"] = "student_model"
        optimized_config["teacher_model"] = model_config.get("model_id", "unknown")
        
        metrics = {
            "original_size_mb": original_size,
            "optimized_size_mb": optimized_config["size_mb"],
            "size_reduction": 1 - student_size_ratio,
            "original_accuracy": original_accuracy,
            "optimized_accuracy": optimized_config["accuracy"],
            "accuracy_retention": accuracy_retention,
            "student_teacher_ratio": student_size_ratio
        }
        
        return {
            "success": True,
            "optimized_config": optimized_config,
            "metrics": metrics
        }
    
    async def _apply_neural_architecture_search(
        self,
        model_config: Dict[str, Any],
        edge_requirements: Dict[str, Any],
        targets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply neural architecture search."""
        # Simulate NAS process
        original_size = model_config.get("size_mb", 100)
        original_latency = model_config.get("inference_time_ms", 100)
        original_accuracy = model_config.get("accuracy", 0.95)
        
        # NAS finds optimal architecture for constraints
        size_reduction = 0.4  # 40% size reduction
        latency_reduction = 0.6  # 60% latency reduction
        accuracy_change = -0.005  # Small accuracy loss
        
        optimized_config = model_config.copy()
        optimized_config["size_mb"] = original_size * (1 - size_reduction)
        optimized_config["inference_time_ms"] = original_latency * (1 - latency_reduction)
        optimized_config["accuracy"] = original_accuracy + accuracy_change
        optimized_config["nas_optimized"] = True
        optimized_config["architecture"] = "nas_discovered"
        
        metrics = {
            "original_size_mb": original_size,
            "optimized_size_mb": optimized_config["size_mb"],
            "size_reduction": size_reduction,
            "original_latency_ms": original_latency,
            "optimized_latency_ms": optimized_config["inference_time_ms"],
            "latency_reduction": latency_reduction,
            "original_accuracy": original_accuracy,
            "optimized_accuracy": optimized_config["accuracy"],
            "accuracy_change": accuracy_change
        }
        
        return {
            "success": True,
            "optimized_config": optimized_config,
            "metrics": metrics
        }
    
    async def _validate_optimized_model(
        self,
        optimized_config: Dict[str, Any],
        edge_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate optimized model against edge requirements."""
        constraints = edge_requirements.get("constraints", {})
        
        # Check size constraint
        model_size = optimized_config.get("size_mb", 0)
        max_size = constraints.get("max_model_size_mb", 100)
        size_ok = model_size <= max_size
        
        # Check latency constraint
        inference_time = optimized_config.get("inference_time_ms", 0)
        max_latency = constraints.get("max_inference_time_ms", 100)
        latency_ok = inference_time <= max_latency
        
        # Check memory constraint
        memory_usage = optimized_config.get("memory_usage_mb", 0)
        max_memory = constraints.get("max_memory_usage_mb", 256)
        memory_ok = memory_usage <= max_memory
        
        # Check accuracy constraint
        accuracy = optimized_config.get("accuracy", 0)
        min_accuracy = constraints.get("min_accuracy_threshold", 0.85)
        accuracy_ok = accuracy >= min_accuracy
        
        meets_requirements = size_ok and latency_ok and memory_ok and accuracy_ok
        
        return {
            "meets_requirements": meets_requirements,
            "size_constraint_met": size_ok,
            "latency_constraint_met": latency_ok,
            "memory_constraint_met": memory_ok,
            "accuracy_constraint_met": accuracy_ok,
            "details": {
                "model_size_mb": model_size,
                "max_size_mb": max_size,
                "inference_time_ms": inference_time,
                "max_latency_ms": max_latency,
                "memory_usage_mb": memory_usage,
                "max_memory_mb": max_memory,
                "accuracy": accuracy,
                "min_accuracy": min_accuracy
            }
        }
    
    async def deploy_model_to_edge(
        self,
        model_id: str,
        edge_nodes: List[str],
        deployment_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Deploy optimized model to edge nodes."""
        if model_id not in self.optimized_models:
            return {"error": "Model not optimized for edge deployment"}
        
        optimized_model = self.optimized_models[model_id]
        if not optimized_model["deployment_ready"]:
            return {"error": "Model does not meet edge requirements"}
        
        deployment_session = {
            "model_id": model_id,
            "edge_nodes": edge_nodes,
            "deployment_config": deployment_config or {},
            "deployment_results": {},
            "start_time": datetime.now(),
            "status": "in_progress"
        }
        
        # Deploy to each edge node
        successful_deployments = []
        failed_deployments = []
        
        for node_id in edge_nodes:
            try:
                # Simulate deployment process
                deployment_result = await self._deploy_to_single_node(
                    model_id, node_id, optimized_model["optimized_config"], deployment_config
                )
                
                deployment_session["deployment_results"][node_id] = deployment_result
                
                if deployment_result["success"]:
                    successful_deployments.append(node_id)
                else:
                    failed_deployments.append(node_id)
                    
            except Exception as e:
                deployment_session["deployment_results"][node_id] = {
                    "success": False,
                    "error": str(e)
                }
                failed_deployments.append(node_id)
        
        deployment_session["end_time"] = datetime.now()
        deployment_session["status"] = "completed"
        deployment_session["successful_deployments"] = successful_deployments
        deployment_session["failed_deployments"] = failed_deployments
        
        # Store deployment
        self.edge_deployments[f"{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"] = deployment_session
        
        logger.info(f"Model deployed to edge: {model_id} - {len(successful_deployments)}/{len(edge_nodes)} nodes")
        
        return {
            "model_id": model_id,
            "deployment_summary": {
                "total_nodes": len(edge_nodes),
                "successful_deployments": len(successful_deployments),
                "failed_deployments": len(failed_deployments),
                "success_rate": len(successful_deployments) / len(edge_nodes),
                "deployment_time": str(deployment_session["end_time"] - deployment_session["start_time"])
            },
            "deployment_results": deployment_session["deployment_results"]
        }
    
    async def _deploy_to_single_node(
        self,
        model_id: str,
        node_id: str,
        model_config: Dict[str, Any],
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy model to a single edge node."""
        # Simulate deployment process
        await asyncio.sleep(0.1)  # Simulate deployment time
        
        # Check node capabilities
        node_capabilities = await self._get_node_capabilities(node_id)
        
        # Validate compatibility
        model_size = model_config.get("size_mb", 0)
        node_storage = node_capabilities.get("available_storage_mb", 0)
        
        if model_size > node_storage:
            return {
                "success": False,
                "error": f"Insufficient storage: {model_size}MB > {node_storage}MB"
            }
        
        # Simulate successful deployment
        return {
            "success": True,
            "node_id": node_id,
            "model_id": model_id,
            "deployment_time": datetime.now(),
            "model_size_mb": model_size,
            "node_capabilities": node_capabilities
        }
    
    async def _get_node_capabilities(self, node_id: str) -> Dict[str, Any]:
        """Get edge node capabilities."""
        # Simulate node capabilities
        return {
            "node_id": node_id,
            "cpu_cores": 4,
            "memory_mb": 2048,
            "available_storage_mb": 1024,
            "gpu_available": False,
            "network_bandwidth_mbps": 100,
            "supported_frameworks": ["tensorflow", "pytorch", "onnx"]
        }
    
    async def start_federated_learning_session(
        self,
        model_id: str,
        client_nodes: List[str],
        federated_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Start federated learning session."""
        if model_id not in self.optimized_models:
            return {"error": "Model not found"}
        
        config = federated_config or self.config["federated_learning"]
        
        if len(client_nodes) < config["min_clients"]:
            return {"error": f"Insufficient clients: {len(client_nodes)} < {config['min_clients']}"}
        
        session_id = f"fl_{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        federated_session = {
            "session_id": session_id,
            "model_id": model_id,
            "client_nodes": client_nodes,
            "config": config,
            "current_round": 0,
            "max_rounds": config["max_rounds"],
            "aggregation_method": config["aggregation_method"],
            "model_updates": {},
            "global_model": self.optimized_models[model_id]["optimized_config"],
            "start_time": datetime.now(),
            "status": "active"
        }
        
        self.federated_learning_sessions[session_id] = federated_session
        
        logger.info(f"Federated learning session started: {session_id}")
        
        return {
            "session_id": session_id,
            "model_id": model_id,
            "client_nodes": client_nodes,
            "config": config,
            "status": "started"
        }
    
    async def aggregate_federated_updates(
        self,
        session_id: str,
        client_updates: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate federated learning updates."""
        if session_id not in self.federated_learning_sessions:
            return {"error": "Federated learning session not found"}
        
        session = self.federated_learning_sessions[session_id]
        
        # Store client updates
        session["model_updates"].update(client_updates)
        
        # Apply aggregation method
        if session["aggregation_method"] == "fedavg":
            aggregated_model = await self._federated_averaging(client_updates)
        elif session["aggregation_method"] == "fedprox":
            aggregated_model = await self._federated_proximal(client_updates)
        else:
            return {"error": f"Unknown aggregation method: {session['aggregation_method']}"}
        
        # Update global model
        session["global_model"] = aggregated_model
        session["current_round"] += 1
        
        # Check if training is complete
        if session["current_round"] >= session["max_rounds"]:
            session["status"] = "completed"
            session["end_time"] = datetime.now()
        
        logger.info(f"Federated update aggregated: {session_id} - Round {session['current_round']}")
        
        return {
            "session_id": session_id,
            "current_round": session["current_round"],
            "max_rounds": session["max_rounds"],
            "status": session["status"],
            "aggregated_model": aggregated_model,
            "clients_participated": len(client_updates)
        }
    
    async def _federated_averaging(self, client_updates: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Apply federated averaging aggregation."""
        # Simulate federated averaging
        # In real implementation, would average model weights
        
        num_clients = len(client_updates)
        if num_clients == 0:
            return {}
        
        # Average accuracy across clients
        accuracies = [update.get("accuracy", 0) for update in client_updates.values()]
        avg_accuracy = sum(accuracies) / len(accuracies)
        
        # Average model size
        sizes = [update.get("model_size_mb", 0) for update in client_updates.values()]
        avg_size = sum(sizes) / len(sizes)
        
        return {
            "aggregation_method": "fedavg",
            "num_clients": num_clients,
            "average_accuracy": avg_accuracy,
            "average_model_size_mb": avg_size,
            "aggregated_at": datetime.now()
        }
    
    async def _federated_proximal(self, client_updates: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Apply federated proximal aggregation."""
        # Simulate federated proximal (similar to FedAvg but with proximity constraint)
        result = await self._federated_averaging(client_updates)
        result["aggregation_method"] = "fedprox"
        result["proximity_constraint"] = 0.01
        
        return result
    
    async def monitor_edge_model_performance(
        self,
        model_id: str,
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Monitor and analyze edge model performance."""
        if model_id not in self.optimized_models:
            return {"error": "Model not found"}
        
        # Store performance data
        if model_id not in self.model_performance:
            self.model_performance[model_id] = {
                "performance_history": [],
                "alerts": [],
                "optimization_suggestions": []
            }
        
        performance_entry = {
            "timestamp": datetime.now(),
            "metrics": performance_data,
            "node_id": performance_data.get("node_id", "unknown")
        }
        
        self.model_performance[model_id]["performance_history"].append(performance_entry)
        
        # Limit history size
        if len(self.model_performance[model_id]["performance_history"]) > 1000:
            self.model_performance[model_id]["performance_history"] = self.model_performance[model_id]["performance_history"][-500:]
        
        # Analyze performance
        analysis = await self._analyze_performance_trends(model_id, performance_data)
        
        # Generate optimization suggestions
        suggestions = await self._generate_optimization_suggestions(model_id, analysis)
        
        self.model_performance[model_id]["optimization_suggestions"] = suggestions
        
        return {
            "model_id": model_id,
            "performance_analysis": analysis,
            "optimization_suggestions": suggestions,
            "monitoring_timestamp": datetime.now()
        }
    
    async def _analyze_performance_trends(
        self,
        model_id: str,
        current_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze performance trends for model."""
        performance_history = self.model_performance[model_id]["performance_history"]
        
        if len(performance_history) < 10:
            return {"status": "insufficient_data"}
        
        # Calculate recent averages
        recent_entries = performance_history[-10:]
        
        avg_accuracy = sum(
            entry["metrics"].get("accuracy", 0) for entry in recent_entries
        ) / len(recent_entries)
        
        avg_latency = sum(
            entry["metrics"].get("inference_time_ms", 0) for entry in recent_entries
        ) / len(recent_entries)
        
        avg_memory = sum(
            entry["metrics"].get("memory_usage_mb", 0) for entry in recent_entries
        ) / len(recent_entries)
        
        # Detect degradation
        original_accuracy = self.optimized_models[model_id]["optimized_config"].get("accuracy", 0)
        accuracy_degradation = (original_accuracy - avg_accuracy) / original_accuracy
        
        return {
            "status": "analyzed",
            "recent_performance": {
                "average_accuracy": avg_accuracy,
                "average_latency_ms": avg_latency,
                "average_memory_mb": avg_memory
            },
            "accuracy_degradation": accuracy_degradation,
            "performance_stable": accuracy_degradation < 0.05,  # 5% degradation threshold
            "data_points": len(recent_entries)
        }
    
    async def _generate_optimization_suggestions(
        self,
        model_id: str,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate optimization suggestions based on performance analysis."""
        suggestions = []
        
        if analysis["status"] != "analyzed":
            return suggestions
        
        recent_perf = analysis["recent_performance"]
        
        # Accuracy degradation suggestions
        if analysis["accuracy_degradation"] > 0.05:
            suggestions.append({
                "type": "retraining_needed",
                "priority": "high",
                "description": "Model accuracy degraded significantly",
                "suggested_action": "retrain_with_new_data",
                "expected_improvement": "accuracy_restoration"
            })
        
        # Latency suggestions
        if recent_perf["average_latency_ms"] > 80:
            suggestions.append({
                "type": "performance_optimization",
                "priority": "medium",
                "description": "High inference latency detected",
                "suggested_action": "apply_additional_quantization",
                "expected_improvement": "latency_reduction_20_30"
            })
        
        # Memory usage suggestions
        if recent_perf["average_memory_mb"] > 200:
            suggestions.append({
                "type": "memory_optimization",
                "priority": "medium",
                "description": "High memory usage detected",
                "suggested_action": "apply_model_pruning",
                "expected_improvement": "memory_reduction_30_40"
            })
        
        return suggestions
    
    def get_optimization_metrics(self) -> Dict[str, Any]:
        """Get edge AI optimization metrics."""
        return {
            "total_optimized_models": len(self.optimized_models),
            "active_deployments": len(self.edge_deployments),
            "active_federated_sessions": len([
                s for s in self.federated_learning_sessions.values()
                if s["status"] == "active"
            ]),
            "total_optimization_history": len(self.optimization_history),
            "models_monitored": len(self.model_performance),
            "average_optimization_time": self._calculate_average_optimization_time(),
            "optimization_success_rate": self._calculate_optimization_success_rate()
        }
    
    def _calculate_average_optimization_time(self) -> float:
        """Calculate average optimization time."""
        if not self.optimization_history:
            return 0.0
        
        total_time = sum(
            (session["end_time"] - session["start_time"]).total_seconds()
            for session in self.optimization_history
            if session["status"] == "completed"
        )
        
        completed_sessions = len([
            session for session in self.optimization_history
            if session["status"] == "completed"
        ])
        
        return total_time / completed_sessions if completed_sessions > 0 else 0.0
    
    def _calculate_optimization_success_rate(self) -> float:
        """Calculate optimization success rate."""
        if not self.optimization_history:
            return 0.0
        
        successful = len([
            session for session in self.optimization_history
            if session["status"] == "completed" and 
            session.get("validation_result", {}).get("meets_requirements", False)
        ])
        
        return successful / len(self.optimization_history)


# Global edge AI optimizer instance
edge_ai_optimizer = EdgeAIOptimizer()


async def optimize_model_for_edge_deployment(
    model_id: str,
    model_config: Dict[str, Any],
    edge_requirements: Dict[str, Any],
    optimization_targets: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Optimize AI model for edge deployment."""
    return await edge_ai_optimizer.optimize_model_for_edge(
        model_id, model_config, edge_requirements, optimization_targets
    )


async def deploy_optimized_model_to_edge(
    model_id: str,
    edge_nodes: List[str],
    deployment_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Deploy optimized model to edge nodes."""
    return await edge_ai_optimizer.deploy_model_to_edge(
        model_id, edge_nodes, deployment_config
    )


async def start_edge_federated_learning(
    model_id: str,
    client_nodes: List[str],
    federated_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Start federated learning session."""
    return await edge_ai_optimizer.start_federated_learning_session(
        model_id, client_nodes, federated_config
    )


async def aggregate_edge_federated_updates(
    session_id: str,
    client_updates: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """Aggregate federated learning updates."""
    return await edge_ai_optimizer.aggregate_federated_updates(
        session_id, client_updates
    )


async def monitor_edge_model_performance(
    model_id: str,
    performance_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Monitor edge model performance."""
    return await edge_ai_optimizer.monitor_edge_model_performance(
        model_id, performance_data
    )


def get_edge_ai_optimization_metrics() -> Dict[str, Any]:
    """Get edge AI optimization metrics."""
    return edge_ai_optimizer.get_optimization_metrics()
