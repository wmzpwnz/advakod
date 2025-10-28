import time
import logging
from typing import Dict, Any, Optional
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
try:
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    _otel_available = True
except Exception:
    _otel_available = False

logger = logging.getLogger(__name__)

# Prometheus метрики
REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

CHAT_REQUESTS = Counter(
    'chat_requests_total',
    'Total chat requests',
    ['user_id', 'session_id']
)

CHAT_RESPONSE_TIME = Histogram(
    'chat_response_duration_seconds',
    'Chat response duration in seconds',
    ['model_type']
)

AI_MODEL_LOAD_TIME = Histogram(
    'ai_model_load_duration_seconds',
    'AI model loading time in seconds',
    ['model_name']
)

ACTIVE_SESSIONS = Gauge(
    'active_chat_sessions',
    'Number of active chat sessions'
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Number of active database connections'
)

MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)


class MonitoringService:
    """Сервис мониторинга приложения"""
    
    def __init__(self):
        self.sentry_initialized = False
        self.tracing_initialized = False
        
    def init_sentry(self, dsn: str, environment: str = "development"):
        """Инициализация Sentry для отслеживания ошибок"""
        try:
            sentry_sdk.init(
                dsn=dsn,
                environment=environment,
                integrations=[
                    FastApiIntegration(auto_enabling_instrumentations=False),
                    SqlalchemyIntegration(),
                    HttpxIntegration(),
                ],
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
            )
            self.sentry_initialized = True
            logger.info("Sentry инициализирован успешно")
        except Exception as e:
            logger.error(f"Ошибка инициализации Sentry: {e}")
    
    def init_tracing(self, jaeger_endpoint: str = "http://localhost:14268/api/traces"):
        """Инициализация OpenTelemetry трейсинга"""
        if not _otel_available:
            logger.warning("OpenTelemetry недоступен — трейсинг отключен для dev")
            return
        try:
            # Настройка ресурса
            resource = Resource.create({
                "service.name": "ai-lawyer-backend",
                "service.version": "1.0.0",
            })
            
            # Настройка Jaeger экспортера
            jaeger_exporter = JaegerExporter(
                agent_host_name="localhost",
                agent_port=6831,
            )
            
            # Настройка провайдера трейсов
            trace.set_tracer_provider(TracerProvider(resource=resource))
            tracer = trace.get_tracer(__name__)
            
            # Добавление процессора
            span_processor = BatchSpanProcessor(jaeger_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            
            self.tracing_initialized = True
            logger.info("OpenTelemetry трейсинг инициализирован успешно")
        except Exception as e:
            logger.error(f"Ошибка инициализации трейсинга: {e}")
    
    def instrument_fastapi(self, app):
        """Инструментирование FastAPI приложения"""
        if self.tracing_initialized and _otel_available:
            FastAPIInstrumentor.instrument_app(app)
            SQLAlchemyInstrumentor().instrument()
            HTTPXClientInstrumentor().instrument()
            logger.info("FastAPI приложение инструментировано для трейсинга")
    
    def track_request(self, request: Request, response: Response, duration: float):
        """Отслеживание HTTP запросов"""
        endpoint = request.url.path
        method = request.method
        status_code = response.status_code
        
        # Prometheus метрики
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        # Sentry контекст
        if self.sentry_initialized:
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("endpoint", endpoint)
                scope.set_tag("method", method)
                scope.set_tag("status_code", status_code)
    
    def track_chat_request(self, user_id: int, session_id: int, duration: float, model_type: str = "qwen"):
        """Отслеживание запросов к чату"""
        CHAT_REQUESTS.labels(
            user_id=str(user_id),
            session_id=str(session_id)
        ).inc()
        
        CHAT_RESPONSE_TIME.labels(
            model_type=model_type
        ).observe(duration)
    
    def track_model_load(self, model_name: str, duration: float):
        """Отслеживание времени загрузки модели"""
        AI_MODEL_LOAD_TIME.labels(
            model_name=model_name
        ).observe(duration)
    
    def update_active_sessions(self, count: int):
        """Обновление количества активных сессий"""
        ACTIVE_SESSIONS.set(count)
    
    def update_database_connections(self, count: int):
        """Обновление количества подключений к БД"""
        DATABASE_CONNECTIONS.set(count)
    
    def update_system_metrics(self, memory_bytes: int, cpu_percent: float):
        """Обновление системных метрик"""
        MEMORY_USAGE.set(memory_bytes)
        CPU_USAGE.set(cpu_percent)
    
    def capture_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """Захват исключений в Sentry"""
        if self.sentry_initialized:
            if context:
                with sentry_sdk.configure_scope() as scope:
                    for key, value in context.items():
                        scope.set_extra(key, value)
            sentry_sdk.capture_exception(exception)
        else:
            logger.error(f"Exception: {exception}", exc_info=True)
    
    def capture_message(self, message: str, level: str = "info", context: Optional[Dict[str, Any]] = None):
        """Захват сообщений в Sentry"""
        if self.sentry_initialized:
            if context:
                with sentry_sdk.configure_scope() as scope:
                    for key, value in context.items():
                        scope.set_extra(key, value)
            sentry_sdk.capture_message(message, level=level)
        else:
            logger.info(f"Message: {message}")
    
    def get_metrics(self) -> str:
        """Получение метрик в формате Prometheus"""
        return generate_latest()


# Декоратор для отслеживания времени выполнения функций
def track_execution_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Декоратор для отслеживания времени выполнения функций"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                # Здесь можно добавить логику для записи метрик
                logger.debug(f"{func.__name__} выполнен за {duration:.3f} секунд")
        return async_wrapper
    
    def sync_decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                logger.debug(f"{func.__name__} выполнен за {duration:.3f} секунд")
        return sync_wrapper
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_decorator


# Глобальный экземпляр сервиса мониторинга
monitoring_service = MonitoringService()
