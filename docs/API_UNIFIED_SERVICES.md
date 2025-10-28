# API Documentation - Unified Services

## Overview

Документация по API endpoints для унифицированной архитектуры AI-сервисов АДВАКОД.

## Authentication

Все endpoints требуют аутентификации через JWT токен:

```bash
Authorization: Bearer <jwt_token>
```

## Unified Chat API

### POST /api/v1/chat/enhanced

Унифицированный endpoint для чата с поддержкой RAG и LLM.

**Request:**
```json
{
  "message": "Какие права у работника при увольнении?",
  "context": "Дополнительный контекст",
  "use_rag": true,
  "situation_date": "2024-01-15"
}
```

**Response:**
```json
{
  "response": "Подробный юридический ответ...",
  "sources": [
    {
      "content": "Текст источника",
      "similarity": 0.85,
      "relevance": 0.92,
      "source_type": "hybrid",
      "metadata": {
        "article": "80",
        "source": "ТК РФ"
      }
    }
  ],
  "quality_score": 0.88,
  "processing_time": 12.5,
  "session_id": "uuid"
}
```

## System Status API

### GET /ready

Проверка готовности унифицированной системы.

**Response:**
```json
{
  "ready": true,
  "system_status": "healthy",
  "services": {
    "total": 2,
    "healthy": 2,
    "degraded": 0,
    "unhealthy": 0
  },
  "monitoring": {
    "status": "healthy",
    "metrics_count": 45,
    "active_alerts": 0
  },
  "uptime": 3600.5,
  "last_check": "2024-01-15T10:30:00Z"
}
```

### GET /health

Простая проверка жизнеспособности.

**Response:**
```json
{
  "status": "healthy",
  "service": "ai-lawyer-backend",
  "version": "2.0.0",
  "timestamp": 1705312200
}
```

## Metrics API

### GET /metrics

Prometheus метрики в exposition format.

**Response:**
```
# HELP llm_requests_per_minute LLM requests per minute
# TYPE llm_requests_per_minute gauge
llm_requests_per_minute 12.5

# HELP rag_cache_hit_rate RAG cache hit rate
# TYPE rag_cache_hit_rate gauge
rag_cache_hit_rate 0.75
```

### GET /metrics/json

JSON метрики для дашбордов.

**Response:**
```json
{
  "unified_services": {
    "unified_llm": {
      "requests_per_minute": 12.5,
      "average_response_time": 8.2,
      "error_rate": 0.02,
      "queue_length": 3,
      "concurrent_requests": 2
    },
    "unified_rag": {
      "search_time_avg": 1.2,
      "cache_hit_rate": 0.75,
      "vector_store_size": 15000,
      "total_searches": 1250
    }
  },
  "service_manager": {
    "initialization": {
      "total_initializations": 2,
      "successful_initializations": 2,
      "average_initialization_time": 25.3
    },
    "services": {
      "unified_llm": {
        "status": "healthy",
        "error_count": 0,
        "restart_count": 0
      }
    }
  },
  "monitoring_dashboard": {
    "metrics": {
      "llm_requests_per_minute": 12.5,
      "system_cpu_usage_percent": 45.2,
      "service_health_score": 1.0
    },
    "alerts": {
      "active": [],
      "count": 0
    }
  },
  "timestamp": 1705312200
}
```

## Chat Statistics API

### GET /api/v1/chat/health

Проверка здоровья чат-сервиса.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "unified_llm": true,
    "unified_rag": true
  },
  "timestamp": 1705312200
}
```

### GET /api/v1/chat/stats

Статистика чат-сервиса (только для админов).

**Response:**
```json
{
  "unified_llm_stats": {
    "requests_per_minute": 12.5,
    "average_response_time": 8.2,
    "p95_response_time": 15.1,
    "error_rate": 0.02,
    "total_requests": 5420,
    "successful_requests": 5309,
    "failed_requests": 111
  },
  "rag_stats": {
    "search_time_avg": 1.2,
    "generation_time_avg": 7.1,
    "cache_hit_rate": 0.75,
    "vector_store_size": 15000,
    "total_searches": 1250,
    "successful_searches": 1198,
    "failed_searches": 52
  },
  "performance": {
    "uptime": 3600.5,
    "memory_usage": 2048.5,
    "cpu_usage": 45.2
  },
  "timestamp": 1705312200
}
```

## Error Responses

### Standard Error Format

```json
{
  "error": "error_code",
  "message": "Human readable error message",
  "details": {
    "field": "Additional error details"
  },
  "timestamp": 1705312200,
  "request_id": "uuid"
}
```

### Common Error Codes

- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `429` - Too Many Requests (rate limited)
- `500` - Internal Server Error
- `503` - Service Unavailable (system not ready)

## Rate Limiting

### Limits

- **Chat API**: 60 requests/minute per user
- **Metrics API**: 120 requests/minute per user
- **Status API**: 300 requests/minute per user

### Headers

```
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705312260
```

## WebSocket API (Future)

### /ws/chat

Real-time streaming chat interface.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat?token=jwt_token');
```

**Message Format:**
```json
{
  "type": "chat_request",
  "data": {
    "message": "Вопрос пользователя",
    "use_rag": true
  }
}
```

**Response Stream:**
```json
{"type": "token", "data": {"token": "Ответ"}}
{"type": "token", "data": {"token": " по"}}
{"type": "token", "data": {"token": " частям"}}
{"type": "complete", "data": {"sources": [...], "quality_score": 0.88}}
```

## Migration Notes

### Breaking Changes from v1.x

1. **Endpoint Changes:**
   - Legacy endpoints still work but deprecated
   - New unified endpoints recommended

2. **Response Format:**
   - `sources` structure changed (added `source_type`, `relevance`)
   - `quality_score` replaces separate validation scores

3. **Error Handling:**
   - Standardized error format
   - Better error messages and codes

### Backward Compatibility

Legacy endpoints remain functional but will be removed in v3.0:
- Use new unified endpoints for new integrations
- Migrate existing integrations gradually

---

**API Version**: 2.0  
**Last Updated**: 2024-01-15  
**Status**: Production Ready