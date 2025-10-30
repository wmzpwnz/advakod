# ОПТя  ВАННЫЕ API роутеры - только необходимые для ИИ-Юриста
from fastapi import APIRouter
from .auth import router as auth_router
from .chat import router as chat_router
from .tokens import router as tokens_router
from .rag import router as rag_router  # RAG система
from .admin import router as admin_router  # Админ панель
from .admin_dashboard import router as admin_dashboard_router  # Расширенная админ панель
from .role_management import router as role_management_router  # Управление ролями и правами
from .monitoring import router as monitoring_router  # Мониторинг системы
from .llm_monitoring import router as llm_monitoring_router  # Мониторинг унифицированного LLM сервиса
# from .enhanced_rag import router as enhanced_rag_router  # Удален - неиспользуемый
from .canary_lora import router as canary_lora_router  # Canary-релизы и LoRA улучшения
from .smart_upload import router as smart_upload_router  # Интеллектуальная загрузка документов
from .feedback import router as feedback_router  # Обратная связь пользователей
from .moderation import router as moderation_router  # Модерация ответов ИИ
from .marketing import router as marketing_router  # Маркетинговые инструменты и A/B тестирование
from .project import router as project_router  # Система управления проектом
# from .backup import router as backup_router  # Система резервного копирования - temporarily disabled
# from .websocket import router as websocket_router  # Подключается отдельно в main.py

# from .notifications import router as notifications_router  # Система уведомлений
# from .encryption import router as encryption_router
# from .external import router as external_router
# from .webhook_management import router as webhook_management_router
# from .fine_tuning import router as fine_tuning_router
# from .rag import router as rag_router
# from .sentiment import router as sentiment_router
# from .categorization import router as categorization_router
# from .subscription import router as subscription_router
# from .payment import router as payment_router
# from .corporate import router as corporate_router
# from .referral import router as referral_router
# from .annotations import router as annotations_router
# from .document_diff import router as document_diff_router
# from .export import router as export_router
# from .user_profiles import router as user_profiles_router
# from .favorites import router as favorites_router
# from .analytics import router as analytics_router
# from .integrations import router as integrations_router
# from .metrics import router as metrics_router
# from .files import router as files_router
# from .two_factor import router as two_factor_router

api_router = APIRouter()

# Основные роутеры для ИИ-Юриста
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(tokens_router, prefix="/tokens", tags=["tokens"])
api_router.include_router(rag_router, prefix="/rag", tags=["rag"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_dashboard_router, prefix="/admin", tags=["admin-dashboard"])
# В router role_management уже задан абсолютный префикс "/admin/roles"
# Здесь НЕ добавляем дополнительный префикс, иначе получится "/api/v1/api/v1/admin/roles"
api_router.include_router(role_management_router, tags=["role-management"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(llm_monitoring_router, prefix="/llm", tags=["llm-monitoring"])
# api_router.include_router(enhanced_rag_router, tags=["enhanced-rag"])  # Удален - неиспользуемый
api_router.include_router(canary_lora_router, tags=["canary-lora"])
api_router.include_router(smart_upload_router, tags=["smart-upload"])
api_router.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
api_router.include_router(moderation_router, prefix="/moderation", tags=["moderation"])
api_router.include_router(marketing_router, prefix="/marketing", tags=["marketing"])
api_router.include_router(project_router, prefix="/project", tags=["project"])
# api_router.include_router(backup_router, prefix="/backup", tags=["backup"])  # Temporarily disabled

# api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
# api_router.include_router(encryption_router, prefix="/encryption", tags=["encryption"])
# api_router.include_router(external_router, prefix="/external", tags=["external"])
# api_router.include_router(webhook_management_router, prefix="/webhooks", tags=["webhooks"])
# api_router.include_router(fine_tuning_router, prefix="/ai", tags=["fine-tuning"])
# api_router.include_router(rag_router, prefix="/rag", tags=["rag"])
# api_router.include_router(sentiment_router, prefix="/sentiment", tags=["sentiment"])
# api_router.include_router(categorization_router, prefix="/categorization", tags=["categorization"])
# api_router.include_router(subscription_router, prefix="/subscription", tags=["subscription"])
# api_router.include_router(payment_router, prefix="/payment", tags=["payment"])
# api_router.include_router(corporate_router, prefix="/corporate", tags=["corporate"])
# api_router.include_router(referral_router, prefix="/referral", tags=["referral"])
# api_router.include_router(annotations_router, prefix="/annotations", tags=["annotations"])
# api_router.include_router(document_diff_router, prefix="/document-diff", tags=["document-diff"])
# api_router.include_router(export_router, prefix="/export", tags=["export"])
# api_router.include_router(user_profiles_router, prefix="/profile", tags=["user-profiles"])
# api_router.include_router(favorites_router, prefix="/favorites", tags=["favorites"])
# api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
# api_router.include_router(integrations_router, prefix="/integrations", tags=["integrations"])
# api_router.include_router(metrics_router, prefix="/metrics", tags=["metrics"])
# api_router.include_router(files_router, prefix="/files", tags=["files"])
# api_router.include_router(two_factor_router, prefix="/2fa", tags=["2fa"])
# api_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])  # Подключается отдельно в main.py
