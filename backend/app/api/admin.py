"""
API для админ панели
Управление пользователями, документами, аналитикой и системой
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import io
import os
import tempfile

from ..core.database import get_db
from ..models.user import User
from ..models.chat import ChatSession, ChatMessage
from ..models.audit_log import AuditLog, ActionType, SeverityLevel
from ..schemas.user import User as UserSchema, UserCreate
from ..schemas.admin import (
    UserUpdate, AdminDashboard, DocumentList, DocumentSearchResponse,
    AuditLogsResponse, UserAnalytics, FileUploadResponse
)
from ..services.auth_service import auth_service
from ..services.document_service import document_service
from ..services.vector_store_service import vector_store_service
from ..services.embeddings_service import embeddings_service
from ..services.rag_service import rag_service
from ..services.smart_document_processor import smart_document_processor
from ..services.audit_service import get_audit_service
from ..services.ai_document_validator import ai_document_validator
from ..services.document_versioning import document_versioning_service
from ..core.admin_security import get_secure_admin, require_admin_action_validation

logger = logging.getLogger(__name__)

router = APIRouter()

def get_current_admin(current_user: User = Depends(auth_service.get_current_active_user)):
    """Проверка прав администратора"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ==================== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ====================

@router.get("/users", response_model=List[UserSchema])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_premium: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить список пользователей с фильтрацией"""
    try:
        query = db.query(User)
        
        # Фильтрация
        if search:
            query = query.filter(
                (User.username.contains(search)) |
                (User.email.contains(search)) |
                (User.full_name.contains(search))
            )
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if is_premium is not None:
            query = query.filter(User.is_premium == is_premium)
            
        if is_admin is not None:
            query = query.filter(User.is_admin == is_admin)
        
        users = query.offset(skip).limit(limit).all()
        return users
        
    except Exception as e:
        logger.error(f"Ошибка получения пользователей: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить пользователя по ID"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/users/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Обновить пользователя"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Обновляем поля
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # Логируем действие
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.ADMIN_ACTION,
            resource="user",
            resource_id=str(user_id),
            description=f"Updated user {user.username}",
            details={"updated_fields": list(update_data.keys())}
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
@require_admin_action_validation("delete_user", "user")
async def delete_user(
    user_id: int,
    request: Request,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Удалить пользователя (мягкое удаление)"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Мягкое удаление - деактивируем пользователя
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.commit()
        
        # Логируем действие
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.ADMIN_ACTION,
            resource="user",
            resource_id=str(user_id),
            description=f"Deactivated user {user.username}",
            severity=SeverityLevel.HIGH
        )
        
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{user_id}/toggle-admin")
@require_admin_action_validation("toggle_admin_status", "user")
async def toggle_admin_status(
    user_id: int,
    request: Request,
    current_admin: User = Depends(get_secure_admin),
    db: Session = Depends(get_db)
):
    """Переключить статус администратора"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Нельзя убрать права админа у самого себя
        if user_id == current_admin.id:
            raise HTTPException(status_code=400, detail="Cannot change your own admin status")
        
        user.is_admin = not user.is_admin
        user.updated_at = datetime.utcnow()
        db.commit()
        
        # Логируем действие
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.ADMIN_ACTION,
            resource="user",
            resource_id=str(user_id),
            description=f"Toggled admin status for {user.username} to {user.is_admin}",
            severity=SeverityLevel.HIGH
        )
        
        return {
            "message": f"Admin status {'granted' if user.is_admin else 'revoked'}",
            "is_admin": user.is_admin
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка изменения статуса админа для пользователя {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== АНАЛИТИКА И СТАТИСТИКА ====================

@router.get("/dashboard", response_model=AdminDashboard)
async def get_admin_dashboard(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить дашборд администратора"""
    try:
        # Общая статистика пользователей
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        premium_users = db.query(User).filter(User.is_premium == True).count()
        admin_users = db.query(User).filter(User.is_admin == True).count()
        
        # Статистика за последние 30 дней
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users_30d = db.query(User).filter(User.created_at >= thirty_days_ago).count()
        
        # Статистика чатов
        total_sessions = db.query(ChatSession).count()
        total_messages = db.query(ChatMessage).count()
        
        # Статистика RAG системы
        rag_status = rag_service.get_status()
        vector_store_status = vector_store_service.get_status()
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "premium": premium_users,
                "admins": admin_users,
                "new_last_30d": new_users_30d
            },
            "chats": {
                "total_sessions": total_sessions,
                "total_messages": total_messages
            },
            "system": {
                "rag_status": rag_status,
                "vector_store_status": vector_store_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения дашборда: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/users")
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить аналитику пользователей"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Регистрации по дням
        daily_registrations = db.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        ).filter(
            User.created_at >= start_date
        ).group_by(
            func.date(User.created_at)
        ).all()
        
        # Активность по типам подписки
        subscription_stats = db.query(
            User.subscription_type,
            func.count(User.id).label('count')
        ).group_by(User.subscription_type).all()
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "daily_registrations": [
                {"date": str(reg.date), "count": reg.count}
                for reg in daily_registrations
            ],
            "subscription_distribution": [
                {"type": stat.subscription_type, "count": stat.count}
                for stat in subscription_stats
            ]
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения аналитики пользователей: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== УПРАВЛЕНИЕ ДОКУМЕНТАМИ ====================

@router.get("/documents")
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    document_type: Optional[str] = Query(None, description="Фильтр по типу документа (codex, federal_law, supreme_court_resolution, resolution, decree, order, other)"),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить список документов в RAG системе"""
    try:
        # Автоматическая инициализация, если не готова
        if not vector_store_service.is_ready():
            logger.warning("Vector store not ready, attempting initialization...")
            try:
                vector_store_service.initialize()
                if not vector_store_service.is_ready():
                    logger.error("Failed to initialize vector store service")
                    return {"documents": [], "total": 0, "message": "Vector store not ready"}
            except Exception as init_error:
                logger.error(f"Error initializing vector store: {init_error}")
                return {"documents": [], "total": 0, "message": f"Vector store initialization failed: {str(init_error)}"}
        
        # Получаем информацию о коллекции
        collection = vector_store_service.collection
        if collection is None:
            logger.error("Collection is None after initialization")
            return {"documents": [], "total": 0, "message": "Collection not found"}
        
        try:
            total_docs = collection.count()
        except Exception as count_error:
            logger.error(f"Error getting collection count: {count_error}")
            return {"documents": [], "total": 0, "message": f"Error accessing collection: {str(count_error)}"}
        
        # Если документов нет, возвращаем пустой список
        if total_docs == 0:
            return {
                "documents": [],
                "total": 0,
                "skip": skip,
                "limit": limit
            }
        
        # Получаем ВСЕ документы с метаданными для группировки
        try:
            results = collection.get(
                limit=total_docs,  # Получаем все документы
                include=['metadatas', 'documents']
            )
        except Exception as get_error:
            logger.error(f"Error getting documents from collection: {get_error}")
            return {"documents": [], "total": 0, "message": f"Error retrieving documents: {str(get_error)}"}
        
        # Проверяем структуру результатов
        if not results or 'documents' not in results or 'metadatas' not in results:
            logger.warning("Invalid results structure from collection")
            return {"documents": [], "total": 0, "message": "Invalid collection data structure"}
        
        if not results['documents'] or len(results['documents']) == 0:
            return {
                "documents": [],
                "total": 0,
                "skip": skip,
                "limit": limit
            }
        
        # Группируем чанки по document_id для получения уникальных документов
        documents_by_id = {}
        try:
            ids = results.get('ids', [])
            documents_list = results.get('documents', [])
            metadatas_list = results.get('metadatas', [])
            
            for i in range(len(documents_list)):
                doc = documents_list[i] if i < len(documents_list) else ""
                meta = metadatas_list[i] if i < len(metadatas_list) else {}
                doc_id = meta.get('document_id', ids[i] if i < len(ids) else str(i))
                
                # Пропускаем заглушки и очень маленькие документы
                # (документы размером < 1000 байт считаются заглушками)
                doc_size = len(doc) if doc else 0
                if doc_size < 1000:  # Фильтруем все документы меньше 1 KB
                    continue
                
                if doc_id not in documents_by_id:
                    # Создаем новый документ
                    doc_size = len(doc) if doc else 0
                    documents_by_id[doc_id] = {
                        "id": doc_id,
                        "content": doc,
                        "metadata": meta,
                        "length": doc_size,  # Будет обновлено на total_length при добавлении чанков
                        "chunks_count": 1,
                        "total_length": doc_size
                    }
                else:
                    # Обновляем существующий документ
                    existing = documents_by_id[doc_id]
                    existing["chunks_count"] += 1
                    existing["total_length"] += len(doc) if doc else 0
                    # Обновляем контент на более длинный чанк
                    if doc and len(doc) > len(existing.get("content", "")):
                        existing["content"] = doc
                    # Всегда обновляем length на total_length для отображения общего размера документа
                    existing["length"] = existing["total_length"]
        except Exception as grouping_error:
            logger.error(f"Error grouping documents: {grouping_error}")
            return {"documents": [], "total": 0, "message": f"Error processing documents: {str(grouping_error)}"}
        
        # Преобразуем в список и обновляем length для всех документов
        documents = list(documents_by_id.values())
        for doc in documents:
            # Убеждаемся, что length = total_length для корректного отображения в UI
            doc["length"] = doc.get("total_length", doc.get("length", 0))
            # Добавляем file_name на верхний уровень для удобства фронтенда
            meta = doc.get("metadata", {})
            if "file_name" not in doc:
                doc["file_name"] = meta.get("file_name") or meta.get("filename", "Без имени файла")
            # Добавляем document_type на верхний уровень
            if "document_type" not in doc:
                doc["document_type"] = meta.get("document_type", "other")
        
        # Фильтруем документы по общему размеру (сумма всех чанков)
        # Документы с общим размером < 5 KB считаются заглушками
        documents = [doc for doc in documents if doc.get('total_length', 0) >= 5120]
        
        documents.sort(key=lambda x: x['metadata'].get('added_at', ''), reverse=True)
        
        # Фильтруем по типу документа, если указан
        if document_type:
            documents = [doc for doc in documents if doc['metadata'].get('document_type') == document_type]
        
        # Удаляем дубликаты по source_url для URL документов
        seen_urls = set()
        unique_documents = []
        for doc in documents:
            if doc['metadata'].get('source_type') == 'url':
                source_url = doc['metadata'].get('source_url', '')
                if source_url and source_url not in seen_urls:
                    seen_urls.add(source_url)
                    unique_documents.append(doc)
            else:
                unique_documents.append(doc)
        
        documents = unique_documents
        
        # Применяем пагинацию
        total_unique_docs = len(documents)
        documents = documents[skip:skip + limit]
        
        # Логирование для отладки
        logger.info(f"API /documents: возвращаем {len(documents)} документов из {total_unique_docs} уникальных")
        if len(documents) > 0:
            first_doc = documents[0]
            file_name = first_doc.get('file_name') or first_doc.get('metadata', {}).get('file_name', 'unknown')
            logger.info(f"Первый документ: {file_name}")
        else:
            logger.warning(f"API /documents: документы не найдены после группировки. documents_by_id содержит {len(documents_by_id)} записей")
        
        # Улучшаем структуру ответа для фронтенда
        # Добавляем информацию о типах документов для группировки
        documents_by_type = {}
        for doc in documents:
            doc_type = doc['metadata'].get('document_type', 'other')
            if doc_type not in documents_by_type:
                documents_by_type[doc_type] = []
            documents_by_type[doc_type].append(doc)
        
        return {
            "documents": documents,
            "total": total_unique_docs,
            "skip": skip,
            "limit": limit,
            "document_type": document_type,  # Возвращаем примененный фильтр
            "documents_by_type": documents_by_type,  # Группировка по типам для удобства
            "available_types": list(documents_by_type.keys())  # Доступные типы документов
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения документов: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

# Маппинг типов документов на русские названия
DOCUMENT_TYPE_NAMES = {
    "codex": "Кодексы",
    "federal_law": "Федеральные законы",
    "supreme_court_resolution": "Постановления Верховного Суда",
    "resolution": "Постановления",
    "decree": "Указы",
    "order": "Приказы",
    "other": "Другие документы"
}

@router.get("/documents/types")
async def get_document_types(
    current_admin: User = Depends(get_current_admin)
):
    """Получить список доступных типов документов с русскими названиями"""
    return {
        "types": [
            {
                "id": doc_type,
                "name": DOCUMENT_TYPE_NAMES.get(doc_type, doc_type),
                "icon": get_document_type_icon(doc_type)
            }
            for doc_type in DOCUMENT_TYPE_NAMES.keys()
        ]
    }

def get_document_type_icon(doc_type: str) -> str:
    """Возвращает иконку для типа документа"""
    icons = {
        "codex": "📚",
        "federal_law": "📜",
        "supreme_court_resolution": "⚖️",
        "resolution": "📋",
        "decree": "📝",
        "order": "📄",
        "other": "📑"
    }
    return icons.get(doc_type, "📄")

@router.get("/documents/stats")
async def get_documents_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить статистику по типам документов"""
    try:
        if not vector_store_service.is_ready():
            vector_store_service.initialize()
            if not vector_store_service.is_ready():
                return {"stats": {}, "message": "Vector store not ready"}
        
        collection = vector_store_service.collection
        if collection is None:
            return {"stats": {}, "message": "Collection not found"}
        
        try:
            total_docs = collection.count()
            if total_docs == 0:
                return {"stats": {}, "total": 0}
            
            # Получаем все документы с метаданными
            results = collection.get(
                limit=total_docs,
                include=['metadatas']
            )
            
            # Подсчитываем по типам
            stats = {}
            documents_by_type = {}
            
            metadatas_list = results.get('metadatas', [])
            for meta in metadatas_list:
                doc_type = meta.get('document_type', 'other')
                doc_id = meta.get('document_id', 'unknown')
                
                if doc_type not in stats:
                    stats[doc_type] = 0
                    documents_by_type[doc_type] = set()
                
                # Считаем уникальные документы по document_id
                if doc_id not in documents_by_type[doc_type]:
                    documents_by_type[doc_type].add(doc_id)
                    stats[doc_type] += 1
            
            # Преобразуем в список для удобства с русскими названиями
            stats_list = [
                {
                    "type": doc_type,
                    "count": count,
                    "name": DOCUMENT_TYPE_NAMES.get(doc_type, doc_type),
                    "icon": get_document_type_icon(doc_type)
                }
                for doc_type, count in sorted(stats.items())
            ]
            
            return {
                "stats": stats,
                "stats_list": stats_list,
                "total": total_docs,
                "total_unique_documents": sum(stats.values()),
                "type_names": DOCUMENT_TYPE_NAMES  # Маппинг для фронтенда
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {"stats": {}, "message": f"Error: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Ошибка получения статистики документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/by-type/{document_type}")
async def get_documents_by_type(
    document_type: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить документы определенного типа с группировкой"""
    try:
        if not vector_store_service.is_ready():
            vector_store_service.initialize()
            if not vector_store_service.is_ready():
                return {"documents": [], "total": 0, "message": "Vector store not ready"}
        
        collection = vector_store_service.collection
        if collection is None:
            return {"documents": [], "total": 0, "message": "Collection not found"}
        
        # Получаем все документы нужного типа
        total_docs = collection.count()
        if total_docs == 0:
            return {"documents": [], "total": 0, "skip": skip, "limit": limit}
        
        results = collection.get(limit=total_docs, include=['metadatas', 'documents'])
        
        # Группируем по document_id
        documents_by_id = {}
        ids = results.get('ids', [])
        documents_list = results.get('documents', [])
        metadatas_list = results.get('metadatas', [])
        
        for i in range(len(documents_list)):
            doc = documents_list[i] if i < len(documents_list) else ""
            meta = metadatas_list[i] if i < len(metadatas_list) else {}
            
            # Фильтруем по типу
            if meta.get('document_type') != document_type:
                continue
            
            # Пропускаем маленькие документы (< 1000 байт)
            doc_size = len(doc) if doc else 0
            if doc_size < 1000:
                continue
            
            doc_id = meta.get('document_id', ids[i] if i < len(ids) else str(i))
            
            if doc_id not in documents_by_id:
                documents_by_id[doc_id] = {
                    "id": doc_id,
                    "content": doc,
                    "metadata": meta,
                    "length": len(doc) if doc else 0,
                    "chunks_count": 1,
                    "total_length": len(doc) if doc else 0,
                    "file_name": meta.get('file_name', meta.get('filename', 'unknown')),
                    "document_type": meta.get('document_type', 'other')
                }
            else:
                existing = documents_by_id[doc_id]
                existing["chunks_count"] += 1
                existing["total_length"] += len(doc) if doc else 0
                if doc and len(doc) > len(existing.get("content", "")):
                    existing["content"] = doc
                    existing["length"] = len(doc)
        
        # Преобразуем в список и фильтруем по общему размеру
        documents = list(documents_by_id.values())
        
        # Фильтруем документы по общему размеру (сумма всех чанков)
        # Документы с общим размером < 5 KB считаются заглушками
        documents = [doc for doc in documents if doc.get('total_length', 0) >= 5120]
        
        # Добавляем file_name и document_type на верхний уровень для удобства фронтенда
        for doc in documents:
            meta = doc.get("metadata", {})
            if "file_name" not in doc:
                doc["file_name"] = meta.get("file_name") or meta.get("filename", "Без имени файла")
            if "document_type" not in doc:
                doc["document_type"] = meta.get("document_type", "other")
        
        documents.sort(key=lambda x: x['metadata'].get('added_at', ''), reverse=True)
        
        # Применяем пагинацию
        total_unique_docs = len(documents)
        documents = documents[skip:skip + limit]
        
        return {
            "documents": documents,
            "total": total_unique_docs,
            "skip": skip,
            "limit": limit,
            "document_type": document_type
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения документов по типу: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")

@router.get("/documents/{document_id}/structure")
async def get_document_structure(
    document_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить структуру документа (разделы, статьи для кодексов)"""
    try:
        if not vector_store_service.is_ready():
            vector_store_service.initialize()
            if not vector_store_service.is_ready():
                return {"structure": [], "message": "Vector store not ready"}
        
        collection = vector_store_service.collection
        if collection is None:
            return {"structure": [], "message": "Collection not found"}
        
        # Получаем все чанки этого документа
        total_docs = collection.count()
        results = collection.get(limit=total_docs, include=['metadatas', 'documents', 'ids'])
        
        metadatas = results.get('metadatas', [])
        documents = results.get('documents', [])
        ids = results.get('ids', [])
        
        # Фильтруем по document_id
        document_chunks = []
        for i, (meta, doc, chunk_id) in enumerate(zip(metadatas, documents, ids)):
            if meta.get('document_id') == document_id:
                document_chunks.append({
                    'chunk_id': chunk_id,
                    'content': doc,
                    'metadata': meta,
                    'chunk_index': meta.get('chunk_index', i),
                    'part': meta.get('part', ''),
                    'article': meta.get('article', ''),
                    'item': meta.get('item', ''),
                })
        
        # Сортируем по chunk_index
        document_chunks.sort(key=lambda x: x['chunk_index'])
        
        # Группируем по разделам/статьям для кодексов
        structure = []
        current_section = None
        current_article = None
        
        for chunk in document_chunks:
            meta = chunk['metadata']
            part = meta.get('part', '')
            article = meta.get('article', '')
            
            # Если есть part - это раздел
            if part and part != current_section:
                current_section = part
                structure.append({
                    'type': 'section',
                    'name': part,
                    'chunks': []
                })
            
            # Если есть article - это статья
            if article:
                # Ищем раздел для этой статьи
                section = None
                for s in structure:
                    if s['type'] == 'section' and s['name'] == part:
                        section = s
                        break
                
                if not section and part:
                    section = {'type': 'section', 'name': part, 'chunks': []}
                    structure.append(section)
                
                # Добавляем статью
                article_name = f"Статья {article}" if article else "Без номера"
                if not section or article_name not in [a['name'] for a in section.get('articles', [])]:
                    if section:
                        if 'articles' not in section:
                            section['articles'] = []
                        section['articles'].append({
                            'name': article_name,
                            'article': article,
                            'chunks': []
                        })
            
            # Добавляем чанк в структуру
            if structure:
                if article and structure[-1].get('articles'):
                    structure[-1]['articles'][-1]['chunks'].append(chunk)
                else:
                    if 'chunks' not in structure[-1]:
                        structure[-1]['chunks'] = []
                    structure[-1]['chunks'].append(chunk)
            else:
                structure.append({
                    'type': 'content',
                    'chunks': [chunk]
                })
        
        return {
            "document_id": document_id,
            "structure": structure,
            "total_chunks": len(document_chunks)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения структуры документа: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving document structure: {str(e)}")

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Загрузить документ в RAG систему"""
    try:
        # Сохраняем файл временно
        
        # Безопасное имя файла
        safe_filename = os.path.basename(file.filename) if file.filename else "unknown"
        safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ".-_")[:50]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{safe_filename}") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Определяем тип файла и читаем содержимое
            file_extension = os.path.splitext(file.filename)[1].lower() if file.filename else ''
            
            if file_extension == '.docx':
                # Для DOCX файлов используем специальную обработку
                import docx
                try:
                    doc = docx.Document(tmp_file_path)
                    content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                except Exception as e:
                    logger.error(f"Ошибка чтения DOCX файла: {e}")
                    # Fallback: читаем как бинарный файл
                    with open(tmp_file_path, 'rb') as f:
                        content = f.read().decode('utf-8', errors='ignore')
            elif file_extension == '.pdf':
                # Для PDF файлов
                try:
                    import PyPDF2
                    with open(tmp_file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        content = '\n'.join([page.extract_text() for page in reader.pages])
                except Exception as e:
                    logger.error(f"Ошибка чтения PDF файла: {e}")
                    content = "Ошибка извлечения текста из PDF"
            else:
                # Для текстовых файлов
                with open(tmp_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            # Используем новую интеллектуальную систему обработки
            result = await smart_document_processor.process_document(
                file_path=file.filename,
                content=content
            )
            
            if result.get('success'):
                # Логируем действие
                audit_service = get_audit_service(db)
                audit_service.log_action(
                    user_id=current_admin.id,
                    action=ActionType.ADMIN_ACTION,
                    resource="document",
                    resource_id=file.filename,
                    description=f"Uploaded document with smart processing: {file.filename}",
                    details={
                        "chunks_created": result.get('chunks_count', 0),
                        "articles_found": result.get('articles_count', 0),
                        "document_type": result.get('metadata', {}).get('document_type', 'unknown'),
                        "structure_score": result.get('metadata', {}).get('structure_score', 0)
                    }
                )
                
                return {
                    "success": True,
                    "message": "Document uploaded and analyzed successfully",
                    "details": result,
                    "chunks_created": result.get('chunks_count', 0),
                    "articles_found": result.get('articles_count', 0),
                    "sections_found": result.get('sections_count', 0),
                    "document_type": result.get('metadata', {}).get('document_type', 'unknown'),
                    "structure_score": result.get('metadata', {}).get('structure_score', 0),
                    "processing_time": result.get('processing_time', 0),
                    "filename": file.filename
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to process document with smart analysis",
                    "error": result.get('error', 'Unknown error')
                }
                
        finally:
            # Удаляем временный файл
            os.unlink(tmp_file_path)
        
    except Exception as e:
        logger.error(f"Ошибка загрузки документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/upload-url")
async def upload_document_from_url(
    request: dict,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Загрузить документ по URL"""
    try:
        url = request.get('url')
        if not url:
            raise HTTPException(status_code=400, detail="URL не указан")
            
        logger.info(f"Загрузка документа по URL: {url}")
        
        # Валидация URL
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="Некорректный URL")
        
        # Загружаем документ по URL
        result = await document_service.process_url(url)
        
        if result.get('success'):
            # Логируем действие администратора
            audit_service = get_audit_service(db)
            audit_service.log_action(
                user_id=current_admin.id,
                action=ActionType.ADMIN_ACTION,
                resource="document",
                resource_id=result.get('document_id', 'unknown'),
                description=f"Uploaded document from URL: {url}",
                details={"chunks_added": result.get('chunks_added', 0)}
            )
            
            return {
                "success": True,
                "message": "Document uploaded successfully from URL",
                "details": result,
                "chunks_added": result.get('chunks_added', 0),
                "document_type": result.get('document_type', 'unknown'),
                "validation_confidence": result.get('validation_confidence', 0),
                "legal_score": result.get('legal_score', 0),
                "text_length": result.get('text_length', 0),
                "file_hash": result.get('file_hash', ''),
                "document_id": result.get('document_id', ''),
                "source_url": url
            }
        else:
            return {
                "success": False,
                "message": "Failed to upload document from URL",
                "error": result.get('error')
            }
            
    except Exception as e:
        logger.error(f"Ошибка загрузки документа по URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validation/status")
async def get_validation_status(
    current_admin: User = Depends(get_current_admin)
):
    """Получить статус валидации документов"""
    try:
        status = document_service.get_status()
        return {
            "success": True,
            "validation_method": status.get("validation_method", "unknown"),
            "available_methods": ["hybrid", "ai", "rules"],
            "hybrid_stats": status.get("hybrid_stats", {}),
            "ai_validator_stats": ai_document_validator.get_validation_stats()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса валидации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validation/method")
async def set_validation_method(
    method: str = Query(..., description="Метод валидации: hybrid, ai, rules, none"),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Переключить метод валидации документов"""
    try:
        document_service.set_validation_method(method)
        
        # Логируем действие
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.ADMIN_ACTION,
            resource="validation_method",
            resource_id="system",
            description=f"Changed validation method to: {method}",
            details={"validation_method": method}
        )
        
        method_names = {
            "hybrid": "Гибридный (правила + AI)",
            "ai": "AI (Vistral-24B)",
            "rules": "Правила (быстрый)"
        }
        
        return {
            "success": True,
            "message": f"Метод валидации изменен на: {method_names.get(method, method)}",
            "validation_method": method
        }
    except Exception as e:
        logger.error(f"Ошибка изменения метода валидации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validation/clear-cache")
async def clear_validation_cache(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Очистить кэш валидации"""
    try:
        from ..services.hybrid_document_validator import hybrid_document_validator
        hybrid_document_validator.clear_cache()
        
        # Логируем действие
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.ADMIN_ACTION,
            resource="validation_cache",
            resource_id="system",
            description="Cleared validation cache",
            details={}
        )
        
        return {
            "success": True,
            "message": "Кэш валидации очищен"
        }
    except Exception as e:
        logger.error(f"Ошибка очистки кэша валидации: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/versions")
async def get_document_versions(
    document_id: Optional[str] = Query(None, description="ID документа для получения версий"),
    current_admin: User = Depends(get_current_admin)
):
    """Получить версии документов"""
    try:
        if document_id:
            # Получить версии конкретного документа
            versions = document_versioning_service.get_all_versions(document_id)
            current_version = document_versioning_service.get_current_version(document_id)
            
            return {
                "success": True,
                "document_id": document_id,
                "current_version": current_version.__dict__ if current_version else None,
                "all_versions": [v.__dict__ for v in versions]
            }
        else:
            # Получить статистику всех документов
            stats = document_versioning_service.get_version_statistics()
            return {
                "success": True,
                "statistics": stats
            }
    except Exception as e:
        logger.error(f"Ошибка получения версий документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/current-versions")
async def get_current_versions(
    current_admin: User = Depends(get_current_admin)
):
    """Получить только текущие версии документов"""
    try:
        # Получить все документы с их текущими версиями
        all_documents = {}
        for document_id in document_versioning_service.versions.keys():
            current_version = document_versioning_service.get_current_version(document_id)
            if current_version:
                all_documents[document_id] = current_version.__dict__
        
        return {
            "success": True,
            "current_versions": all_documents
        }
    except Exception as e:
        logger.error(f"Ошибка получения текущих версий: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/{document_id}/archive")
async def archive_document(
    document_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Архивировать документ (пометить как устаревший)"""
    try:
        # Получить все версии документа
        versions = document_versioning_service.get_all_versions(document_id)
        if not versions:
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Пометить все версии как архивированные
        for version in versions:
            version.status = "archived"
        
        # Логируем действие
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.ADMIN_ACTION,
            resource="document",
            resource_id=document_id,
            description=f"Archived document {document_id}",
            details={"versions_archived": len(versions)}
        )
        
        return {
            "success": True,
            "message": f"Документ {document_id} архивирован",
            "archived_versions": len(versions)
        }
    except Exception as e:
        logger.error(f"Ошибка архивирования документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Удалить документ из RAG системы (синхронизированно с simple_expert_rag)"""
    try:
        if not vector_store_service.is_ready():
            raise HTTPException(status_code=503, detail="Vector store not ready")
        
        # Импортируем simple_expert_rag
        from ..services.simple_expert_rag import simple_expert_rag
        
        # 1. Удаляем из ChromaDB
        collection = vector_store_service.collection
        all_results = collection.get(include=['metadatas'])
        
        # Фильтруем чанки по document_id или по chunk_id
        matching_ids = []
        for i, metadata in enumerate(all_results['metadatas']):
            if metadata and (metadata.get('document_id') == document_id or all_results['ids'][i] == document_id):
                matching_ids.append(all_results['ids'][i])
        
        chromadb_chunks_deleted = 0
        if matching_ids:
            # Удаляем все чанки документа из ChromaDB
            collection.delete(ids=matching_ids)
            chromadb_chunks_deleted = len(matching_ids)
            logger.info(f"🗑️ Удалено из ChromaDB: {chromadb_chunks_deleted} чанков")
        
        # 2. Удаляем из simple_expert_rag
        # Пробуем удалить по document_id и по всем возможным именам файлов
        simple_rag_result = await simple_expert_rag.delete_document(document_id)
        simple_rag_chunks_deleted = simple_rag_result.get('chunks_deleted', 0)
        
        # Если не найден по document_id, пробуем найти по именам файлов в ChromaDB
        if simple_rag_chunks_deleted == 0 and matching_ids:
            # Получаем метаданные для поиска имени файла
            for chunk_id in matching_ids:
                try:
                    chunk_results = collection.get(ids=[chunk_id], include=['metadatas'])
                    if chunk_results['metadatas'] and len(chunk_results['metadatas']) > 0:
                        chunk_metadata = chunk_results['metadatas'][0]
                        if chunk_metadata and 'filename' in chunk_metadata:
                            filename = chunk_metadata['filename']
                            # Пробуем удалить по имени файла
                            filename_result = await simple_expert_rag.delete_document(filename)
                            if filename_result.get('success', False):
                                simple_rag_chunks_deleted += filename_result.get('chunks_deleted', 0)
                                simple_rag_result = filename_result
                                break
                except Exception as e:
                    logger.warning(f"Ошибка получения метаданных для {chunk_id}: {e}")
                    continue
        
        if not simple_rag_result.get('success', False):
            logger.warning(f"⚠️ Ошибка удаления из simple_expert_rag: {simple_rag_result.get('error', 'Unknown error')}")
        
        # 3. Проверяем, был ли документ найден хотя бы в одной системе
        if chromadb_chunks_deleted == 0 and simple_rag_chunks_deleted == 0:
            logger.warning(f"⚠️ Документ {document_id} не найден ни в ChromaDB, ни в simple_expert_rag")
            raise HTTPException(
                status_code=404, 
                detail=f"Документ с ID '{document_id}' не найден в системе. Возможно, он уже был удален или никогда не существовал."
            )
        
        # 4. Логируем действие
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.ADMIN_ACTION,
            resource="document",
            resource_id=document_id,
            description=f"Deleted document from RAG systems (ChromaDB: {chromadb_chunks_deleted}, Simple RAG: {simple_rag_chunks_deleted} chunks)",
            severity=SeverityLevel.MEDIUM,
            details={
                "chromadb_chunks_deleted": chromadb_chunks_deleted,
                "simple_rag_chunks_deleted": simple_rag_chunks_deleted,
                "simple_rag_success": simple_rag_result.get('success', False)
            }
        )
        
        return {
            "message": "Document deleted successfully from all RAG systems",
            "chromadb_chunks_deleted": chromadb_chunks_deleted,
            "simple_rag_chunks_deleted": simple_rag_chunks_deleted,
            "total_chunks_deleted": chromadb_chunks_deleted + simple_rag_chunks_deleted,
            "simple_rag_status": simple_rag_result.get('status', 'unknown')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления документа {document_id}: {e}")
        logger.error(f"Тип ошибки: {type(e)}")
        logger.error(f"Детали ошибки: {e.__dict__ if hasattr(e, '__dict__') else 'Нет деталей'}")
        raise HTTPException(status_code=500, detail=f"Ошибка удаления: {str(e)}")

@router.post("/documents/clear-all")
async def clear_all_documents(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Удалить все документы из RAG системы (синхронизированно с simple_expert_rag)"""
    try:
        if not vector_store_service.is_ready():
            raise HTTPException(status_code=503, detail="Vector store not ready")
        
        # Импортируем simple_expert_rag
        from ..services.simple_expert_rag import simple_expert_rag
        
        # 1. Очищаем ChromaDB
        collection = vector_store_service.collection
        all_results = collection.get(include=['metadatas'])
        
        chromadb_chunks_deleted = len(all_results['ids'])
        if chromadb_chunks_deleted > 0:
            # Удаляем все чанки из ChromaDB
            collection.delete(ids=all_results['ids'])
            logger.info(f"🗑️ Очищено ChromaDB: {chromadb_chunks_deleted} чанков")
        
        # 2. Очищаем simple_expert_rag
        simple_rag_result = await simple_expert_rag.clear_all_documents()
        simple_rag_documents_deleted = simple_rag_result.get('documents_deleted', 0)
        simple_rag_chunks_deleted = simple_rag_result.get('chunks_deleted', 0)
        
        if not simple_rag_result.get('success', False):
            logger.warning(f"⚠️ Ошибка очистки simple_expert_rag: {simple_rag_result.get('error', 'Unknown error')}")
        
        # 3. Проверяем, были ли документы хотя бы в одной системе
        if chromadb_chunks_deleted == 0 and simple_rag_chunks_deleted == 0:
            return {
                "message": "No documents to delete in any system",
                "chromadb_chunks_deleted": 0,
                "simple_rag_documents_deleted": 0,
                "simple_rag_chunks_deleted": 0,
                "total_chunks_deleted": 0
            }
        
        # 4. Логируем действие
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.ADMIN_ACTION,
            resource="documents",
            resource_id="all",
            description=f"Cleared all documents from RAG systems (ChromaDB: {chromadb_chunks_deleted}, Simple RAG: {simple_rag_documents_deleted} docs, {simple_rag_chunks_deleted} chunks)",
            severity=SeverityLevel.HIGH,
            details={
                "chromadb_chunks_deleted": chromadb_chunks_deleted,
                "simple_rag_documents_deleted": simple_rag_documents_deleted,
                "simple_rag_chunks_deleted": simple_rag_chunks_deleted,
                "simple_rag_success": simple_rag_result.get('success', False)
            }
        )
        
        return {
            "message": "All documents deleted successfully from all RAG systems",
            "chromadb_chunks_deleted": chromadb_chunks_deleted,
            "simple_rag_documents_deleted": simple_rag_documents_deleted,
            "simple_rag_chunks_deleted": simple_rag_chunks_deleted,
            "total_chunks_deleted": chromadb_chunks_deleted + simple_rag_chunks_deleted,
            "simple_rag_status": simple_rag_result.get('status', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Ошибка очистки всех документов: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка очистки: {str(e)}")

@router.get("/documents/search")
async def search_documents(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Поиск документов в RAG системе"""
    try:
        if not vector_store_service.is_ready():
            raise HTTPException(status_code=503, detail="Vector store not ready")
        
        collection = vector_store_service.collection
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            include=['documents', 'metadatas', 'distances']
        )
        
        documents = []
        for i, (doc, meta, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            documents.append({
                "id": results['ids'][0][i],
                "content": doc,
                "metadata": meta,
                "similarity": 1 - distance,
                "distance": distance
            })
        
        return {
            "query": query,
            "documents": documents,
            "total_found": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Ошибка поиска документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ЛОГИ И АУДИТ ====================

@router.get("/logs/audit")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: Optional[ActionType] = None,
    severity: Optional[SeverityLevel] = None,
    user_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить логи аудита"""
    try:
        query = db.query(AuditLog)
        
        # Фильтрация по времени
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(AuditLog.created_at >= start_date)
        
        # Дополнительные фильтры
        if action:
            query = query.filter(AuditLog.action == action)
        if severity:
            query = query.filter(AuditLog.severity == severity)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        # Сортировка по времени (новые сначала)
        query = query.order_by(AuditLog.created_at.desc())
        
        logs = query.offset(skip).limit(limit).all()
        
        return {
            "logs": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource": log.resource,
                    "resource_id": log.resource_id,
                    "description": log.description,
                    "severity": log.severity,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat(),
                    "details": log.details
                }
                for log in logs
            ],
            "total": query.count(),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения логов аудита: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/export")
async def export_audit_logs(
    format: str = Query("json", pattern="^(json|csv)$"),
    days: int = Query(30, ge=1, le=365),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Экспорт логов аудита"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        logs = db.query(AuditLog).filter(
            AuditLog.created_at >= start_date
        ).order_by(AuditLog.created_at.desc()).all()
        
        if format == "json":
            data = [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource": log.resource,
                    "resource_id": log.resource_id,
                    "description": log.description,
                    "severity": log.severity,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat(),
                    "details": log.details
                }
                for log in logs
            ]
            
            return StreamingResponse(
                io.StringIO(json.dumps(data, indent=2, ensure_ascii=False)),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.json"}
            )
        
        elif format == "csv":
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Заголовки
            writer.writerow([
                "ID", "User ID", "Action", "Resource", "Resource ID",
                "Description", "Severity", "IP Address", "Created At", "Details"
            ])
            
            # Данные
            for log in logs:
                writer.writerow([
                    log.id, log.user_id, log.action, log.resource, log.resource_id,
                    log.description, log.severity, log.ip_address,
                    log.created_at.isoformat(), json.dumps(log.details) if log.details else ""
                ])
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        
    except Exception as e:
        logger.error(f"Ошибка экспорта логов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== СИСТЕМА ====================

@router.get("/system/status")
async def get_system_status(
    current_admin: User = Depends(get_current_admin)
):
    """Получить статус системы"""
    try:
        return {
            "rag_system": rag_service.get_status(),
            "vector_store": vector_store_service.get_status(),
            "embeddings": embeddings_service.get_status(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса системы: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/rag/reinitialize")
async def reinitialize_rag_system(
    current_admin: User = Depends(get_current_admin)
):
    """Переинициализировать RAG систему"""
    try:
        # Переинициализируем компоненты
        vector_store_service.initialize()
        embeddings_service.load_model()
        
        # Логируем действие
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.ADMIN_ACTION,
            resource="system",
            resource_id="rag",
            description="Reinitialized RAG system",
            severity=SeverityLevel.HIGH
        )
        
        return {"message": "RAG system reinitialized successfully"}
        
    except Exception as e:
        logger.error(f"Ошибка переинициализации RAG системы: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/reprocess")
async def reprocess_documents(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Переобработать все документы с новыми настройками валидации"""
    try:
        if not vector_store_service.is_ready():
            raise HTTPException(status_code=400, detail="Vector store not ready")
        
        # Получаем все документы
        collection = vector_store_service.collection
        total_docs = collection.count()
        
        if total_docs == 0:
            return {"message": "No documents to reprocess", "processed": 0}
        
        # Получаем все документы с метаданными
        results = collection.get(
            limit=total_docs,
            include=['metadatas', 'documents']
        )
        
        # Группируем по document_id
        documents_by_id = {}
        for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
            doc_id = meta.get('document_id', results['ids'][i])
            if doc_id not in documents_by_id:
                documents_by_id[doc_id] = {
                    "id": doc_id,
                    "metadata": meta,
                    "content": doc
                }
        
        processed_count = 0
        errors = []
        
        # Переобрабатываем каждый документ
        for doc_id, doc_data in documents_by_id.items():
            try:
                # Создаем временный файл для переобработки
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
                    tmp_file.write(doc_data['content'])
                    tmp_file_path = tmp_file.name
                
                try:
                    # Переобрабатываем с новыми настройками
                    result = await document_service.process_file(tmp_file_path, doc_data['metadata'])
                    if result.get('success'):
                        processed_count += 1
                    else:
                        errors.append(f"Document {doc_id}: {result.get('error', 'Unknown error')}")
                finally:
                    # Удаляем временный файл
                    if os.path.exists(tmp_file_path):
                        os.unlink(tmp_file_path)
                        
            except Exception as e:
                errors.append(f"Document {doc_id}: {str(e)}")
        
        # Логируем действие
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.ADMIN_ACTION,
            resource="documents",
            resource_id="reprocess",
            description=f"Reprocessed {processed_count} documents",
            severity=SeverityLevel.MEDIUM
        )
        
        return {
            "message": f"Reprocessed {processed_count} documents",
            "processed": processed_count,
            "total": len(documents_by_id),
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Ошибка переобработки документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))
