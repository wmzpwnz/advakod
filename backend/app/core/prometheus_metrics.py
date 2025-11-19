"""
Prometheus Metrics for AI-Lawyer System
Экспортирует метрики для мониторинга производительности и бизнес-процессов
"""

import time
import logging
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Histogram, Gauge, Info, Enum,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from datetime import datetime
import psutil
import threading

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """Prometheus metrics collector for AI-Lawyer system"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        
        # HTTP Request Metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0],
            registry=self.registry
        )
        
        # AI/ML Metrics
        self.ai_inference_requests = Counter(
            'ai_inference_requests_total',
            'Total AI inference requests',
            ['model_type', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.ai_inference_duration = Histogram(
            'ai_inference_duration_seconds',
            'AI inference duration in seconds',
            ['model_type', 'endpoint'],
            buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0],
            registry=self.registry
        )
        
        self.ai_token_usage = Counter(
            'ai_tokens_processed_total',
            'Total tokens processed by AI models',
            ['model_type', 'operation'],
            registry=self.registry
        )
        
        # Rate Limiting Metrics
        self.rate_limit_hits = Counter(
            'rate_limit_hits_total',
            'Total rate limit hits',
            ['user_tier', 'endpoint_type', 'limit_type'],
            registry=self.registry
        )
        
        self.rate_limit_wait_time = Histogram(
            'rate_limit_wait_duration_seconds',
            'Rate limit wait time in seconds',
            ['user_tier', 'endpoint_type'],
            buckets=[1, 5, 10, 30, 60, 300, 600],
            registry=self.registry
        )
        
        # Cache Metrics
        self.cache_operations = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['cache_type', 'operation', 'result'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_size = Gauge(
            'cache_size_items',
            'Number of items in cache',
            ['cache_type'],
            registry=self.registry
        )
        
        # Database Metrics
        self.db_connections = Gauge(
            'database_connections_active',
            'Active database connections',
            ['database'],
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'database_query_duration_seconds',
            'Database query duration in seconds',
            ['database', 'operation'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self.registry
        )
        
        # Vector Store Metrics
        self.vector_operations = Counter(
            'vector_store_operations_total',
            'Total vector store operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.vector_search_duration = Histogram(
            'vector_search_duration_seconds',
            'Vector search duration in seconds',
            ['search_type'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        self.vector_documents_count = Gauge(
            'vector_store_documents_total',
            'Total documents in vector store',
            registry=self.registry
        )
        
        # Business Metrics
        self.user_sessions = Counter(
            'user_sessions_total',
            'Total user sessions',
            ['user_tier'],
            registry=self.registry
        )
        
        self.legal_queries = Counter(
            'legal_queries_total',
            'Total legal queries',
            ['query_type', 'success'],
            registry=self.registry
        )
        
        self.document_uploads = Counter(
            'document_uploads_total',
            'Total document uploads',
            ['document_type', 'status'],
            registry=self.registry
        )
        
        # Training Metrics
        self.training_jobs = Counter(
            'training_jobs_total',
            'Total training jobs',
            ['job_type', 'status'],
            registry=self.registry
        )
        
        self.training_duration = Histogram(
            'training_job_duration_seconds',
            'Training job duration in seconds',
            ['job_type'],
            buckets=[60, 300, 900, 1800, 3600, 7200, 14400, 28800],
            registry=self.registry
        )
        
        # System Metrics
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            'system_disk_usage_bytes',
            'System disk usage in bytes',
            ['mount_point'],
            registry=self.registry
        )
        
        # Model Status
        self.model_status = Enum(
            'model_status',
            'Model status',
            ['model_name'],
            states=['loading', 'ready', 'error', 'unloaded'],
            registry=self.registry
        )
        
        self.model_info = Info(
            'model_info',
            'Model information',
            ['model_name'],
            registry=self.registry
        )
        
        # Error Metrics
        self.errors_total = Counter(
            'errors_total',
            'Total errors',
            ['error_type', 'component'],
            registry=self.registry
        )
        
        # Start system metrics collection
        self._start_system_metrics_collection()
    
    def _start_system_metrics_collection(self):
        """Start background thread for system metrics collection"""
        def collect_system_metrics():
            while True:
                try:
                    # CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    self.system_cpu_usage.set(cpu_percent)
                    
                    # Memory usage
                    memory = psutil.virtual_memory()
                    self.system_memory_usage.set(memory.used)
                    
                    # Disk usage
                    for partition in psutil.disk_partitions():
                        try:
                            usage = psutil.disk_usage(partition.mountpoint)
                            self.system_disk_usage.labels(
                                mount_point=partition.mountpoint
                            ).set(usage.used)
                        except PermissionError:
                            continue
                    
                    time.sleep(15)  # Collect every 15 seconds
                    
                except Exception as e:
                    logger.error(f"Error collecting system metrics: {e}")
                    time.sleep(60)  # Wait longer on error
        
        thread = threading.Thread(target=collect_system_metrics, daemon=True)
        thread.start()
        logger.info("✅ System metrics collection started")
    
    # Convenience methods for common operations
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        self.http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()
        self.http_request_duration.labels(
            method=method, endpoint=endpoint
        ).observe(duration)
    
    def record_ai_inference(self, model_type: str, endpoint: str, duration: float, 
                           tokens: int = 0, success: bool = True):
        """Record AI inference metrics"""
        status = 'success' if success else 'error'
        self.ai_inference_requests.labels(
            model_type=model_type, endpoint=endpoint, status=status
        ).inc()
        
        if success:
            self.ai_inference_duration.labels(
                model_type=model_type, endpoint=endpoint
            ).observe(duration)
            
            if tokens > 0:
                self.ai_token_usage.labels(
                    model_type=model_type, operation='generation'
                ).inc(tokens)
    
    def record_rate_limit(self, user_tier: str, endpoint_type: str, 
                         limit_type: str, wait_time: float = 0):
        """Record rate limit hit"""
        self.rate_limit_hits.labels(
            user_tier=user_tier, endpoint_type=endpoint_type, limit_type=limit_type
        ).inc()
        
        if wait_time > 0:
            self.rate_limit_wait_time.labels(
                user_tier=user_tier, endpoint_type=endpoint_type
            ).observe(wait_time)
    
    def record_cache_operation(self, cache_type: str, operation: str, result: str):
        """Record cache operation"""
        self.cache_operations.labels(
            cache_type=cache_type, operation=operation, result=result
        ).inc()
    
    def update_cache_stats(self, cache_type: str, hit_ratio: float, size: int):
        """Update cache statistics"""
        self.cache_hit_ratio.labels(cache_type=cache_type).set(hit_ratio)
        self.cache_size.labels(cache_type=cache_type).set(size)
    
    def record_vector_operation(self, operation: str, status: str, duration: float = None):
        """Record vector store operation"""
        self.vector_operations.labels(operation=operation, status=status).inc()
        
        if duration is not None and status == 'success':
            search_type = 'semantic' if 'search' in operation else 'other'
            self.vector_search_duration.labels(search_type=search_type).observe(duration)
    
    def update_vector_documents(self, count: int):
        """Update vector store document count"""
        self.vector_documents_count.set(count)
    
    def record_user_session(self, user_tier: str):
        """Record user session"""
        self.user_sessions.labels(user_tier=user_tier).inc()
    
    def record_legal_query(self, query_type: str, success: bool):
        """Record legal query"""
        success_str = 'success' if success else 'error'
        self.legal_queries.labels(query_type=query_type, success=success_str).inc()
    
    def record_training_job(self, job_type: str, status: str, duration: float = None):
        """Record training job"""
        self.training_jobs.labels(job_type=job_type, status=status).inc()
        
        if duration is not None and status == 'completed':
            self.training_duration.labels(job_type=job_type).observe(duration)
    
    def update_model_status(self, model_name: str, status: str, info: Dict[str, str] = None):
        """Update model status"""
        self.model_status.labels(model_name=model_name).state(status)
        
        if info:
            self.model_info.labels(model_name=model_name).info(info)
    
    def record_error(self, error_type: str, component: str):
        """Record error occurrence"""
        self.errors_total.labels(error_type=error_type, component=component).inc()
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get content type for metrics endpoint"""
        return CONTENT_TYPE_LATEST


# Global metrics instance
prometheus_metrics = PrometheusMetrics()


# Decorator for automatic metrics collection
def monitor_endpoint(endpoint_name: str = None, model_type: str = None):
    """Decorator to automatically collect metrics for endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or func.__name__
            success = True
            status_code = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                status_code = 500
                prometheus_metrics.record_error(
                    error_type=type(e).__name__,
                    component=endpoint
                )
                raise
            finally:
                duration = time.time() - start_time
                
                # Record HTTP metrics if this is an HTTP endpoint
                if hasattr(args[0], 'method') if args else False:
                    request = args[0]
                    prometheus_metrics.record_http_request(
                        method=request.method,
                        endpoint=endpoint,
                        status_code=status_code,
                        duration=duration
                    )
                
                # Record AI metrics if this is an AI endpoint
                if model_type:
                    prometheus_metrics.record_ai_inference(
                        model_type=model_type,
                        endpoint=endpoint,
                        duration=duration,
                        success=success
                    )
        
        return wrapper
    return decorator