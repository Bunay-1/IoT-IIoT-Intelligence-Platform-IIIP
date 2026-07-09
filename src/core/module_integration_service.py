"""
Module Integration Service

This service provides centralized integration between all platform modules
and the core AI/ML engines (AutoML and Reinforcement Learning).
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from src.ai_ml.automl_engine import AutoMLEngine
from src.energy_optimization_ai import EnergyOptimizationAI
from src.ai_ml.reinforcement_learning import ReinforcementLearningEngine
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ModuleIntegrationService:
    """
    Centralized service for integrating all platform modules with AI/ML engines.

    This service provides:
    - Unified interface for all modules
    - Integration with AutoML and RL engines
    - Cross-module data sharing
    - Orchestrated processing pipelines
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the module integration service.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Core AI/ML engines
        self.automl_engine = AutoMLEngine()
        # Initialize RL engine with default parameters
        self.rl_engine = ReinforcementLearningEngine(
            parameter_ranges={"speed": (0.1, 10.0), "temperature": (20.0, 200.0)},
            target_metrics=["efficiency", "quality"]
        )

        # Module registry
        self.modules = {}
        self.active_modules = set()

        # Data sharing between modules
        self.shared_data_store = {}

        # Integration pipelines
        self.processing_pipelines = {}

        self.logger.info("Module Integration Service initialized")

    async def register_module(
        self,
        module_name: str,
        module_instance: Any,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a module with the integration service.

        Args:
            module_name: Unique name for the module
            module_instance: Module instance
            config: Module-specific configuration
        """
        try:
            self.modules[module_name] = {
                "instance": module_instance,
                "config": config or {},
                "status": "registered",
                "last_active": None
            }

            # Initialize module if it has init method
            if hasattr(module_instance, "initialize"):
                await module_instance.initialize()

            self.logger.info(f"Module '{module_name}' registered successfully")

        except Exception as e:
            self.logger.error(f"Failed to register module '{module_name}': {e}")
            raise

    async def activate_module(self, module_name: str) -> None:
        """
        Activate a registered module.

        Args:
            module_name: Name of the module to activate
        """
        if module_name not in self.modules:
            raise ValueError(f"Module '{module_name}' not registered")

        try:
            module_info = self.modules[module_name]
            module_instance = module_info["instance"]

            # Start module if it has start method
            if hasattr(module_instance, "start"):
                await module_instance.start()

            module_info["status"] = "active"
            module_info["last_active"] = asyncio.get_event_loop().time()
            self.active_modules.add(module_name)

            self.logger.info(f"Module '{module_name}' activated")

        except Exception as e:
            self.logger.error(f"Failed to activate module '{module_name}': {e}")
            raise

    async def deactivate_module(self, module_name: str) -> None:
        """
        Deactivate an active module.

        Args:
            module_name: Name of the module to deactivate
        """
        if module_name not in self.active_modules:
            self.logger.warning(f"Module '{module_name}' is not active")
            return

        try:
            module_info = self.modules[module_name]
            module_instance = module_info["instance"]

            # Stop module if it has stop method
            if hasattr(module_instance, "stop"):
                await module_instance.stop()

            module_info["status"] = "inactive"
            self.active_modules.discard(module_name)

            self.logger.info(f"Module '{module_name}' deactivated")

        except Exception as e:
            self.logger.error(f"Failed to deactivate module '{module_name}': {e}")
            raise

    async def process_with_automl_integration(
        self,
        data: Any,
        target_column: Optional[str] = None,
        modules_to_use: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process data using AutoML integration across modules.

        Args:
            data: Input data for processing
            target_column: Target column for supervised learning
            modules_to_use: List of modules to include in processing

        Returns:
            Processing results with AutoML insights
        """
        try:
            self.logger.info("Starting AutoML-integrated processing")

            results = {
                "automl_predictions": None,
                "module_results": {},
                "integrated_insights": [],
                "processing_timestamp": asyncio.get_event_loop().time()
            }

            # Get AutoML predictions if applicable
            if hasattr(data, target_column) and target_column:
                try:
                    automl_results = await self.automl_engine.predict(data)
                    results["automl_predictions"] = automl_results
                    results["integrated_insights"].append({
                        "type": "automl_prediction",
                        "data": automl_results
                    })
                except Exception as e:
                    self.logger.warning(f"AutoML prediction failed: {e}")

            # Process with relevant modules
            modules = modules_to_use or list(self.active_modules)

            for module_name in modules:
                if module_name in self.active_modules:
                    try:
                        module_result = await self._process_with_module(
                            module_name, data, {"automl_context": results["automl_predictions"]}
                        )
                        results["module_results"][module_name] = module_result

                        # Extract insights from module results
                        insights = self._extract_module_insights(module_name, module_result)
                        results["integrated_insights"].extend(insights)

                    except Exception as e:
                        self.logger.error(f"Module '{module_name}' processing failed: {e}")
                        results["module_results"][module_name] = {"error": str(e)}

            # Generate cross-module insights
            cross_insights = self._generate_cross_module_insights(results)
            results["integrated_insights"].extend(cross_insights)

            self.logger.info("AutoML-integrated processing completed")
            return results

        except Exception as e:
            self.logger.error(f"AutoML integration processing failed: {e}")
            raise

    async def process_with_rl_integration(
        self,
        current_state: Dict[str, Any],
        modules_to_use: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process using Reinforcement Learning integration.

        Args:
            current_state: Current system state
            modules_to_use: List of modules to include

        Returns:
            RL-optimized processing results
        """
        try:
            self.logger.info("Starting RL-integrated processing")

            results = {
                "rl_optimization": None,
                "module_results": {},
                "optimization_applied": False,
                "processing_timestamp": asyncio.get_event_loop().time()
            }

            # Get RL optimization
            try:
                rl_result = self.rl_engine.optimize_parameters(current_state)
                results["rl_optimization"] = rl_result

                # Apply optimization to state
                optimized_state = {**current_state}
                if "optimized_parameters" in rl_result:
                    optimized_state.update(rl_result["optimized_parameters"])
                    results["optimization_applied"] = True

            except Exception as e:
                self.logger.warning(f"RL optimization failed: {e}")
                optimized_state = current_state

            # Process with modules using optimized state
            modules = modules_to_use or list(self.active_modules)

            for module_name in modules:
                if module_name in self.active_modules:
                    try:
                        module_result = await self._process_with_module(
                            module_name, optimized_state, {"rl_context": results["rl_optimization"]}
                        )
                        results["module_results"][module_name] = module_result

                    except Exception as e:
                        self.logger.error(f"Module '{module_name}' RL processing failed: {e}")
                        results["module_results"][module_name] = {"error": str(e)}

            self.logger.info("RL-integrated processing completed")
            return results

        except Exception as e:
            self.logger.error(f"RL integration processing failed: {e}")
            raise

    async def _process_with_module(
        self,
        module_name: str,
        data: Any,
        context: Dict[str, Any]
    ) -> Any:
        """Process data with a specific module."""
        module_info = self.modules[module_name]
        module_instance = module_info["instance"]

        # Add context to module config
        processing_config = {**module_info["config"], **context}

        # Call appropriate processing method
        if hasattr(module_instance, "process_with_context"):
            result = await module_instance.process_with_context(data, processing_config)
        elif hasattr(module_instance, "process_data"):
            result = await module_instance.process_data(data)
        elif hasattr(module_instance, "predict"):
            result = await module_instance.predict(data)
        else:
            raise AttributeError(f"Module '{module_name}' has no suitable processing method")

        # Update last active timestamp
        module_info["last_active"] = asyncio.get_event_loop().time()

        return result

    def _extract_module_insights(self, module_name: str, module_result: Any) -> List[Dict[str, Any]]:
        """Extract insights from module processing results."""
        insights = []

        try:
            if module_name == "energy_optimization_ai":
                if isinstance(module_result, dict) and "significant_savings" in module_result:
                    for saving in module_result["significant_savings"]:
                        insights.append({
                            "type": "energy_saving_opportunity",
                            "module": module_name,
                            "data": saving
                        })

            elif module_name == "predictive_quality_control":
                if isinstance(module_result, dict) and "defects" in module_result:
                    defect_count = module_result.get("defect_count", 0)
                    if defect_count > 0:
                        insights.append({
                            "type": "quality_issue_detected",
                            "module": module_name,
                            "data": {"defect_count": defect_count}
                        })

            # Add more module-specific insight extraction here

        except Exception as e:
            self.logger.warning(f"Failed to extract insights from {module_name}: {e}")

        return insights

    def _generate_cross_module_insights(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights that span multiple modules."""
        insights = []

        try:
            module_results = results.get("module_results", {})

            # Energy + Quality correlation
            if "energy_optimization_ai" in module_results and "predictive_quality_control" in module_results:
                energy_data = module_results["energy_optimization_ai"]
                quality_data = module_results["predictive_quality_control"]

                # Check if high energy consumption correlates with quality issues
                if (isinstance(energy_data, dict) and
                    isinstance(quality_data, dict) and
                    energy_data.get("current_consumption", 0) > 150 and  # High consumption
                    quality_data.get("defect_rate", 0) > 0.1):  # High defect rate

                    insights.append({
                        "type": "energy_quality_correlation",
                        "severity": "high",
                        "description": "High energy consumption correlated with quality issues",
                        "recommendation": "Investigate process parameters affecting both energy and quality"
                    })

        except Exception as e:
            self.logger.warning(f"Failed to generate cross-module insights: {e}")

        return insights

    async def get_integrated_health_status(self) -> Dict[str, Any]:
        """
        Get integrated health status of all modules and engines.

        Returns:
            Comprehensive health status
        """
        try:
            health_status = {
                "overall_status": "healthy",
                "engines": {},
                "modules": {},
                "issues": []
            }

            # Check AI/ML engines
            try:
                automl_status = "healthy" if self.automl_engine else "unavailable"
                health_status["engines"]["automl"] = automl_status
            except:
                health_status["engines"]["automl"] = "error"

            try:
                rl_status = "healthy" if self.rl_engine else "unavailable"
                health_status["engines"]["reinforcement_learning"] = rl_status
            except:
                health_status["engines"]["reinforcement_learning"] = "error"

            # Check modules
            for module_name, module_info in self.modules.items():
                try:
                    module_instance = module_info["instance"]
                    status = module_info["status"]

                    # Check if module has health check method
                    if hasattr(module_instance, "get_health_status"):
                        module_health = await module_instance.get_health_status()
                        health_status["modules"][module_name] = module_health
                    else:
                        health_status["modules"][module_name] = {
                            "status": status,
                            "last_active": module_info["last_active"]
                        }

                except Exception as e:
                    health_status["modules"][module_name] = {"status": "error", "error": str(e)}
                    health_status["issues"].append(f"Module {module_name}: {str(e)}")

            # Determine overall status
            unhealthy_components = []
            for component_type in ["engines", "modules"]:
                for component_name, component_status in health_status[component_type].items():
                    if isinstance(component_status, dict):
                        if component_status.get("status") not in ["healthy", "active"]:
                            unhealthy_components.append(f"{component_type}.{component_name}")
                    elif component_status not in ["healthy", "available"]:
                        unhealthy_components.append(f"{component_type}.{component_name}")

            if unhealthy_components:
                health_status["overall_status"] = "degraded"
                health_status["issues"].extend(unhealthy_components)

            return health_status

        except Exception as e:
            self.logger.error(f"Failed to get integrated health status: {e}")
            return {
                "overall_status": "error",
                "error": str(e),
                "engines": {},
                "modules": {},
                "issues": [str(e)]
            }

    def share_data_between_modules(
        self,
        source_module: str,
        target_module: str,
        data_key: str,
        data: Any
    ) -> None:
        """
        Share data between modules.

        Args:
            source_module: Module providing the data
            target_module: Module receiving the data
            data_key: Key for the shared data
            data: Data to share
        """
        if source_module not in self.modules or target_module not in self.modules:
            raise ValueError("Source or target module not registered")

        shared_key = f"{source_module}_{target_module}_{data_key}"
        self.shared_data_store[shared_key] = {
            "data": data,
            "timestamp": asyncio.get_event_loop().time(),
            "source": source_module,
            "target": target_module
        }

        self.logger.debug(f"Data shared from {source_module} to {target_module}: {data_key}")

    def get_shared_data(
        self,
        source_module: str,
        target_module: str,
        data_key: str
    ) -> Optional[Any]:
        """
        Retrieve shared data between modules.

        Args:
            source_module: Source module
            target_module: Target module
            data_key: Data key

        Returns:
            Shared data if available
        """
        shared_key = f"{source_module}_{target_module}_{data_key}"
        shared_item = self.shared_data_store.get(shared_key)

        if shared_item:
            return shared_item["data"]

        return None

    async def create_processing_pipeline(
        self,
        pipeline_name: str,
        modules: List[str],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create a processing pipeline with multiple modules.

        Args:
            pipeline_name: Name of the pipeline
            modules: List of module names in processing order
            config: Pipeline configuration
        """
        # Validate modules exist
        for module_name in modules:
            if module_name not in self.modules:
                raise ValueError(f"Module '{module_name}' not registered")

        self.processing_pipelines[pipeline_name] = {
            "modules": modules,
            "config": config or {},
            "created_at": asyncio.get_event_loop().time()
        }

        self.logger.info(f"Processing pipeline '{pipeline_name}' created with modules: {modules}")

    async def execute_pipeline(
        self,
        pipeline_name: str,
        input_data: Any
    ) -> Dict[str, Any]:
        """
        Execute a processing pipeline.

        Args:
            pipeline_name: Name of the pipeline
            input_data: Input data for the pipeline

        Returns:
            Pipeline execution results
        """
        if pipeline_name not in self.processing_pipelines:
            raise ValueError(f"Pipeline '{pipeline_name}' not found")

        pipeline = self.processing_pipelines[pipeline_name]
        results = {
            "pipeline": pipeline_name,
            "module_results": {},
            "execution_time": 0,
            "status": "running"
        }

        start_time = asyncio.get_event_loop().time()

        try:
            current_data = input_data

            for module_name in pipeline["modules"]:
                if module_name in self.active_modules:
                    self.logger.debug(f"Executing pipeline module: {module_name}")

                    module_result = await self._process_with_module(
                        module_name, current_data, pipeline["config"]
                    )

                    results["module_results"][module_name] = module_result

                    # Pass result to next module if needed
                    if hasattr(module_result, "processed_data"):
                        current_data = module_result["processed_data"]
                else:
                    self.logger.warning(f"Module '{module_name}' not active, skipping")

            results["status"] = "completed"

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            self.logger.error(f"Pipeline '{pipeline_name}' execution failed: {e}")

        finally:
            execution_time = asyncio.get_event_loop().time() - start_time
            results["execution_time"] = execution_time

        return results