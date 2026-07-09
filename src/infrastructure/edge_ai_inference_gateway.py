"""
Edge AI Inference Gateway Module

This module provides AI inference capabilities at the edge, enabling
low-latency predictions and offline operation for industrial applications.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union

import numpy as np

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class EdgeInferenceError(Exception):
    """Base exception for edge inference errors."""

    pass


class ModelLoadError(EdgeInferenceError):
    """Raised when model loading fails."""

    pass


class InferenceError(EdgeInferenceError):
    """Raised when inference fails."""

    pass


class EdgeAIInferenceGateway:
    """
    Edge AI Inference Gateway for low-latency AI predictions.

    Provides optimized model loading, inference execution, and resource
    management for edge computing scenarios in industrial environments.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Edge AI Inference Gateway.

        Args:
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.logger = get_logger(__name__)

        # Model management
        self.loaded_models: Dict[str, Dict[str, Any]] = {}
        self.model_cache: Dict[str, Any] = {}

        # Performance tracking
        self.inference_stats: Dict[str, List[float]] = {}
        self.resource_usage: Dict[str, Any] = {}

        # Hardware acceleration
        self.hardware_accelerators = self._detect_hardware()

        # Offline capabilities
        self.offline_mode = self.config.get("offline_mode", False)
        self.offline_storage = self.config.get("offline_storage", "./offline_models")

        self.logger.info("Edge AI Inference Gateway initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "max_models_in_memory": 5,
            "model_cache_ttl": 3600,  # 1 hour
            "inference_timeout": 5.0,  # seconds
            "batch_size_limit": 32,
            "memory_limit_mb": 512,
            "cpu_threads": 2,
            "offline_mode": False,
            "offline_storage": "./offline_models",
            "auto_quantization": True,
            "precision": "fp32",  # fp32, fp16, int8
            "optimization_level": "balanced",  # speed, accuracy, balanced
        }

    def _detect_hardware(self) -> Dict[str, bool]:
        """Detect available hardware accelerators."""
        accelerators = {
            "cpu": True,  # Always available
            "gpu": False,
            "tpu": False,
            "npu": False,
        }

        try:
            # Check for CUDA GPU
            import torch

            accelerators["gpu"] = torch.cuda.is_available()
        except ImportError:
            pass

        try:
            # Check for TPU (Google Coral, etc.)
            import tflite_runtime.interpreter as tflite

            # TPU detection logic would go here
            accelerators["tpu"] = False  # Placeholder
        except ImportError:
            pass

        try:
            # Check for NPU (Intel Neural Processing Unit)
            # NPU detection logic would go here
            accelerators["npu"] = False  # Placeholder
        except:
            pass

        self.logger.info(f"Detected hardware accelerators: {accelerators}")
        return accelerators

    async def load_model(
        self,
        model_id: str,
        model_path: str,
        model_config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Load an AI model for inference.

        Args:
            model_id: Unique identifier for the model
            model_path: Path to model file
            model_config: Model-specific configuration

        Returns:
            True if loading successful
        """
        try:
            self.logger.info(f"Loading model {model_id} from {model_path}")

            config = model_config or {}
            model_format = self._detect_model_format(model_path)

            # Load model based on format
            if model_format == "pytorch":
                model = await self._load_pytorch_model(model_path, config)
            elif model_format == "tensorflow":
                model = await self._load_tensorflow_model(model_path, config)
            elif model_format == "onnx":
                model = await self._load_onnx_model(model_path, config)
            elif model_format == "tflite":
                model = await self._load_tflite_model(model_path, config)
            else:
                raise ModelLoadError(f"Unsupported model format: {model_format}")

            # Optimize model for edge deployment
            if self.config["auto_quantization"]:
                model = await self._optimize_model(model, model_format, config)

            # Store model info
            self.loaded_models[model_id] = {
                "model": model,
                "format": model_format,
                "config": config,
                "loaded_at": time.time(),
                "inference_count": 0,
                "avg_inference_time": 0.0,
                "memory_usage": await self._estimate_model_memory(model),
            }

            # Initialize stats tracking
            self.inference_stats[model_id] = []

            # Manage memory (unload least recently used models if needed)
            await self._manage_memory()

            self.logger.info(f"Successfully loaded model {model_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load model {model_id}: {e}")
            raise ModelLoadError(f"Failed to load model {model_id}: {e}") from e

    def _detect_model_format(self, model_path: str) -> str:
        """Detect model format from file path."""
        if model_path.endswith((".pt", ".pth", ".torch")):
            return "pytorch"
        elif model_path.endswith((".pb", ".h5", ".savedmodel")):
            return "tensorflow"
        elif model_path.endswith(".onnx"):
            return "onnx"
        elif model_path.endswith(".tflite"):
            return "tflite"
        else:
            # Try to infer from content or raise error
            raise ModelLoadError(f"Cannot detect model format for {model_path}")

    async def _load_pytorch_model(self, model_path: str, config: Dict[str, Any]) -> Any:
        """Load PyTorch model."""
        try:
            import torch
            from torch import nn

            # Load model
            model = torch.load(model_path, map_location="cpu")
            model.eval()

            # Move to appropriate device
            device = self._get_optimal_device()
            if isinstance(model, nn.Module):
                model = model.to(device)

            return {"model": model, "device": device, "framework": "pytorch"}

        except ImportError:
            raise ModelLoadError("PyTorch not available")
        except Exception as e:
            raise ModelLoadError(f"PyTorch model loading failed: {e}")

    async def _load_tensorflow_model(
        self, model_path: str, config: Dict[str, Any]
    ) -> Any:
        """Load TensorFlow model."""
        try:
            import tensorflow as tf

            # Load model based on format
            if model_path.endswith(".pb"):
                model = tf.saved_model.load(model_path)
            elif model_path.endswith(".h5"):
                model = tf.keras.models.load_model(model_path)
            else:
                model = tf.saved_model.load(model_path)

            return {"model": model, "framework": "tensorflow"}

        except ImportError:
            raise ModelLoadError("TensorFlow not available")
        except Exception as e:
            raise ModelLoadError(f"TensorFlow model loading failed: {e}")

    async def _load_onnx_model(self, model_path: str, config: Dict[str, Any]) -> Any:
        """Load ONNX model."""
        try:
            import onnxruntime as ort

            # Create inference session with optimizations
            providers = self._get_onnx_providers()
            session = ort.InferenceSession(model_path, providers=providers)

            return {"session": session, "framework": "onnx"}

        except ImportError:
            raise ModelLoadError("ONNX Runtime not available")
        except Exception as e:
            raise ModelLoadError(f"ONNX model loading failed: {e}")

    async def _load_tflite_model(self, model_path: str, config: Dict[str, Any]) -> Any:
        """Load TensorFlow Lite model."""
        try:
            import tflite_runtime.interpreter as tflite

            # Create interpreter
            interpreter = tflite.Interpreter(model_path=model_path)

            # Allocate tensors
            interpreter.allocate_tensors()

            return {"interpreter": interpreter, "framework": "tflite"}

        except ImportError:
            raise ModelLoadError("TensorFlow Lite not available")
        except Exception as e:
            raise ModelLoadError(f"TFLite model loading failed: {e}")

    def _get_optimal_device(self) -> str:
        """Get optimal device for inference."""
        if self.hardware_accelerators["gpu"]:
            return "cuda"
        elif self.hardware_accelerators["tpu"]:
            return "tpu"
        else:
            return "cpu"

    def _get_onnx_providers(self) -> List[str]:
        """Get ONNX execution providers in order of preference."""
        providers = []

        if self.hardware_accelerators["gpu"]:
            providers.append("CUDAExecutionProvider")

        if self.hardware_accelerators["tpu"]:
            providers.append("TPUExecutionProvider")

        # CPU is always available as fallback
        providers.append("CPUExecutionProvider")

        return providers

    async def _optimize_model(
        self, model: Any, model_format: str, config: Dict[str, Any]
    ) -> Any:
        """Optimize model for edge deployment."""
        try:
            optimization_level = self.config["optimization_level"]

            if model_format == "pytorch":
                return await self._optimize_pytorch_model(model, optimization_level)
            elif model_format == "tensorflow":
                return await self._optimize_tensorflow_model(model, optimization_level)
            elif model_format == "onnx":
                return await self._optimize_onnx_model(model, optimization_level)
            elif model_format == "tflite":
                return model  # Already optimized
            else:
                return model

        except Exception as e:
            self.logger.warning(f"Model optimization failed: {e}")
            return model

    async def _optimize_pytorch_model(self, model_data: Dict, level: str) -> Dict:
        """Optimize PyTorch model."""
        try:
            import torch
            from torch import nn

            model = model_data["model"]

            if isinstance(model, nn.Module):
                # Apply optimizations based on level
                if level in ["speed", "balanced"]:
                    model = torch.jit.script(model)  # JIT compilation

                if level == "speed":
                    # Additional speed optimizations
                    pass

            return {**model_data, "optimized": True}

        except Exception as e:
            self.logger.warning(f"PyTorch optimization failed: {e}")
            return model_data

    async def _optimize_tensorflow_model(self, model_data: Dict, level: str) -> Dict:
        """Optimize TensorFlow model."""
        try:
            import tensorflow as tf

            # TensorFlow optimizations would go here
            # This is a placeholder for actual optimization logic

            return {**model_data, "optimized": True}

        except Exception as e:
            self.logger.warning(f"TensorFlow optimization failed: {e}")
            return model_data

    async def _optimize_onnx_model(self, model_data: Dict, level: str) -> Dict:
        """Optimize ONNX model."""
        try:
            # ONNX optimizations would go here
            return {**model_data, "optimized": True}

        except Exception as e:
            self.logger.warning(f"ONNX optimization failed: {e}")
            return model_data

    async def _estimate_model_memory(self, model: Any) -> int:
        """Estimate memory usage of model."""
        try:
            # Rough estimation - in practice this would be more sophisticated
            if hasattr(model, "parameters"):
                # PyTorch model
                param_count = sum(p.numel() for p in model.parameters())
                return param_count * 4  # Assume 4 bytes per parameter
            else:
                return 50 * 1024 * 1024  # 50MB default estimate

        except Exception:
            return 50 * 1024 * 1024  # 50MB default

    async def _manage_memory(self) -> None:
        """Manage memory by unloading least recently used models."""
        try:
            max_models = self.config["max_models_in_memory"]

            if len(self.loaded_models) <= max_models:
                return

            # Sort by last access time (oldest first)
            sorted_models = sorted(
                self.loaded_models.items(), key=lambda x: x[1]["loaded_at"]
            )

            # Unload oldest models
            models_to_unload = sorted_models[: len(sorted_models) - max_models]

            for model_id, _ in models_to_unload:
                await self.unload_model(model_id)
                self.logger.info(f"Unloaded model {model_id} due to memory constraints")

        except Exception as e:
            self.logger.error(f"Memory management failed: {e}")

    async def predict(
        self,
        model_id: str,
        input_data: Union[np.ndarray, List, Dict],
        config: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Perform inference with loaded model.

        Args:
            model_id: Model identifier
            input_data: Input data for inference
            config: Inference configuration

        Returns:
            Model prediction
        """
        if model_id not in self.loaded_models:
            raise InferenceError(f"Model {model_id} not loaded")

        try:
            start_time = time.time()
            model_info = self.loaded_models[model_id]
            model_data = model_info["model"]
            model_format = model_info["format"]

            # Prepare input data
            processed_input = await self._preprocess_input(
                input_data, model_format, config
            )

            # Perform inference
            if model_format == "pytorch":
                result = await self._predict_pytorch(model_data, processed_input)
            elif model_format == "tensorflow":
                result = await self._predict_tensorflow(model_data, processed_input)
            elif model_format == "onnx":
                result = await self._predict_onnx(model_data, processed_input)
            elif model_format == "tflite":
                result = await self._predict_tflite(model_data, processed_input)
            else:
                raise InferenceError(f"Unsupported model format: {model_format}")

            # Post-process result
            final_result = await self._postprocess_output(result, model_format, config)

            # Update statistics
            inference_time = time.time() - start_time
            self.inference_stats[model_id].append(inference_time)
            model_info["inference_count"] += 1

            # Keep only recent stats
            if len(self.inference_stats[model_id]) > 100:
                self.inference_stats[model_id] = self.inference_stats[model_id][-100:]

            # Update average
            model_info["avg_inference_time"] = sum(
                self.inference_stats[model_id]
            ) / len(self.inference_stats[model_id])

            self.logger.debug(
                f"Inference completed for {model_id} in {inference_time:.3f}s"
            )
            return final_result

        except Exception as e:
            self.logger.error(f"Inference failed for model {model_id}: {e}")
            raise InferenceError(f"Inference failed: {e}") from e

    async def _preprocess_input(
        self, input_data: Any, model_format: str, config: Optional[Dict[str, Any]]
    ) -> Any:
        """Preprocess input data for model."""
        try:
            # Convert to appropriate format
            if isinstance(input_data, list):
                input_data = np.array(input_data)

            if isinstance(input_data, np.ndarray):
                # Add batch dimension if needed
                if input_data.ndim == 1:
                    input_data = input_data.reshape(1, -1)
                elif input_data.ndim == 3:  # Image data
                    input_data = np.expand_dims(input_data, axis=0)

            # Framework-specific preprocessing
            if model_format == "pytorch":
                import torch

                input_data = torch.from_numpy(input_data).float()
            elif model_format == "tensorflow":
                input_data = input_data.astype(np.float32)

            return input_data

        except Exception as e:
            raise InferenceError(f"Input preprocessing failed: {e}")

    async def _predict_pytorch(self, model_data: Dict, input_data: Any) -> Any:
        """Perform PyTorch inference."""
        try:
            import torch

            model = model_data["model"]
            device = model_data["device"]

            with torch.no_grad():
                input_tensor = input_data.to(device)
                output = model(input_tensor)

                # Convert to numpy for consistency
                if isinstance(output, torch.Tensor):
                    output = output.cpu().numpy()

            return output

        except Exception as e:
            raise InferenceError(f"PyTorch inference failed: {e}")

    async def _predict_tensorflow(self, model_data: Dict, input_data: Any) -> Any:
        """Perform TensorFlow inference."""
        try:
            model = model_data["model"]

            # TensorFlow inference logic would go here
            # This is a placeholder

            return input_data  # Placeholder

        except Exception as e:
            raise InferenceError(f"TensorFlow inference failed: {e}")

    async def _predict_onnx(self, model_data: Dict, input_data: Any) -> Any:
        """Perform ONNX inference."""
        try:
            session = model_data["session"]

            # Prepare inputs
            input_name = session.get_inputs()[0].name
            inputs = {input_name: input_data}

            # Run inference
            outputs = session.run(None, inputs)

            return outputs[0] if len(outputs) == 1 else outputs

        except Exception as e:
            raise InferenceError(f"ONNX inference failed: {e}")

    async def _predict_tflite(self, model_data: Dict, input_data: Any) -> Any:
        """Perform TensorFlow Lite inference."""
        try:
            interpreter = model_data["interpreter"]

            # Get input/output details
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()

            # Set input tensor
            interpreter.set_tensor(input_details[0]["index"], input_data)

            # Invoke interpreter
            interpreter.invoke()

            # Get output tensor
            output = interpreter.get_tensor(output_details[0]["index"])

            return output

        except Exception as e:
            raise InferenceError(f"TFLite inference failed: {e}")

    async def _postprocess_output(
        self, output: Any, model_format: str, config: Optional[Dict[str, Any]]
    ) -> Any:
        """Postprocess model output."""
        try:
            # Convert to standard format
            if isinstance(output, np.ndarray):
                if output.ndim == 1:
                    return output.tolist()
                elif output.ndim == 2 and output.shape[0] == 1:
                    return output[0].tolist()
                else:
                    return output.tolist()
            else:
                return output

        except Exception as e:
            self.logger.warning(f"Output postprocessing failed: {e}")
            return output

    async def batch_predict(
        self,
        model_id: str,
        input_batch: List[Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        """
        Perform batch inference.

        Args:
            model_id: Model identifier
            input_batch: List of input data
            config: Batch configuration

        Returns:
            List of predictions
        """
        try:
            batch_size = len(input_batch)
            max_batch_size = self.config["batch_size_limit"]

            if batch_size > max_batch_size:
                # Split into smaller batches
                results = []
                for i in range(0, batch_size, max_batch_size):
                    batch = input_batch[i : i + max_batch_size]
                    batch_results = await self._predict_batch(model_id, batch, config)
                    results.extend(batch_results)
                return results
            else:
                return await self._predict_batch(model_id, input_batch, config)

        except Exception as e:
            self.logger.error(f"Batch prediction failed: {e}")
            raise InferenceError(f"Batch prediction failed: {e}") from e

    async def _predict_batch(
        self, model_id: str, input_batch: List[Any], config: Optional[Dict[str, Any]]
    ) -> List[Any]:
        """Internal batch prediction method."""
        # For now, process sequentially - could be optimized for true batching
        tasks = [
            self.predict(model_id, input_data, config) for input_data in input_batch
        ]
        return await asyncio.gather(*tasks)

    async def unload_model(self, model_id: str) -> bool:
        """
        Unload a model from memory.

        Args:
            model_id: Model identifier

        Returns:
            True if unloading successful
        """
        try:
            if model_id in self.loaded_models:
                # Clean up model resources
                model_info = self.loaded_models[model_id]
                model_data = model_info["model"]

                # Framework-specific cleanup
                if model_info["format"] == "pytorch":
                    if hasattr(model_data["model"], "cpu"):
                        model_data["model"].cpu()  # Move to CPU before deletion

                del self.loaded_models[model_id]
                del self.inference_stats[model_id]

                self.logger.info(f"Unloaded model {model_id}")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Failed to unload model {model_id}: {e}")
            return False

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a loaded model."""
        if model_id not in self.loaded_models:
            return None

        model_info = self.loaded_models[model_id].copy()
        model_info["inference_stats"] = {
            "count": len(self.inference_stats[model_id]),
            "avg_time": model_info["avg_inference_time"],
            "recent_times": self.inference_stats[model_id][-10:],  # Last 10
        }

        return model_info

    def get_gateway_stats(self) -> Dict[str, Any]:
        """Get gateway performance statistics."""
        return {
            "loaded_models": len(self.loaded_models),
            "hardware_accelerators": self.hardware_accelerators,
            "total_inference_count": sum(
                m["inference_count"] for m in self.loaded_models.values()
            ),
            "avg_inference_time": sum(
                m["avg_inference_time"] for m in self.loaded_models.values()
            )
            / max(1, len(self.loaded_models)),
            "memory_usage": sum(m["memory_usage"] for m in self.loaded_models.values()),
            "offline_mode": self.offline_mode,
        }

    async def enable_offline_mode(self, storage_path: Optional[str] = None) -> None:
        """
        Enable offline mode for disconnected operation.

        Args:
            storage_path: Path for offline model storage
        """
        self.offline_mode = True
        if storage_path:
            self.offline_storage = storage_path

        # Create offline storage directory
        import os

        os.makedirs(self.offline_storage, exist_ok=True)

        self.logger.info(f"Offline mode enabled with storage: {self.offline_storage}")

    async def preload_models_for_offline(
        self, model_configs: List[Dict[str, Any]]
    ) -> None:
        """
        Preload models for offline operation.

        Args:
            model_configs: List of model configurations
        """
        if not self.offline_mode:
            raise EdgeInferenceError("Offline mode not enabled")

        for config in model_configs:
            try:
                model_id = config["model_id"]
                model_path = config["model_path"]

                # Load model
                await self.load_model(model_id, model_path, config.get("config"))

                # Cache for offline use
                self.model_cache[model_id] = self.loaded_models[model_id]

                self.logger.info(f"Preloaded model {model_id} for offline use")

            except Exception as e:
                self.logger.error(
                    f"Failed to preload model {config.get('model_id', 'unknown')}: {e}"
                )

    async def sync_models_online(self) -> None:
        """Synchronize models when back online."""
        if not self.offline_mode:
            return

        try:
            # Placeholder for online synchronization logic
            # This would check for model updates, download new versions, etc.
            self.logger.info("Model synchronization completed")

        except Exception as e:
            self.logger.error(f"Model synchronization failed: {e}")
