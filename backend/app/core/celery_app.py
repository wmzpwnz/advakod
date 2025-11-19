from celery import Celery
import os
from kombu import Queue

# Настройки Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Создание экземпляра Celery
celery_app = Celery(
    "ai_lawyer",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.ai_tasks", 
        "app.tasks.file_tasks",
        "app.tasks.analytics_tasks"
    ]
)

# Конфигурация Celery
celery_app.conf.update(
    # Основные настройки
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    
    # Настройки очередей
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="default"),
        Queue("ai_processing", routing_key="ai_processing"),
        Queue("email", routing_key="email"),
        Queue("file_processing", routing_key="file_processing"),
        Queue("analytics", routing_key="analytics"),
        Queue("high_priority", routing_key="high_priority"),
    ),
    
    # Маршрутизация задач
    task_routes={
        "app.tasks.ai_tasks.*": {"queue": "ai_processing"},
        "app.tasks.email_tasks.*": {"queue": "email"},
        "app.tasks.file_tasks.*": {"queue": "file_processing"},
        "app.tasks.analytics_tasks.*": {"queue": "analytics"},
    },
    
    # Настройки выполнения
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # Настройки повторных попыток
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Настройки результатов
    result_expires=3600,  # 1 час
    result_persistent=True,
    
    # Настройки мониторинга
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Настройки безопасности
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Настройки для разных окружений
if os.getenv("ENVIRONMENT") == "production":
    celery_app.conf.update(
        # Продакшен настройки
        worker_max_tasks_per_child=1000,
        worker_max_memory_per_child=200000,  # 200MB
        task_compression="gzip",
        result_compression="gzip",
    )
elif os.getenv("ENVIRONMENT") == "development":
    celery_app.conf.update(
        # Настройки разработки
        task_always_eager=False,  # Для тестирования можно установить True
        task_eager_propagates=True,
    )

# Автоматическое обнаружение задач
celery_app.autodiscover_tasks()

# Настройки логирования
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def debug_task(self):
    """Отладочная задача"""
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Debug task request: {self.request!r}")
    return "Debug task completed"

# Мониторинг состояния Celery
@celery_app.task
def health_check():
    """Проверка здоровья Celery"""
    return {
        "status": "healthy",
        "broker": CELERY_BROKER_URL,
        "backend": CELERY_RESULT_BACKEND
    }

# Периодические задачи (Celery Beat)
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Очистка старых результатов каждые 6 часов
    "cleanup-old-results": {
        "task": "app.tasks.cleanup_tasks.cleanup_old_results",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    
    # Генерация аналитических отчетов каждый день в 2:00
    "daily-analytics": {
        "task": "app.tasks.analytics_tasks.generate_daily_report",
        "schedule": crontab(minute=0, hour=2),
    },
    
    # Очистка временных файлов каждый день в 3:00
    "cleanup-temp-files": {
        "task": "app.tasks.file_tasks.cleanup_temp_files",
        "schedule": crontab(minute=0, hour=3),
    },
    
    # Отправка уведомлений о подписках каждый день в 9:00
    "subscription-notifications": {
        "task": "app.tasks.email_tasks.send_subscription_reminders",
        "schedule": crontab(minute=0, hour=9),
    },
    
    # Обновление кэша AI моделей каждые 4 часа
    "update-ai-cache": {
        "task": "app.tasks.ai_tasks.update_model_cache",
        "schedule": crontab(minute=0, hour="*/4"),
    },
}

celery_app.conf.timezone = "Europe/Moscow"
