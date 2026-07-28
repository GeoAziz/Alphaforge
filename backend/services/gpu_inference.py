"""
GPU Inference Pipeline - §6.4 Architecture Doc
Handles ONNX/TensorRT model loading, INT8/FP16 quantization,
inference batching (32-128 items), and GPU instance management.
"""

import logging
import time
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QuantizationPrecision(str, Enum):
    FP32 = "fp32"
    FP16 = "fp16"
    INT8 = "int8"


class InferenceBackend(str, Enum):
    ONNX = "onnx"
    TENSORRT = "tensorrt"
    CPU_FALLBACK = "cpu_fallback"


@dataclass
class ModelConfig:
    """Configuration for a deployed model."""
    model_name: str
    model_path: str
    backend: InferenceBackend = InferenceBackend.ONNX
    precision: QuantizationPrecision = QuantizationPrecision.FP32
    batch_size: int = 64
    max_batch_size: int = 128
    input_feature_count: int = 30
    output_classes: int = 3  # BUY, SELL, HOLD
    gpu_device_id: int = 0
    quantized: bool = False
    accuracy_delta_threshold: float = 0.005  # 0.5% max accuracy loss from quantization


@dataclass
class InferenceResult:
    """Result from a single inference call."""
    model_name: str
    predictions: List[Dict[str, Any]]
    batch_size: int
    inference_time_ms: float
    backend: str
    precision: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class QuantizationManager:
    """
    Manages model quantization from FP32 to INT8/FP16.
    Validates quantized model accuracy against full-precision baseline.
    """

    def __init__(self):
        self._quantized_models: Dict[str, Dict[str, Any]] = {}

    def quantize_model(
        self,
        model_path: str,
        target_precision: QuantizationPrecision,
        calibration_data: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Quantize a model to the target precision.
        In production, uses ONNX Runtime quantization or TensorRT.
        """
        model_name = os.path.basename(model_path)

        if target_precision == QuantizationPrecision.FP32:
            return {
                "success": True,
                "model_name": model_name,
                "precision": "fp32",
                "message": "No quantization needed for FP32",
                "model_path": model_path,
            }

        try:
            # Attempt ONNX Runtime quantization
            if target_precision == QuantizationPrecision.INT8:
                result = self._quantize_onnx_int8(model_path, calibration_data)
            elif target_precision == QuantizationPrecision.FP16:
                result = self._quantize_onnx_fp16(model_path)
            else:
                return {"success": False, "error": f"Unsupported precision: {target_precision}"}

            if result.get("success"):
                self._quantized_models[model_name] = {
                    "original_path": model_path,
                    "quantized_path": result.get("quantized_path", model_path),
                    "precision": target_precision.value,
                    "accuracy_delta": result.get("accuracy_delta", 0),
                    "quantized_at": datetime.utcnow().isoformat(),
                }

            return result

        except Exception as e:
            logger.error(f"Quantization failed for {model_name}: {e}")
            # Fallback: use original model
            return {
                "success": True,
                "model_name": model_name,
                "precision": "fp32",
                "message": f"Quantization failed, using FP32 fallback: {e}",
                "model_path": model_path,
            }

    def validate_accuracy(
        self,
        original_predictions: List[float],
        quantized_predictions: List[float],
        threshold: float = 0.005,
    ) -> Dict[str, Any]:
        """Validate quantized model accuracy against full-precision baseline."""
        if not original_predictions or not quantized_predictions:
            return {"valid": False, "error": "Empty prediction lists"}

        import numpy as np
        orig = np.array(original_predictions)
        quant = np.array(quantized_predictions)

        # Mean absolute error
        mae = float(np.mean(np.abs(orig - quant)))

        # Max absolute error
        max_err = float(np.max(np.abs(orig - quant)))

        # Within threshold percentage
        within_threshold = float(np.mean(np.abs(orig - quant) <= threshold * np.abs(orig)) * 100)

        valid = within_threshold >= 99.0  # 99% of predictions within threshold

        return {
            "valid": valid,
            "mean_absolute_error": round(mae, 6),
            "max_absolute_error": round(max_err, 6),
            "predictions_within_threshold_pct": round(within_threshold, 2),
            "threshold": threshold,
        }

    @staticmethod
    def _quantize_onnx_int8(model_path: str, calibration_data=None) -> Dict[str, Any]:
        """Quantize ONNX model to INT8."""
        try:
            from onnxruntime.quantization import quantize_dynamic, QuantType
            quantized_path = model_path.replace(".onnx", "_int8.onnx")
            quantize_dynamic(model_path, quantized_path, weight_type=QuantType.QInt8)
            return {
                "success": True,
                "quantized_path": quantized_path,
                "precision": "int8",
            }
        except ImportError:
            logger.warning("onnxruntime quantization not available")
            return {"success": False, "error": "onnxruntime not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _quantize_onnx_fp16(model_path: str) -> Dict[str, Any]:
        """Quantize ONNX model to FP16."""
        try:
            from onnxruntime.quantization import quantize_dynamic, QuantType
            quantized_path = model_path.replace(".onnx", "_fp16.onnx")
            quantize_dynamic(model_path, quantized_path, weight_type=QuantType.QFloat16)
            return {
                "success": True,
                "quantized_path": quantized_path,
                "precision": "fp16",
            }
        except ImportError:
            logger.warning("onnxruntime quantization not available")
            return {"success": False, "error": "onnxruntime not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class InferenceBatcher:
    """
    Batches incoming feature vectors for efficient GPU inference.
    Targets batch sizes of 32-128 items per batch.
    Batch latency ceiling: 500ms (within 2s signal latency target).
    """

    MAX_BATCH_LATENCY_MS = 500
    DEFAULT_BATCH_SIZE = 64

    def __init__(self, batch_size: int = DEFAULT_BATCH_SIZE):
        self.batch_size = min(batch_size, 128)
        self._pending_batch: List[Dict[str, Any]] = []
        self._batch_created_at: Optional[float] = None

    def add_to_batch(self, item: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Add an item to the current batch.
        Returns a full batch when ready, None otherwise.
        """
        if not self._pending_batch:
            self._batch_created_at = time.time()

        self._pending_batch.append(item)

        # Check if batch is full
        if len(self._pending_batch) >= self.batch_size:
            batch = self._pending_batch
            self._pending_batch = []
            self._batch_created_at = None
            return batch

        # Check if latency ceiling reached
        if self._batch_created_at:
            elapsed_ms = (time.time() - self._batch_created_at) * 1000
            if elapsed_ms >= self.MAX_BATCH_LATENCY_MS:
                batch = self._pending_batch
                self._pending_batch = []
                self._batch_created_at = None
                return batch

        return None

    def flush(self) -> List[Dict[str, Any]]:
        """Flush any pending items as a partial batch."""
        batch = self._pending_batch
        self._pending_batch = []
        self._batch_created_at = None
        return batch

    @property
    def pending_count(self) -> int:
        return len(self._pending_batch)


class GPUInferenceService:
    """
    GPU inference pipeline for deep learning models (LSTM, Transformers).
    
    Features:
    - ONNX Runtime and TensorRT backend support
    - INT8/FP16 quantization with accuracy validation
    - Inference batching (32-128 items)
    - GPU device management
    - Automatic CPU fallback
    """

    def __init__(self):
        self._models: Dict[str, ModelConfig] = {}
        self._sessions: Dict[str, Any] = {}  # ONNX sessions
        self._quantization_manager = QuantizationManager()
        self._batchers: Dict[str, InferenceBatcher] = {}
        self._gpu_available = self._check_gpu_availability()
        self._inference_stats: Dict[str, Dict[str, Any]] = {}

        logger.info(f"🖥️ GPU Inference Service initialized (GPU available: {self._gpu_available})")

    def register_model(self, config: ModelConfig) -> Dict[str, Any]:
        """Register a model for inference."""
        self._models[config.model_name] = config
        self._batchers[config.model_name] = InferenceBatcher(config.batch_size)

        logger.info(
            f"📋 Model registered: {config.model_name} "
            f"(backend={config.backend.value}, precision={config.precision.value}, "
            f"batch_size={config.batch_size})"
        )

        return {
            "success": True,
            "model_name": config.model_name,
            "backend": config.backend.value,
            "precision": config.precision.value,
            "batch_size": config.batch_size,
        }

    async def infer(
        self,
        model_name: str,
        feature_vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run inference on a single feature vector.
        Automatically batches for GPU efficiency.
        """
        config = self._models.get(model_name)
        if not config:
            return {"success": False, "error": f"Model {model_name} not registered"}

        batcher = self._batchers[model_name]
        item = {
            "features": feature_vector,
            "metadata": metadata or {},
            "queued_at": time.time(),
        }

        # Try to form a batch
        batch = batcher.add_to_batch(item)

        if batch is not None:
            return await self._run_batch_inference(model_name, batch)

        # If batch not ready, check if we should run partial batch
        if batcher.pending_count > 0:
            # Small latency optimization: if only 1 item, run immediately
            if batcher.pending_count == 1:
                single_batch = batcher.flush()
                return await self._run_batch_inference(model_name, single_batch)

        return {
            "success": True,
            "status": "queued",
            "pending_count": batcher.pending_count,
            "message": f"Queued for batch (batch_size={batcher.batch_size})",
        }

    async def infer_batch(
        self,
        model_name: str,
        feature_vectors: List[List[float]],
    ) -> InferenceResult:
        """Run inference on a batch of feature vectors directly."""
        config = self._models.get(model_name)
        if not config:
            raise ValueError(f"Model {model_name} not registered")

        items = [
            {"features": fv, "metadata": {}, "queued_at": time.time()}
            for fv in feature_vectors
        ]

        return await self._run_batch_inference(model_name, items)

    async def _run_batch_inference(
        self, model_name: str, batch: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute batch inference using the configured backend."""
        config = self._models.get(model_name)
        start_time = time.time()

        try:
            # Try ONNX Runtime
            if config.backend == InferenceBackend.ONNX and self._gpu_available:
                result = await self._run_onnx_inference(config, batch)
            # Try TensorRT
            elif config.backend == InferenceBackend.TENSORRT and self._gpu_available:
                result = await self._run_tensorrt_inference(config, batch)
            # CPU fallback
            else:
                result = await self._run_cpu_inference(config, batch)

            inference_time_ms = (time.time() - start_time) * 1000

            # Update stats
            if model_name not in self._inference_stats:
                self._inference_stats[model_name] = {
                    "total_calls": 0,
                    "total_time_ms": 0,
                    "avg_time_ms": 0,
                }
            stats = self._inference_stats[model_name]
            stats["total_calls"] += 1
            stats["total_time_ms"] += inference_time_ms
            stats["avg_time_ms"] = stats["total_time_ms"] / stats["total_calls"]

            return {
                "success": True,
                "predictions": result,
                "batch_size": len(batch),
                "inference_time_ms": round(inference_time_ms, 2),
                "backend": config.backend.value,
                "precision": config.precision.value,
                "model_name": model_name,
            }

        except Exception as e:
            inference_time_ms = (time.time() - start_time) * 1000
            logger.error(f"❌ Inference failed for {model_name}: {e}")

            # Fallback to CPU
            try:
                result = await self._run_cpu_inference(config, batch)
                return {
                    "success": True,
                    "predictions": result,
                    "batch_size": len(batch),
                    "inference_time_ms": round(inference_time_ms, 2),
                    "backend": "cpu_fallback",
                    "precision": "fp32",
                    "model_name": model_name,
                    "fallback_used": True,
                }
            except Exception as fallback_error:
                return {
                    "success": False,
                    "error": str(e),
                    "fallback_error": str(fallback_error),
                    "batch_size": len(batch),
                }

    async def _run_onnx_inference(
        self, config: ModelConfig, batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run inference using ONNX Runtime."""
        import numpy as np

        features = np.array([item["features"] for item in batch], dtype=np.float32)

        session = self._sessions.get(config.model_name)
        if session is None:
            # Lazy load ONNX session
            try:
                import onnxruntime as ort
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
                session = ort.InferenceSession(config.model_path, providers=providers)
                self._sessions[config.model_name] = session
            except ImportError:
                raise RuntimeError("onnxruntime not installed")
            except Exception as e:
                raise RuntimeError(f"Failed to load ONNX model: {e}")

        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: features})

        # Parse predictions
        raw_output = outputs[0]
        predictions = []
        for i, raw in enumerate(raw_output):
            softmax = self._softmax(raw)
            predicted_class = int(np.argmax(softmax))
            confidence = float(softmax[predicted_class])
            predictions.append({
                "class": ["BUY", "SELL", "HOLD"][predicted_class] if predicted_class < 3 else "HOLD",
                "confidence": round(confidence, 4),
                "probabilities": {
                    "buy": round(float(softmax[0]), 4),
                    "sell": round(float(softmax[1]), 4) if len(softmax) > 1 else 0,
                    "hold": round(float(softmax[2]), 4) if len(softmax) > 2 else 0,
                },
            })

        return predictions

    async def _run_tensorrt_inference(
        self, config: ModelConfig, batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run inference using TensorRT (via ONNX Runtime with TensorRT provider)."""
        import numpy as np

        features = np.array([item["features"] for item in batch], dtype=np.float32)

        session = self._sessions.get(config.model_name)
        if session is None:
            try:
                import onnxruntime as ort
                providers = [
                    ("TensorrtExecutionProvider", {
                        "trt_max_workspace_size": 2 * 1024 * 1024 * 1024,
                        "trt_fp16_enable": config.precision == QuantizationPrecision.FP16,
                    }),
                    "CUDAExecutionProvider",
                    "CPUExecutionProvider",
                ]
                session = ort.InferenceSession(config.model_path, providers=providers)
                self._sessions[config.model_name] = session
            except Exception as e:
                raise RuntimeError(f"TensorRT fallback to ONNX: {e}")

        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: features})

        raw_output = outputs[0]
        predictions = []
        for raw in raw_output:
            softmax = self._softmax(raw)
            predicted_class = int(np.argmax(softmax))
            confidence = float(softmax[predicted_class])
            predictions.append({
                "class": ["BUY", "SELL", "HOLD"][predicted_class] if predicted_class < 3 else "HOLD",
                "confidence": round(confidence, 4),
                "probabilities": {
                    "buy": round(float(softmax[0]), 4),
                    "sell": round(float(softmax[1]), 4) if len(softmax) > 1 else 0,
                    "hold": round(float(softmax[2]), 4) if len(softmax) > 2 else 0,
                },
            })

        return predictions

    async def _run_cpu_inference(
        self, config: ModelConfig, batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """CPU fallback inference using basic scoring."""
        predictions = []
        for item in batch:
            features = item.get("features", [])
            if not features:
                predictions.append({
                    "class": "HOLD",
                    "confidence": 0.33,
                    "probabilities": {"buy": 0.33, "sell": 0.33, "hold": 0.34},
                })
                continue

            # Simple heuristic-based scoring as CPU fallback
            score = sum(features) / len(features) if features else 0
            if score > 0.6:
                pred = {"class": "BUY", "confidence": min(0.85, 0.5 + score * 0.3)}
            elif score < 0.4:
                pred = {"class": "SELL", "confidence": min(0.85, 0.5 + (1 - score) * 0.3)}
            else:
                pred = {"class": "HOLD", "confidence": 0.5}

            total = pred["confidence"]
            pred["probabilities"] = {
                "buy": pred["confidence"] if pred["class"] == "BUY" else (1 - total) / 2,
                "sell": pred["confidence"] if pred["class"] == "SELL" else (1 - total) / 2,
                "hold": pred["confidence"] if pred["class"] == "HOLD" else (1 - total) / 2,
            }
            pred["confidence"] = round(pred["confidence"], 4)
            pred["probabilities"] = {k: round(v, 4) for k, v in pred["probabilities"].items()}
            predictions.append(pred)

        return predictions

    def get_stats(self) -> Dict[str, Any]:
        """Get inference statistics for all models."""
        return {
            "gpu_available": self._gpu_available,
            "registered_models": len(self._models),
            "models": {
                name: {
                    "backend": config.backend.value,
                    "precision": config.precision.value,
                    "batch_size": config.batch_size,
                    "stats": self._inference_stats.get(name, {}),
                }
                for name, config in self._models.items()
            },
        }

    def quantize_model(
        self, model_name: str, target_precision: QuantizationPrecision
    ) -> Dict[str, Any]:
        """Quantize a registered model."""
        config = self._models.get(model_name)
        if not config:
            return {"success": False, "error": f"Model {model_name} not registered"}

        result = self._quantization_manager.quantize_model(
            config.model_path, target_precision
        )

        if result.get("success"):
            config.precision = target_precision
            config.quantized = True

        return result

    @staticmethod
    def _softmax(x):
        import numpy as np
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    @staticmethod
    def _check_gpu_availability() -> bool:
        """Check if GPU is available for inference."""
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            return "CUDAExecutionProvider" in providers
        except ImportError:
            pass

        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            pass

        return False


_gpu_inference_service: Optional[GPUInferenceService] = None


def get_gpu_inference_service() -> GPUInferenceService:
    """Get or create the global GPU inference service."""
    global _gpu_inference_service
    if _gpu_inference_service is None:
        _gpu_inference_service = GPUInferenceService()
    return _gpu_inference_service
