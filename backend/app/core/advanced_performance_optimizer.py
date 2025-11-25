"""
Advanced Performance Optimizer for AI-Lawyer System
Sprint 3 - Performance & Operations Focus

This module provides comprehensive performance optimizations including:
- GPU memory management and optimization
- Batch processing for AI operations
- Connection pooling improvements
- Advanced caching strategies
- Background task optimization
"""

import asyncio
import time
import gc
import psutil
import threading
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from queue import Queue, Empty, Full
import weakref
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    cpu_usage: float
    memory_usage: float
    gpu_memory_usage: Optional[float]
    active_connections: int
    cache_hit_rate: float
    avg_response_time: float
    queue_sizes: Dict[str, int]
    timestamp: float


class GPUMemoryManager:
    """GPU memory optimization and management"""
    
    def __init__(self):
        self.gpu_available = self._check_gpu_availability()
        self.memory_threshold = 0.85  # 85% threshold
        self.cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()
        self.memory_stats = deque(maxlen=100)
        
    def _check_gpu_availability(self) -> bool:
        """
        Check if GPU is available for CUDA operations.
        
        Returns:
            bool: True if CUDA GPU is available, False otherwise
            
        Note:
            This method safely handles the case where PyTorch is not installed
            or CUDA is not available on the system.
        """
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    @asynccontextmanager
    async def manage_gpu_memory(self):
        """
        Context manager for automatic GPU memory management.
        
        This context manager:
        1. Clears GPU cache before operations
        2. Tracks memory usage during operations  
        3. Performs periodic cleanup if threshold is reached
        4. Records memory usage statistics
        
        Yields:
            None: Context for GPU operations
            
        Example:
            ```python
            async with gpu_manager.manage_gpu_memory():
                # Your GPU operations here
                result = model.inference(data)
            ```
        """
        if not self.gpu_available:
            yield
            return
            
        try:
            import torch
            # Clear cache before operation
            torch.cuda.empty_cache()
            
            initial_memory = torch.cuda.memory_allocated()
            yield
            
        finally:
            if self.gpu_available:
                # Cleanup after operation
                final_memory = torch.cuda.memory_allocated()
                memory_used = final_memory - initial_memory
                
                self.memory_stats.append({
                    'timestamp': time.time(),
                    'memory_used': memory_used,
                    'total_allocated': final_memory
                })
                
                # Periodic cleanup
                if time.time() - self._last_cleanup > self.cleanup_interval:
                    await self._cleanup_gpu_memory()
    
    async def _cleanup_gpu_memory(self):
        """
        Perform GPU memory cleanup operations.
        
        This method:
        - Empties CUDA cache to free unused memory
        - Triggers Python garbage collection
        - Updates last cleanup timestamp
        - Logs cleanup completion
        
        Note:
            Called automatically by manage_gpu_memory() when cleanup_interval
            has elapsed since the last cleanup.
        """
        if not self.gpu_available:
            return
            
        try:
            import torch
            torch.cuda.empty_cache()
            gc.collect()
            self._last_cleanup = time.time()
            logger.info("🧹 GPU memory cleanup completed")
        except Exception as e:
            logger.error(f"GPU memory cleanup failed: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive GPU memory statistics.
        
        Returns:
            Dict[str, Any]: Dictionary containing:
                - gpu_available (bool): Whether GPU is available
                - allocated_memory (int): Currently allocated GPU memory in bytes
                - cached_memory (int): Cached GPU memory in bytes  
                - max_memory (int): Maximum GPU memory ever allocated
                - memory_usage_percent (float): Percentage of total GPU memory used
                - recent_stats (List): Last 10 memory usage records
                - error (str, optional): Error message if stats collection failed
                
        Example:
            ```python
            stats = gpu_manager.get_memory_stats()
            if stats['gpu_available']:
                print(f"GPU usage: {stats['memory_usage_percent']:.1f}%")
            ```
        """
        if not self.gpu_available:
            return {"gpu_available": False}
            
        try:
            import torch
            return {
                "gpu_available": True,
                "allocated_memory": torch.cuda.memory_allocated(),
                "cached_memory": torch.cuda.memory_reserved(),
                "max_memory": torch.cuda.max_memory_allocated(),
                "memory_usage_percent": (torch.cuda.memory_allocated() / torch.cuda.get_device_properties(0).total_memory) * 100,
                "recent_stats": list(self.memory_stats)[-10:]  # Last 10 records
            }
        except Exception as e:
            logger.error(f"Failed to get GPU memory stats: {e}")
            return {"gpu_available": True, "error": str(e)}


class BatchProcessor:
    """
    Intelligent batch processing system for AI operations.
    
    This class provides optimized batch processing capabilities to improve
    throughput and reduce overhead for AI model inference operations.
    
    Features:
    - Dynamic batch size optimization
    - Intelligent request queuing and batching
    - Performance statistics tracking
    - Configurable batch size and wait time limits
    
    Attributes:
        max_batch_size (int): Maximum number of requests per batch
        max_wait_time (float): Maximum time to wait for batch formation (seconds)
        pending_requests (Queue): Queue of pending requests
        processing_lock (asyncio.Lock): Lock for thread-safe batch processing
        stats (Dict): Performance statistics tracking
    
    Example:
        ```python
        processor = BatchProcessor(max_batch_size=32, max_wait_time=0.1)
        
        async def my_inference_func(requests):
            return [model.process(req) for req in requests]
            
        results = await processor.process_batch(my_inference_func, requests)
        ```
    """
    
    def __init__(self, max_batch_size: int = 32, max_wait_time: float = 0.1):
        self.max_batch_size = max_batch_size
        self.max_wait_time = max_wait_time
        self.pending_requests = Queue()
        self.processing_lock = asyncio.Lock()
        self.stats = {
            "total_batches": 0,
            "total_requests": 0,
            "avg_batch_size": 0.0,
            "avg_processing_time": 0.0
        }
        
    async def process_batch(self, processor_func, requests: List[Any]) -> List[Any]:
        """
        Process a batch of requests using the provided processor function.
        
        Args:
            processor_func: Async function that processes a batch of requests
            requests (List[Any]): List of requests to process
            
        Returns:
            List[Any]: List of processing results corresponding to input requests
            
        Raises:
            Exception: If batch processing fails
            
        Note:
            Updates internal statistics including total batches processed,
            average batch size, and average processing time.
        """
        start_time = time.time()
        
        try:
            # Process batch
            results = await processor_func(requests)
            
            # Update statistics
            processing_time = time.time() - start_time
            self.stats["total_batches"] += 1
            self.stats["total_requests"] += len(requests)
            self.stats["avg_batch_size"] = self.stats["total_requests"] / self.stats["total_batches"]
            self.stats["avg_processing_time"] = (
                (self.stats["avg_processing_time"] * (self.stats["total_batches"] - 1) + processing_time) 
                / self.stats["total_batches"]
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise
    
    async def add_to_batch(self, request: Any, result_future: asyncio.Future):
        """
        Add a request to the batch processing queue.
        
        Args:
            request (Any): The request to be processed
            result_future (asyncio.Future): Future object to receive the result
            
        Note:
            This method adds the request-future pair to the pending queue.
            The batch worker will process these requests in batches.
        """
        self.pending_requests.put((request, result_future))
    
    async def start_batch_worker(self, processor_func):
        """
        Start the batch processing worker loop.
        
        Args:
            processor_func: Async function that processes batches of requests
            
        Note:
            This is a long-running coroutine that:
            1. Continuously collects requests into batches
            2. Processes batches when size or time limits are reached
            3. Distributes results back to the corresponding futures
            4. Handles exceptions gracefully
            
            Should be run as a background task:
            ```python
            task = asyncio.create_task(processor.start_batch_worker(my_func))
            ```
        """
        while True:
            try:
                batch = []
                futures = []
                start_time = time.time()
                
                # Collect requests for batch
                while (len(batch) < self.max_batch_size and 
                       time.time() - start_time < self.max_wait_time):
                    try:
                        request, future = self.pending_requests.get_nowait()
                        batch.append(request)
                        futures.append(future)
                    except Empty:
                        if batch:  # Process if we have any requests
                            break
                        await asyncio.sleep(0.01)  # Small delay
                        continue
                
                if batch:
                    try:
                        results = await self.process_batch(processor_func, batch)
                        
                        # Distribute results to futures
                        for future, result in zip(futures, results):
                            if not future.cancelled():
                                future.set_result(result)
                                
                    except Exception as e:
                        # Set exception for all futures
                        for future in futures:
                            if not future.cancelled():
                                future.set_exception(e)
                
            except Exception as e:
                logger.error(f"Batch worker error: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on error
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive batch processing statistics.
        
        Returns:
            Dict[str, Any]: Statistics including:
                - total_batches (int): Total number of batches processed
                - total_requests (int): Total number of requests processed
                - avg_batch_size (float): Average batch size
                - avg_processing_time (float): Average processing time per batch
                - pending_requests (int): Current number of pending requests
                - optimal_batch_size (int): Recommended optimal batch size
        """
        return {
            **self.stats,
            "pending_requests": self.pending_requests.qsize(),
            "optimal_batch_size": min(self.max_batch_size, max(1, int(self.stats["avg_batch_size"] * 1.2)))
        }


class ConnectionPoolOptimizer:
    """Advanced connection pool optimization"""
    
    def __init__(self):
        self.pool_stats = defaultdict(lambda: {
            "active": 0,
            "idle": 0,
            "total_created": 0,
            "total_closed": 0,
            "avg_usage_time": 0.0,
            "peak_usage": 0
        })
        self.connection_timings = defaultdict(list)
        
    def record_connection_usage(self, pool_name: str, usage_time: float):
        """Record connection usage metrics"""
        stats = self.pool_stats[pool_name]
        timings = self.connection_timings[pool_name]
        
        timings.append(usage_time)
        if len(timings) > 1000:  # Keep last 1000 measurements
            timings.pop(0)
            
        stats["avg_usage_time"] = sum(timings) / len(timings)
        
    def get_optimal_pool_size(self, pool_name: str) -> Tuple[int, int]:
        """Calculate optimal pool size based on usage patterns"""
        stats = self.pool_stats[pool_name]
        timings = self.connection_timings[pool_name]
        
        if not timings:
            return 10, 20  # Default values
            
        # Calculate based on usage patterns
        avg_usage = stats["avg_usage_time"]
        peak_usage = stats["peak_usage"]
        
        # Optimal size based on Little's Law
        optimal_size = max(5, int(peak_usage * avg_usage))
        max_overflow = max(10, int(optimal_size * 0.5))
        
        return optimal_size, max_overflow
    
    def update_pool_metrics(self, pool_name: str, active: int, idle: int):
        """Update pool metrics"""
        stats = self.pool_stats[pool_name]
        stats["active"] = active
        stats["idle"] = idle
        stats["peak_usage"] = max(stats["peak_usage"], active)
    
    def get_pool_recommendations(self) -> Dict[str, Dict[str, Any]]:
        """Get pool optimization recommendations"""
        recommendations = {}
        
        for pool_name, stats in self.pool_stats.items():
            optimal_size, max_overflow = self.get_optimal_pool_size(pool_name)
            
            recommendations[pool_name] = {
                "current_stats": stats,
                "recommended_pool_size": optimal_size,
                "recommended_max_overflow": max_overflow,
                "efficiency": stats["active"] / (stats["active"] + stats["idle"]) if (stats["active"] + stats["idle"]) > 0 else 0
            }
            
        return recommendations


class AdvancedPerformanceOptimizer:
    """Comprehensive performance optimization system"""
    
    def __init__(self):
        self.gpu_manager = GPUMemoryManager()
        self.batch_processor = BatchProcessor()
        self.connection_optimizer = ConnectionPoolOptimizer()
        self.metrics_history = deque(maxlen=1000)
        self.optimization_tasks = {}
        self.background_tasks = set()
        
    async def start_background_optimizations(self):
        """Start background optimization tasks"""
        # Memory cleanup task
        self.optimization_tasks["memory_cleanup"] = asyncio.create_task(
            self._periodic_memory_cleanup()
        )
        
        # Metrics collection task
        self.optimization_tasks["metrics_collection"] = asyncio.create_task(
            self._collect_performance_metrics()
        )
        
        # Connection pool optimization task
        self.optimization_tasks["connection_optimization"] = asyncio.create_task(
            self._optimize_connection_pools()
        )
        
        logger.info("🚀 Background performance optimizations started")
    
    async def stop_background_optimizations(self):
        """Stop background optimization tasks"""
        for task_name, task in self.optimization_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            logger.info(f"✅ Stopped {task_name}")
        
        self.optimization_tasks.clear()
    
    async def _periodic_memory_cleanup(self):
        """Periodic memory cleanup"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Python garbage collection
                collected = gc.collect()
                if collected > 0:
                    logger.info(f"🧹 Collected {collected} objects in garbage collection")
                
                # GPU memory cleanup
                if self.gpu_manager.gpu_available:
                    await self.gpu_manager._cleanup_gpu_memory()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory cleanup error: {e}")
    
    async def _collect_performance_metrics(self):
        """Collect performance metrics periodically"""
        while True:
            try:
                await asyncio.sleep(30)  # Every 30 seconds
                
                # System metrics
                cpu_usage = psutil.cpu_percent(interval=1)
                memory_usage = psutil.virtual_memory().percent
                
                # GPU metrics
                gpu_stats = self.gpu_manager.get_memory_stats()
                gpu_memory_usage = gpu_stats.get("memory_usage_percent", 0)
                
                # Create metrics snapshot
                metrics = PerformanceMetrics(
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    gpu_memory_usage=gpu_memory_usage,
                    active_connections=0,  # Will be updated by connection optimizer
                    cache_hit_rate=0.0,  # Will be updated by cache systems
                    avg_response_time=0.0,  # Will be updated by request handlers
                    queue_sizes={
                        "batch_processing": self.batch_processor.pending_requests.qsize()
                    },
                    timestamp=time.time()
                )
                
                self.metrics_history.append(metrics)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
    
    async def _optimize_connection_pools(self):
        """Optimize connection pools based on usage patterns"""
        while True:
            try:
                await asyncio.sleep(600)  # Every 10 minutes
                
                recommendations = self.connection_optimizer.get_pool_recommendations()
                
                for pool_name, rec in recommendations.items():
                    efficiency = rec["efficiency"]
                    if efficiency < 0.5:  # Low efficiency
                        logger.warning(f"🔧 Pool {pool_name} has low efficiency: {efficiency:.2%}")
                    elif efficiency > 0.9:  # High efficiency
                        logger.info(f"✅ Pool {pool_name} has high efficiency: {efficiency:.2%}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection pool optimization error: {e}")
    
    async def optimize_ai_inference_batch(self, requests: List[Any], model_processor) -> List[Any]:
        """Optimize AI inference with batching and GPU management"""
        async with self.gpu_manager.manage_gpu_memory():
            return await self.batch_processor.process_batch(model_processor, requests)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        recent_metrics = list(self.metrics_history)[-10:]  # Last 10 measurements
        
        avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        avg_gpu = sum(m.gpu_memory_usage or 0 for m in recent_metrics) / len(recent_metrics)
        
        return {
            "system_performance": {
                "avg_cpu_usage": round(avg_cpu, 2),
                "avg_memory_usage": round(avg_memory, 2),
                "avg_gpu_usage": round(avg_gpu, 2) if avg_gpu > 0 else None,
                "status": "optimal" if avg_cpu < 70 and avg_memory < 80 else "high_usage"
            },
            "gpu_performance": self.gpu_manager.get_memory_stats(),
            "batch_processing": self.batch_processor.get_stats(),
            "connection_pools": self.connection_optimizer.get_pool_recommendations(),
            "optimization_status": {
                "active_tasks": len(self.optimization_tasks),
                "background_optimizations": list(self.optimization_tasks.keys())
            },
            "recommendations": self._get_optimization_recommendations(recent_metrics)
        }
    
    def _get_optimization_recommendations(self, metrics: List[PerformanceMetrics]) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if not metrics:
            return recommendations
        
        avg_cpu = sum(m.cpu_usage for m in metrics) / len(metrics)
        avg_memory = sum(m.memory_usage for m in metrics) / len(metrics)
        
        if avg_cpu > 80:
            recommendations.append("High CPU usage detected - consider scaling horizontally")
        
        if avg_memory > 85:
            recommendations.append("High memory usage detected - increase memory limits or optimize caching")
        
        # GPU recommendations
        gpu_stats = self.gpu_manager.get_memory_stats()
        if gpu_stats.get("memory_usage_percent", 0) > 85:
            recommendations.append("High GPU memory usage - consider batch size optimization")
        
        # Batch processing recommendations
        batch_stats = self.batch_processor.get_stats()
        if batch_stats["avg_batch_size"] < 5:
            recommendations.append("Low batch sizes detected - consider increasing max_wait_time")
        
        return recommendations


# Global performance optimizer instance
performance_optimizer = AdvancedPerformanceOptimizer()