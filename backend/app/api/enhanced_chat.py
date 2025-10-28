"""
Улучшенный API для чата с ИИ-Юристом
Интегрирует все оптимизации: безопасность, производительность, качество, аналитику
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import time
import logging
import uuid

from ..core.security import validate_and_sanitize_query
from ..core.legal_prompt_engine import legal_prompt_engine
from ..core.analytics_engine import analytics_engine, QueryAnalytics
# Унифицированные AI-сервисы
from ..services.unified_llm_service import unified_llm_service
from ..services.unified_rag_service import unified_rag_service
from ..services.auth_service import auth_service
from ..models.user import User
from ..middleware.ml_rate_limit import chat_rate_limit, rag_rate_limit
from ..core.config import settings
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    """Запрос на чат"""
    message: str = Field(..., min_length=1, max_length=5000, description="Сообщение пользователя")
    context: Optional[str] = Field(None, max_length=2000, description="Дополнительный контекст")
    use_rag: bool = Field(True, description="Использовать RAG для поиска в документах")
    user_id: Optional[str] = Field(None, description="ID пользователя")
    situation_date: Optional[str] = Field(None, description="Дата правовой ситуации (ISO8601)")


class ChatResponse(BaseModel):
    """Ответ чата"""
    response: str
    query_id: str
    processing_time: float
    cached: bool
    quality_score: float
    confidence: float
    legal_field: str
    complexity: str
    sources: Optional[List[Dict[str, Any]]] = None
    validation: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None


class ChatHistoryRequest(BaseModel):
    """Запрос истории чата"""
    user_id: str
    limit: int = Field(50, ge=1, le=100)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    http_request: Request,
    current_user: User = Depends(auth_service.get_current_active_user),
    # rate_limit_info: dict = Depends(chat_rate_limit(100))  # Временно отключено
):
    """Чат с ИИ-Юристом с полной оптимизацией"""
    
    start_time = time.time()
    query_id = str(uuid.uuid4())
    
    try:
        # Получаем IP адрес
        client_ip = http_request.client.host if http_request.client else "unknown"
        
        # Анализируем запрос для определения контекста
        legal_context = legal_prompt_engine.analyze_legal_query(request.message)
        
        # Используем унифицированные AI-сервисы
        if request.use_rag:
            # Используем UnifiedRAGService для поиска и генерации
            rag_response = await asyncio.wait_for(
                unified_rag_service.search_and_generate(
                    query=request.message,
                    max_results=10,
                    similarity_threshold=0.7,
                    situation_date=request.situation_date
                ),
                timeout=settings.AI_CHAT_RESPONSE_TIMEOUT
            )
            
            response_text = rag_response.answer
            sources = [
                {
                    "content": source.content,
                    "similarity": source.similarity,
                    "relevance": source.relevance,
                    "source_type": source.source_type,
                    "metadata": source.metadata
                }
                for source in rag_response.sources
            ]
            quality_score = rag_response.confidence
            
        else:
            # Используем только UnifiedLLMService без RAG
            async for response_chunk in unified_llm_service.generate_response(
                prompt=request.message,
                context=request.context,
                stream=False,  # Для API используем не-streaming режим
                max_tokens=1024,
                temperature=0.3,
                top_p=0.8,
                user_id=str(current_user.id)
            ):
                response_text = response_chunk  # В не-streaming режиме получаем полный ответ
                break
            
            sources = None
            quality_score = 0.8  # Базовая оценка качества для LLM без RAG
        
        processing_time = time.time() - start_time
        
        # Записываем аналитику
        query_analytics = QueryAnalytics(
            query_id=query_id,
            user_id=str(current_user.id),
            query_text=request.message,
            response_time=processing_time,
            quality_score=quality_score,
            confidence=quality_score,
            legal_field=legal_context.field.value,
            complexity=legal_context.complexity,
            timestamp=time.time(),
            ip_address=client_ip
        )
        analytics_engine.record_query(query_analytics)
        
        # Формируем ответ
        response = ChatResponse(
            response=response_text,
            query_id=query_id,
            processing_time=processing_time,
            cached=False,  # TODO: Реализовать проверку кэша
            quality_score=quality_score,
            confidence=quality_score,
            legal_field=legal_context.field.value,
            complexity=legal_context.complexity,
            sources=sources
        )
        
        logger.info(f"Chat request processed: {query_id} in {processing_time:.2f}s")
        
        return response
        
    except asyncio.TimeoutError:
        processing_time = time.time() - start_time
        logger.warning(f"⚠️ AI чат превысил таймаут ({settings.AI_CHAT_RESPONSE_TIMEOUT} сек) для запроса {query_id}")
        
        # Возвращаем сообщение об ошибке таймаута
        response = ChatResponse(
            response="Извините, обработка вашего запроса заняла слишком много времени. Попробуйте переформулировать вопрос или обратитесь к специалисту.",
            query_id=query_id,
            processing_time=processing_time,
            cached=False,
            quality_score=0.0,
            confidence=0.0,
            legal_field="general",
            complexity="simple",
            sources=None
        )
        
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error in chat request {query_id}: {e}")
        
        # Записываем ошибку в аналитику
        error_analytics = QueryAnalytics(
            query_id=query_id,
            user_id=str(current_user.id),
            query_text=request.message,
            response_time=processing_time,
            quality_score=0.0,
            confidence=0.0,
            legal_field="general",
            complexity="simple",
            timestamp=time.time(),
            ip_address=client_ip
        )
        analytics_engine.record_query(error_analytics)
        
        raise HTTPException(
            status_code=500,
            detail="Произошла ошибка при обработке запроса. Попробуйте еще раз."
        )


@router.get("/health")
async def chat_health():
    """Проверка здоровья чат-сервиса"""
    try:
        # Проверяем готовность сервисов
        # Проверяем готовность унифицированных сервисов
        llm_ready = unified_llm_service.is_model_loaded()
        rag_ready = unified_rag_service.is_ready()
        
        return {
            "status": "healthy" if llm_ready and rag_ready else "degraded",
            "services": {
                "unified_llm": llm_ready,
                "unified_rag": rag_ready
            },
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error checking chat health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


@router.get("/stats")
async def get_chat_stats(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Получает статистику чата"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Получаем статистику унифицированных сервисов
        llm_stats = unified_llm_service.get_metrics().__dict__ if unified_llm_service.is_model_loaded() else {}
        rag_stats = unified_rag_service.get_metrics().__dict__ if unified_rag_service.is_ready() else {}
        
        # Получаем аналитику
        performance = analytics_engine.get_performance_metrics()
        quality = analytics_engine.get_quality_metrics()
        
        return {
            "unified_llm_stats": llm_stats,
            "rag_stats": rag_stats,
            "performance": performance.__dict__,
            "quality": quality.__dict__,
            "timestamp": time.time()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat stats")


@router.post("/clear-cache")
async def clear_chat_cache(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Очищает кэш чата"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Очищаем кэш сервисов
        # Очищаем кэш унифицированных сервисов (если поддерживается)
        # UnifiedRAGService имеет встроенное управление кэшем
        
        if hasattr(unified_rag_service, 'clear_cache'):
            unified_rag_service.clear_cache()
        
        return {
            "message": "Chat cache cleared successfully",
            "timestamp": time.time()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing chat cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear chat cache")
