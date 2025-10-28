from fastapi import APIRouter, Response
from ..core.monitoring import monitoring_service

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    """Endpoint для получения метрик Prometheus"""
    metrics_data = monitoring_service.get_metrics()
    return Response(
        content=metrics_data,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "sentry_initialized": monitoring_service.sentry_initialized,
        "tracing_initialized": monitoring_service.tracing_initialized
    }
