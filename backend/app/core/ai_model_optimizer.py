"""
AI Model Performance Optimization Service
Optimizes AI model inference performance with advanced techniques
"""

import asyncio
import time
import torch
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from contextlib import asynccontextmanager
import logging
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue, Empty
import json

from .advanced_performance_optimizer import performance_optimizer, GPUMemoryManager

logger = logging.getLogger(__name__)


@dataclass
class ModelOptimizationConfig:
    """
    Configuration settings for AI model optimization.
    
    This dataclass defines various optimization parameters that control
    how models are optimized for inference performance.
    
    Attributes:
        max_batch_size (int): Maximum number of inputs to process in a single batch.
            Default: 32. Larger batches improve throughput but require more memory.
            
        max_sequence_length (int): Maximum sequence length for text models.
            Default: 2048. Longer sequences allow more context but use more memory.
            
        enable_mixed_precision (bool): Whether to use mixed precision (FP16/BF16).
            Default: True. Reduces memory usage and improves speed on compatible hardware.
            
        enable_gradient_checkpointing (bool): Whether to use gradient checkpointing.
            Default: True. Trades computation for memory during training/fine-tuning.
            
        enable_dynamic_batching (bool): Whether to enable dynamic batch sizing.
            Default: True. Automatically adjusts batch size based on available memory.
            
        cache_compiled_models (bool): Whether to cache compiled/optimized models.
            Default: True. Avoids recompilation overhead for frequently used models.
            
        optimization_level (str): Level of optimization to apply.
            Options: "speed", "balanced", "memory". Default: "balanced".
            - "speed": Maximum performance optimizations
            - "balanced": Balance between speed and memory usage  
            - "memory": Minimize memory usage
    """
    max_batch_size: int = 32
    max_sequence_length: int = 2048
    enable_mixed_precision: bool = True
    enable_gradient_checkpointing: bool = True
    enable_dynamic_batching: bool = True
    cache_compiled_models: bool = True
    optimization_level: str = "balanced"  # "speed", "balanced", "memory"


