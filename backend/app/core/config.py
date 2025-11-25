from pydantic_settings import BaseSettings
from pydantic import Field, model_validator, field_validator
from typing import Optional
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Settings(BaseSettings):
    # Основные настройки
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "АДВАКОД - ИИ-Юрист для РФ")
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # База данных (SQLite для разработки, PostgreSQL для продакшена)
    # В Docker использует имя сервиса 'postgres', в локальной разработке - localhost
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://codes_user:codes_password@postgres:5433/codes_db")
    
    # PostgreSQL настройки для продакшена
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5433"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "codes_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "codes_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "codes_db")
    
    # Окружение
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Папки для загрузок и логов
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))
    VOICE_UPLOAD_DIR: str = os.getenv("VOICE_UPLOAD_DIR", os.path.join(UPLOAD_DIR, "voice"))
    DOCUMENT_UPLOAD_DIR: str = os.getenv("DOCUMENT_UPLOAD_DIR", os.path.join(UPLOAD_DIR, "documents"))
    LOG_DIR: str = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "logs"))
    TEMP_DIR: str = os.getenv("TEMP_DIR", os.path.join(BASE_DIR, "temp"))
    
    # Qdrant векторная база данных
    # В Docker использует имя сервиса 'qdrant', в локальной разработке - localhost
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "legal_documents")
    
    # Vistral-24B-Instruct модель (русскоязычная, 24B параметров)
    VISTRAL_MODEL_PATH: str = os.getenv("VISTRAL_MODEL_PATH", "/opt/advakod/models/vistral/Vistral-24B-Instruct-Q5_0.gguf")
    VISTRAL_N_CTX: int = int(os.getenv("VISTRAL_N_CTX", "8192"))  # Полный контекст для мощного железа
    VISTRAL_N_THREADS: int = int(os.getenv("VISTRAL_N_THREADS", "10"))  # Все ядра для мощного железа
    VISTRAL_N_BATCH: int = int(os.getenv("VISTRAL_N_BATCH", "512"))  # Размер батча для ускорения (512 оптимален для CPU, 1024 для GPU)
    VISTRAL_N_GPU_LAYERS: int = int(os.getenv("VISTRAL_N_GPU_LAYERS", "0"))
    VISTRAL_INFERENCE_TIMEOUT: int = int(os.getenv("VISTRAL_INFERENCE_TIMEOUT", "1800"))  # 30 минут для 24B модели
    VISTRAL_MAX_CONCURRENCY: int = int(os.getenv("VISTRAL_MAX_CONCURRENCY", "5"))  # Больше запросов для мощного железа
    # Доп. параметр очереди запросов для UnifiedLLMService
    VISTRAL_QUEUE_SIZE: int = int(os.getenv("VISTRAL_QUEUE_SIZE", "50"))
    VISTRAL_TOKEN_MARGIN: int = int(os.getenv("VISTRAL_TOKEN_MARGIN", "512"))  # Больше токенов для мощного железа
    VISTRAL_REPEAT_PENALTY: float = float(os.getenv("VISTRAL_REPEAT_PENALTY", "1.1"))
    VISTRAL_STOP_TOKENS: Optional[str] = os.getenv("VISTRAL_STOP_TOKENS", None)
    VISTRAL_USE_MLOCK: bool = os.getenv("VISTRAL_USE_MLOCK", "false").lower() == "true"  # По умолчанию False для CPU
    LOG_PROMPTS: bool = os.getenv("LOG_PROMPTS", "false").lower() == "true"
    
    # Дополнительные параметры оптимизации
    VISTRAL_TEMPERATURE: float = float(os.getenv("VISTRAL_TEMPERATURE", "0.7"))  # Температура генерации
    VISTRAL_TOP_P: float = float(os.getenv("VISTRAL_TOP_P", "0.9"))  # Top-p sampling
    VISTRAL_TOP_K: int = int(os.getenv("VISTRAL_TOP_K", "40"))  # Top-k sampling
    VISTRAL_MEMORY_FRACTION: float = float(os.getenv("VISTRAL_MEMORY_FRACTION", "0.8"))  # Доля памяти для модели
    
    # WebSocket настройки (для стабильности real-time соединений)
    WEBSOCKET_MAX_CONNECTIONS_PER_IP: int = int(os.getenv("WEBSOCKET_MAX_CONNECTIONS_PER_IP", "5"))
    WEBSOCKET_RATE_LIMIT_WINDOW: int = int(os.getenv("WEBSOCKET_RATE_LIMIT_WINDOW", "60"))  # сек
    WEBSOCKET_CONNECTION_TIMEOUT: int = int(os.getenv("WEBSOCKET_CONNECTION_TIMEOUT", "10"))  # сек
    WEBSOCKET_MAX_MESSAGE_SIZE: int = int(os.getenv("WEBSOCKET_MAX_MESSAGE_SIZE", "1048576"))  # 1MB
    WEBSOCKET_PING_INTERVAL: int = int(os.getenv("WEBSOCKET_PING_INTERVAL", "10"))  # сек
    WEBSOCKET_PONG_TIMEOUT: int = int(os.getenv("WEBSOCKET_PONG_TIMEOUT", "10"))  # сек
    
    # Настройки унифицированных AI-сервисов
    RAG_MAX_RESULTS: int = int(os.getenv("RAG_MAX_RESULTS", "20"))
    RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))
    RAG_RERANK_TOP_K: int = int(os.getenv("RAG_RERANK_TOP_K", "5"))
    RAG_CONTEXT_WINDOW: int = int(os.getenv("RAG_CONTEXT_WINDOW", "4000"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
    RAG_ENABLE_RERANKING: bool = os.getenv("RAG_ENABLE_RERANKING", "true").lower() == "true"
    RAG_ENABLE_HYBRID_SEARCH: bool = os.getenv("RAG_ENABLE_HYBRID_SEARCH", "true").lower() == "true"
    
    # Настройки мониторинга
    SERVICE_HEALTH_CHECK_INTERVAL: int = int(os.getenv("SERVICE_HEALTH_CHECK_INTERVAL", "30"))
    SERVICE_MAX_RESTART_ATTEMPTS: int = int(os.getenv("SERVICE_MAX_RESTART_ATTEMPTS", "3"))
    SERVICE_RESTART_DELAY: int = int(os.getenv("SERVICE_RESTART_DELAY", "5"))
    MONITORING_COLLECTION_INTERVAL: int = int(os.getenv("MONITORING_COLLECTION_INTERVAL", "30"))
    MONITORING_ALERT_CHECK_INTERVAL: int = int(os.getenv("MONITORING_ALERT_CHECK_INTERVAL", "60"))
    
    # Таймауты для разных типов AI-анализа
    AI_DOCUMENT_ANALYSIS_TIMEOUT: int = int(os.getenv("AI_DOCUMENT_ANALYSIS_TIMEOUT", "600"))  # 10 минут для анализа документов
    AI_CHAT_RESPONSE_TIMEOUT: int = int(os.getenv("AI_CHAT_RESPONSE_TIMEOUT", "300"))  # 5 минут для чата
    AI_COMPLEX_ANALYSIS_TIMEOUT: int = int(os.getenv("AI_COMPLEX_ANALYSIS_TIMEOUT", "1200"))  # 20 минут для сложного анализа
    AI_EMBEDDINGS_TIMEOUT: int = int(os.getenv("AI_EMBEDDINGS_TIMEOUT", "60"))  # 1 минута для эмбеддингов
    
    # Настройки токенов для AI-анализа
    AI_DOCUMENT_ANALYSIS_TOKENS: int = int(os.getenv("AI_DOCUMENT_ANALYSIS_TOKENS", "30000"))  # 30000 токенов для анализа документов
    AI_CHAT_RESPONSE_TOKENS: int = int(os.getenv("AI_CHAT_RESPONSE_TOKENS", "4000"))  # Больше токенов для мощного железа
    AI_COMPLEX_ANALYSIS_TOKENS: int = int(os.getenv("AI_COMPLEX_ANALYSIS_TOKENS", "20000"))  # 20000 токенов для сложного анализа
    AI_EMBEDDINGS_TOKENS: int = int(os.getenv("AI_EMBEDDINGS_TOKENS", "1000"))  # 1000 токенов для эмбеддингов
    
    # JWT настройки - КРИТИЧЕСКИ ВАЖНО
    SECRET_KEY: str = Field(
        default=os.getenv("SECRET_KEY", "DevSecretKey123" + "X" * 50),
        min_length=32, 
        description="JWT secret key (minimum 32 characters)"
    )
    
    @field_validator('SECRET_KEY', mode='before')
    @classmethod
    def clean_secret_key(cls, v):
        """Убираем кавычки из SECRET_KEY если они есть"""
        if isinstance(v, str):
            return v.strip('"').strip("'")
        return v
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    
    # CORS настройки - безопасная конфигурация
    CORS_ORIGINS: Optional[str] = None
    BACKEND_CORS_ORIGINS: Optional[str] = None  # Для совместимости с docker-compose
    
    def get_cors_origins(self) -> list:
        """Получаем CORS origins в зависимости от окружения"""
        if self.ENVIRONMENT == "development":
            # Локальная разработка - разрешаем localhost
            return [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
            ]
        else:
            # В продакшене используем BACKEND_CORS_ORIGINS или CORS_ORIGINS
            cors_env = self.BACKEND_CORS_ORIGINS or self.CORS_ORIGINS or "https://advacodex.com,https://www.advacodex.com"
            production_origins = cors_env.split(",")
            return [origin.strip() for origin in production_origins if origin.strip()]
    
    # Настройки для разработки
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Мониторинг
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    # В Docker использует имя сервиса 'jaeger', в локальной разработке - localhost
    JAEGER_ENDPOINT: str = os.getenv("JAEGER_ENDPOINT", "http://jaeger:14268/api/traces")
    
    # Кэширование
    # В Docker использует имя сервиса 'redis', в локальной разработке - localhost
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
    CACHE_TTL_DEFAULT: int = int(os.getenv("CACHE_TTL_DEFAULT", "3600"))
    CACHE_TTL_AI_RESPONSE: int = int(os.getenv("CACHE_TTL_AI_RESPONSE", "7200"))
    CACHE_TTL_USER_PROFILE: int = int(os.getenv("CACHE_TTL_USER_PROFILE", "1800"))
    
    # Шифрование данных
    ENCRYPTION_KEY: str = Field(
        default=os.getenv("ENCRYPTION_KEY", "EncryptionKey456" + "Y" * 50),  # Safe default for dev
        min_length=32, 
        description="Encryption key for sensitive data"
    )
    
    # Админская безопасность
    # Белый список IP адресов для доступа к админке (только в продакшене)
    # В development режиме проверка IP отключена
    ADMIN_IP_WHITELIST: str = os.getenv("ADMIN_IP_WHITELIST", "127.0.0.1,::1")
    
    @model_validator(mode='after')
    def validate_secret_key(self):
        """Валидация SECRET_KEY"""
        if len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if not any(c.isupper() for c in self.SECRET_KEY):
            raise ValueError("SECRET_KEY must contain uppercase letters")
        if not any(c.islower() for c in self.SECRET_KEY):
            raise ValueError("SECRET_KEY must contain lowercase letters")
        if not any(c.isdigit() for c in self.SECRET_KEY):
            raise ValueError("SECRET_KEY must contain digits")
        return self
    
    @model_validator(mode='after')
    def validate_encryption_key(self):
        """Валидация ключа шифрования"""
        if len(self.ENCRYPTION_KEY) < 32:
            raise ValueError("ENCRYPTION_KEY must be at least 32 characters long")
        return self
    
    @model_validator(mode='after')
    def validate_database_config(self):
        """Валидация конфигурации базы данных"""
        if self.ENVIRONMENT == "production":
            if not self.POSTGRES_PASSWORD or len(self.POSTGRES_PASSWORD) < 12:
                raise ValueError("Strong POSTGRES_PASSWORD required in production (minimum 12 characters)")
            if not self.DATABASE_URL.startswith("postgresql://"):
                raise ValueError("PostgreSQL required in production environment")
        return self
    
    @model_validator(mode='after')
    def validate_cors_config(self):
        """Валидация CORS конфигурации"""
        if self.ENVIRONMENT == "production":
            origins = self.get_cors_origins()
            for origin in origins:
                if not origin.startswith("https://"):
                    raise ValueError("Only HTTPS origins allowed in production")
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()