class ModelInferenceOptimizer:
    """
    Advanced AI model inference optimization system.
    
    This class provides comprehensive optimization capabilities for AI model inference,
    including GPU memory management, batch processing, model compilation, and
    performance monitoring.
    
    Key Features:
    - Automatic model optimization with caching
    - GPU memory management and optimization
    - Dynamic batch size calculation based on available memory
    - Mixed precision and gradient checkpointing support
    - PyTorch 2.0+ compilation integration
    - Comprehensive performance statistics tracking
    
    Attributes:
        config (ModelOptimizationConfig): Optimization configuration settings
        gpu_manager (GPUMemoryManager): GPU memory management instance
        compiled_models_cache (Dict): Cache of optimized models
        inference_stats (Dict): Performance statistics tracking
        optimization_lock (asyncio.Lock): Thread-safe optimization operations
    
    Example:
        ```python
        # Create optimizer with custom config
        config = ModelOptimizationConfig(
            max_batch_size=64,
            optimization_level="speed"
        )
        optimizer = ModelInferenceOptimizer(config)
        
        # Optimize model for inference
        optimized_model = await optimizer.optimize_model_for_inference(
            model, "my_model"
        )
        
        # Perform batch inference
        results = await optimizer.batch_inference(
            optimized_model, inputs, inference_function
        )
        ```
    """
    
    def __init__(self, config: ModelOptimizationConfig = None):
        self.config = config or ModelOptimizationConfig()
        self.gpu_manager = GPUMemoryManager()
        self.compiled_models_cache = {}
        self.inference_stats = {
            "total_inferences": 0,
            "total_tokens": 0,
            "avg_inference_time": 0.0,
            "avg_tokens_per_second": 0.0,
            "batch_efficiency": 0.0
        }
        self.optimization_lock = asyncio.Lock()
        
    async def optimize_model_for_inference(self, model, model_name: str = "default") -> Any:
        """
        Optimize an AI model for inference performance.
        
        This method applies various optimization techniques to improve model
        inference speed and memory efficiency, including mixed precision,
        gradient checkpointing, and PyTorch compilation.
        
        Args:
            model: The AI model to optimize (typically a PyTorch model)
            model_name (str): Unique identifier for the model (used for caching)
            
        Returns:
            Any: Optimized model ready for inference
            
        Note:
            - Optimized models are cached to avoid recompilation overhead
            - Falls back to original model if optimization fails
            - Thread-safe operation using optimization_lock
            
        Example:
            ```python
            optimized_model = await optimizer.optimize_model_for_inference(
                my_pytorch_model, "legal_bert_v1"
            )
            ```
        """
        async with self.optimization_lock:
            try:
                # Check if already optimized and cached
                if model_name in self.compiled_models_cache:
                    logger.info(f"✅ Using cached optimized model: {model_name}")
                    return self.compiled_models_cache[model_name]
                
                logger.info(f"🔧 Optimizing model for inference: {model_name}")
                
                # Apply optimizations based on configuration
                optimized_model = await self._apply_model_optimizations(model)
                
                # Cache optimized model if enabled
                if self.config.cache_compiled_models:
                    self.compiled_models_cache[model_name] = optimized_model
                
                logger.info(f"✅ Model optimization completed: {model_name}")
                return optimized_model
                
            except Exception as e:
                logger.error(f"❌ Model optimization failed for {model_name}: {e}")
                return model  # Return original model as fallback
    
    async def _apply_model_optimizations(self, model) -> Any:
        """Apply various optimizations to the model"""
        try:
            # Check if it's a PyTorch model
            if hasattr(model, 'eval'):
                model.eval()
                
                # Enable mixed precision if available and configured
                if self.config.enable_mixed_precision and torch.cuda.is_available():
                    model = model.half()
                    logger.info("✅ Mixed precision enabled")
                
                # Enable gradient checkpointing for memory efficiency
                if (self.config.enable_gradient_checkpointing and 
                    hasattr(model, 'gradient_checkpointing_enable')):
                    model.gradient_checkpointing_enable()
                    logger.info("✅ Gradient checkpointing enabled")
                
                # Compile model if PyTorch 2.0+ is available
                if hasattr(torch, 'compile'):
                    try:
                        optimization_mode = self._get_torch_compile_mode()
                        model = torch.compile(model, mode=optimization_mode)
                        logger.info(f"✅ Model compiled with mode: {optimization_mode}")
                    except Exception as e:
                        logger.warning(f"Model compilation failed: {e}")
                
                # Set inference mode
                model = torch.jit.optimize_for_inference(model) if hasattr(torch.jit, 'optimize_for_inference') else model
                
            return model
            
        except Exception as e:
            logger.error(f"Model optimization failed: {e}")
            return model
    
    def _get_torch_compile_mode(self) -> str:
        """Get torch compile mode based on optimization level"""
        mode_mapping = {
            "speed": "max-autotune",
            "balanced": "default",
            "memory": "reduce-overhead"
        }
        return mode_mapping.get(self.config.optimization_level, "default")
    
    async def batch_inference(self, 
                             model: Any, 
                             inputs: List[Any], 
                             inference_func: Callable,
                             **kwargs) -> List[Any]:
        """
        Perform optimized batch inference with automatic memory management.
        
        This method handles large-scale inference by:
        1. Calculating optimal batch size based on available GPU memory
        2. Processing inputs in optimized batches
        3. Managing GPU memory automatically
        4. Tracking performance statistics
        
        Args:
            model (Any): Optimized model for inference
            inputs (List[Any]): List of inputs to process
            inference_func (Callable): Function that performs inference on a batch
            **kwargs: Additional arguments passed to inference_func
            
        Returns:
            List[Any]: List of inference results corresponding to inputs
            
        Raises:
            Exception: If batch inference fails
            
        Example:
            ```python
            async def my_inference_func(model, batch, **kwargs):
                return model.predict(batch)
                
            results = await optimizer.batch_inference(
                optimized_model, 
                input_texts, 
                my_inference_func,
                temperature=0.7
            )
            ```
        """
        
        if not inputs:
            return []
        
        start_time = time.time()
        
        try:
            # Optimize batch size based on available memory
            optimal_batch_size = await self._calculate_optimal_batch_size(inputs)
            
            results = []
            
            # Process in optimized batches
            for i in range(0, len(inputs), optimal_batch_size):
                batch = inputs[i:i + optimal_batch_size]
                
                async with self.gpu_manager.manage_gpu_memory():
                    # Perform inference on batch
                    batch_results = await self._run_batch_inference(
                        model, batch, inference_func, **kwargs
                    )
                    results.extend(batch_results)
            
            # Update statistics
            inference_time = time.time() - start_time
            await self._update_inference_stats(len(inputs), inference_time)
            
            return results
            
        except Exception as e:
            logger.error(f"Batch inference failed: {e}")
            raise
    
    async def _calculate_optimal_batch_size(self, inputs: List[Any]) -> int:
        """Calculate optimal batch size based on available memory"""
        try:
            if not self.gpu_manager.gpu_available:
                return min(self.config.max_batch_size, len(inputs))
            
            # Get GPU memory stats
            gpu_stats = self.gpu_manager.get_memory_stats()
            memory_usage_percent = gpu_stats.get("memory_usage_percent", 0)
            
            # Adjust batch size based on memory usage
            if memory_usage_percent > 80:
                # High memory usage - reduce batch size
                optimal_size = max(1, self.config.max_batch_size // 4)
            elif memory_usage_percent > 60:
                # Medium memory usage - moderate batch size
                optimal_size = max(1, self.config.max_batch_size // 2)
            else:
                # Low memory usage - use max batch size
                optimal_size = self.config.max_batch_size
            
            return min(optimal_size, len(inputs))
            
        except Exception as e:
            logger.error(f"Failed to calculate optimal batch size: {e}")
            return min(8, len(inputs))  # Conservative fallback
    
    async def _run_batch_inference(self, 
                                  model: Any, 
                                  batch: List[Any], 
                                  inference_func: Callable,
                                  **kwargs) -> List[Any]:
        """Run inference on a batch"""
        try:
            # Set torch no_grad for memory efficiency
            if hasattr(torch, 'no_grad'):
                with torch.no_grad():
                    if asyncio.iscoroutinefunction(inference_func):
                        return await inference_func(model, batch, **kwargs)
                    else:
                        # Run sync function in thread pool
                        loop = asyncio.get_event_loop()
                        return await loop.run_in_executor(
                            None, inference_func, model, batch, **kwargs
                        )
            else:
                if asyncio.iscoroutinefunction(inference_func):
                    return await inference_func(model, batch, **kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(
                        None, inference_func, model, batch, **kwargs
                    )
                    
        except Exception as e:
            logger.error(f"Batch inference execution failed: {e}")
            raise
    
    async def _update_inference_stats(self, num_inputs: int, inference_time: float):
        """Update inference statistics"""
        try:
            self.inference_stats["total_inferences"] += num_inputs
            
            # Update average inference time
            current_avg = self.inference_stats["avg_inference_time"]
            total_inferences = self.inference_stats["total_inferences"]
            
            new_avg = ((current_avg * (total_inferences - num_inputs)) + 
                      (inference_time / num_inputs)) / total_inferences
            
            self.inference_stats["avg_inference_time"] = new_avg
            
            # Calculate tokens per second (approximate)
            if inference_time > 0:
                estimated_tokens = num_inputs * 50  # Rough estimate
                tokens_per_second = estimated_tokens / inference_time
                
                self.inference_stats["total_tokens"] += estimated_tokens
                self.inference_stats["avg_tokens_per_second"] = (
                    self.inference_stats["total_tokens"] / 
                    (self.inference_stats["total_inferences"] * self.inference_stats["avg_inference_time"])
                )
            
        except Exception as e:
            logger.error(f"Failed to update inference stats: {e}")
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        return {
            "config": {
                "max_batch_size": self.config.max_batch_size,
                "max_sequence_length": self.config.max_sequence_length,
                "enable_mixed_precision": self.config.enable_mixed_precision,
                "optimization_level": self.config.optimization_level
            },
            "performance_stats": self.inference_stats,
            "gpu_stats": self.gpu_manager.get_memory_stats(),
            "cached_models": list(self.compiled_models_cache.keys()),
            "recommendations": self._get_optimization_recommendations()
        }
    
    def _get_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Check inference performance
        avg_time = self.inference_stats["avg_inference_time"]
        if avg_time > 2.0:
            recommendations.append("High inference latency - consider model quantization")
        
        # Check GPU utilization
        gpu_stats = self.gpu_manager.get_memory_stats()
        if gpu_stats.get("memory_usage_percent", 0) < 30:
            recommendations.append("Low GPU utilization - consider increasing batch size")
        elif gpu_stats.get("memory_usage_percent", 0) > 90:
            recommendations.append("High GPU memory usage - consider reducing batch size")
        
        # Check tokens per second
        tokens_per_sec = self.inference_stats["avg_tokens_per_second"]
        if tokens_per_sec < 20:
            recommendations.append("Low token generation rate - consider model optimization")
        
        return recommendations


class EmbeddingsOptimizer:
    """Optimizes embeddings operations"""
    
    def __init__(self):
        self.model_optimizer = ModelInferenceOptimizer(
            ModelOptimizationConfig(
                max_batch_size=64,  # Larger batches for embeddings
                enable_mixed_precision=True,
                optimization_level="speed"
            )
        )
        self.embedding_cache = {}
        
    async def optimize_embeddings_batch(self, 
                                       model: Any, 
                                       texts: List[str],
                                       embedding_func: Callable) -> List[List[float]]:
        """Optimize embeddings generation for batch of texts"""
        
        # Check cache first
        cached_results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            text_hash = hash(text)
            if text_hash in self.embedding_cache:
                cached_results.append((i, self.embedding_cache[text_hash]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Process uncached texts
        if uncached_texts:
            embeddings = await self.model_optimizer.batch_inference(
                model, uncached_texts, embedding_func
            )
            
            # Cache results
            for text, embedding in zip(uncached_texts, embeddings):
                self.embedding_cache[hash(text)] = embedding
            
            # Combine cached and new results
            all_results = [None] * len(texts)
            
            # Add cached results
            for idx, embedding in cached_results:
                all_results[idx] = embedding
            
            # Add new results
            for idx, embedding in zip(uncached_indices, embeddings):
                all_results[idx] = embedding
            
            return all_results
        else:
            # All results were cached
            return [embedding for _, embedding in sorted(cached_results)]


# Global optimizers
model_inference_optimizer = ModelInferenceOptimizer()
embeddings_optimizer = EmbeddingsOptimizer()