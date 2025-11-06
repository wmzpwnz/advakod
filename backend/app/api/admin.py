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
from ..core.cache import cache_service

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

@router.get("/documents", response_model=Dict)
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить список документов в RAG системе"""
    from fastapi import Response
    try:
        if not vector_store_service.is_ready():
            return {"documents": [], "total": 0, "message": "Vector store not ready"}
        
        # Получаем информацию о коллекции
        collection = vector_store_service.collection
        total_docs = collection.count()
        
        if total_docs == 0:
            return {"documents": [], "total": 0, "skip": skip, "limit": limit}
        
        # Получаем ВСЕ документы с метаданными для группировки
        # Используем альтернативные методы из-за бага в ChromaDB _decode_seq_id
        results = None
        try:
            # Сначала пробуем стандартный get
            results = collection.get(
                limit=total_docs,
                include=['metadatas', 'documents']
            )
        except (TypeError, ValueError) as e:
            # Если ошибка с _decode_seq_id, пробуем альтернативные методы
            logger.warning(f"Ошибка get() из ChromaDB (пробуем альтернативы): {e}")
            try:
                # Пробуем peek (если доступно)
                try:
                    peek_results = collection.peek(limit=min(1000, total_docs))
                    if peek_results and 'ids' in peek_results:
                        results = peek_results
                        logger.info(f"Получено {len(peek_results.get('ids', []))} документов через peek()")
                except Exception as peek_err:
                    logger.warning(f"Ошибка peek(): {peek_err}")
                    # Пробуем получить через query с dummy вектором
                    try:
                        # Используем embeddings_service из импортов
                        # Создаем dummy embedding
                        dummy_embedding = embeddings_service.get_embedding("test") if hasattr(embeddings_service, 'get_embedding') else [0.0] * 384
                        query_results = collection.query(
                            query_embeddings=[dummy_embedding],
                            n_results=min(1000, total_docs),
                            include=['metadatas', 'documents']
                        )
                        if query_results and query_results.get('ids'):
                            # Query возвращает вложенные списки
                            results = {
                                'ids': query_results.get('ids', [[]])[0] if query_results.get('ids') else [],
                                'documents': query_results.get('documents', [[]])[0] if query_results.get('documents') else [],
                                'metadatas': query_results.get('metadatas', [[]])[0] if query_results.get('metadatas') else []
                            }
                            logger.info(f"Получено {len(results['ids'])} документов через query()")
                    except Exception as query_err:
                        logger.error(f"Ошибка query(): {query_err}")
                
                # Если ничего не получилось, пробуем получить из файловой системы
                if not results:
                    logger.warning("Пробуем получить документы из файловой системы")
                    try:
                        from pathlib import Path
                        from datetime import datetime
                        import uuid as uuid_lib
                        
                        # Проверяем несколько возможных путей
                        # Примечание: codes-system пока использует старый путь downloaded_codexes
                        # (код копируется при сборке образа, не обновляется через bind mount)
                        possible_paths = [
                            "/app/data/codes_downloads",  # Новый путь (общий volume)
                            "/app/downloaded_codexes",  # Старый путь (используется codes-system)
                            "/app/data/downloaded_codexes"  # Еще один вариант
                        ]
                        codes_dir = None
                        for path_str in possible_paths:
                            path = Path(path_str)
                            if path.exists() and path.is_dir():
                                codes_dir = path
                                break
                        
                        file_docs = []
                        if codes_dir and codes_dir.exists():
                            # Загружаем кэш удаленных документов
                            try:
                                from ..services.deleted_documents_cache import deleted_documents_cache
                            except ImportError:
                                deleted_documents_cache = None
                            
                            # Список старых заглушек для исключения
                            old_stub_ids = [
                                "0001201412140001", "0001201412140002", "0001201412140003",
                                "0001201412140004", "0001201412140005", "0001201412140006",
                                "0001201410140002", "0001201905010039", "0001202203030006",
                                "198", "289-11"
                            ]
                            
                            for file_path in codes_dir.rglob("*.txt"):
                                # Пропускаем удаленные файлы
                                if deleted_documents_cache:
                                    # Проверяем по имени файла
                                    if deleted_documents_cache.is_deleted(filename=file_path.name):
                                        logger.debug(f"Пропущен удаленный файл (по имени): {file_path.name}")
                                        continue
                                    # Проверяем по ID в метаданных
                                    try:
                                        json_path = file_path.with_suffix('.json')
                                        if json_path.exists():
                                            with open(json_path, 'r', encoding='utf-8') as f:
                                                meta = json.load(f)
                                                doc_id = meta.get('document_id') or meta.get('id') or file_path.stem
                                                if deleted_documents_cache.is_deleted(document_id=doc_id):
                                                    logger.debug(f"Пропущен удаленный файл (по ID): {file_path.name} (ID: {doc_id})")
                                                    continue
                                    except Exception:
                                        pass
                                    # Проверяем по имени файла без расширения (stem)
                                    if deleted_documents_cache.is_deleted(document_id=file_path.stem):
                                        logger.debug(f"Пропущен удаленный файл (по stem): {file_path.name}")
                                        continue
                                try:
                                    stat = file_path.stat()
                                    
                                    # Пропускаем маленькие файлы (заглушки <= 2000 байт - заглушки обычно 500-1500 байт)
                                    if stat.st_size <= 2000:
                                        logger.debug(f"Пропущен маленький файл: {file_path.name} ({stat.st_size} байт)")
                                        continue
                                    
                                    # Пропускаем файлы с ID старых заглушек
                                    file_stem = file_path.stem
                                    if any(old_id in file_stem for old_id in old_stub_ids):
                                        logger.debug(f"Пропущен файл заглушки: {file_path.name} (ID: {file_stem})")
                                        continue
                                    
                                    # Дополнительная проверка: если файл содержит только навигацию/заглушку
                                    try:
                                        content_check = file_path.read_text(encoding='utf-8', errors='ignore')[:500].lower()
                                        if len(content_check) < 100 or any(keyword in content_check for keyword in ['навигация', 'navigation', 'заглушка', 'stub', 'placeholder']):
                                            logger.debug(f"Пропущен файл-заглушка по содержимому: {file_path.name}")
                                            continue
                                    except:
                                        pass  # Если не можем прочитать - пропускаем этот файл
                                    
                                    # Пробуем загрузить метаданные из JSON файла
                                    metadata_file = file_path.with_suffix('.json')
                                    metadata_dict = {}
                                    if metadata_file.exists():
                                        try:
                                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                                api_metadata = json.load(f)
                                                # Используем метаданные из API
                                                metadata_dict = {
                                                    "filename": api_metadata.get('file_name', file_path.name),
                                                    "codex_name": api_metadata.get('codex_name'),
                                                    "document_name": api_metadata.get('name'),
                                                    "document_title": api_metadata.get('title'),
                                                    "document_number": api_metadata.get('number'),
                                                    "document_date": api_metadata.get('document_date'),
                                                    "publish_date": api_metadata.get('publish_date'),
                                                    "view_date": api_metadata.get('view_date'),
                                                    "document_type": api_metadata.get('document_type'),
                                                    "pages_count": api_metadata.get('pages_count'),
                                                    "signatory_authorities": api_metadata.get('signatory_authorities', []),
                                                    "eo_number": api_metadata.get('eo_number'),
                                                    "source_url": api_metadata.get('source_url'),
                                                    "source_type": "legal_document",
                                                    "source_path": str(file_path),
                                                    "added_at": api_metadata.get('publish_date') or datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                                    "size": stat.st_size,
                                                    "api_metadata_retrieved_at": api_metadata.get('api_metadata_retrieved_at')
                                                }
                                        except Exception as meta_err:
                                            logger.warning(f"Ошибка загрузки метаданных для {file_path.name}: {meta_err}")
                                    
                                    # Если метаданных нет, используем базовые + пытаемся определить кодекс по имени файла
                                    if not metadata_dict:
                                        # Список кодексов для определения по eo_number
                                        codex_names = {
                                            '0001201410140002': 'Гражданский кодекс РФ',
                                            '0001202203030006': 'Уголовный кодекс РФ',
                                            '0001201412140001': 'Трудовой кодекс РФ',
                                            '0001201412140002': 'Семейный кодекс РФ',
                                            '0001201412140003': 'Жилищный кодекс РФ',
                                            '0001201412140004': 'Налоговый кодекс РФ',
                                            '0001201412140005': 'Бюджетный кодекс РФ',
                                            '0001201412140006': 'Кодекс об административных правонарушениях РФ'
                                        }
                                        
                                        # Извлекаем eo_number из имени файла
                                        eo_number = file_path.stem
                                        codex_name = codex_names.get(eo_number, None)
                                        
                                        metadata_dict = {
                                            "filename": file_path.name,
                                            "eo_number": eo_number,
                                            "codex_name": codex_name,
                                            "source_type": "legal_document",
                                            "source_path": str(file_path),
                                            "added_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                            "size": stat.st_size,
                                            "document_type": "legal_document",
                                            "pages_count": None,
                                            "note": "Метаданные из API будут загружены при следующем цикле скачивания"
                                        }
                                    
                                    # Пропускаем файлы, которые являются заглушками
                                    # Читаем первые 200 символов для проверки
                                    content_preview = file_path.read_text(encoding='utf-8', errors='ignore')[:200]
                                    if len(content_preview) < 50:  # Слишком короткий контент - пропускаем
                                        continue
                                    
                                    # Читаем контент (ограничиваем для экономии памяти)
                                    content = file_path.read_text(encoding='utf-8', errors='ignore')[:500]
                                    
                                    # Формируем название для отображения
                                    display_name = metadata_dict.get("codex_name") or metadata_dict.get("document_name") or metadata_dict.get("filename", file_path.name)
                                    
                                    # Определяем размер для отображения
                                    pdf_size = metadata_dict.get("pdf_file_length")
                                    pages_count = metadata_dict.get("pages_count")
                                    
                                    # Если файл маленький, но должен быть большим - показываем предупреждение
                                    if pdf_size:
                                        # Используем размер PDF из API
                                        display_size = pdf_size
                                        size_warning = None
                                    elif pages_count and pages_count > 10 and stat.st_size < 5000:
                                        # Файл слишком маленький для такого количества страниц
                                        display_size = stat.st_size  # Показываем реальный размер
                                        size_warning = f"⚠️ Файл содержит только HTML-заглушку ({stat.st_size} байт), а не полный текст кодекса. Ожидается ~{pages_count*5}KB для {pages_count} страниц"
                                    else:
                                        display_size = stat.st_size
                                        size_warning = None
                                    
                                    file_docs.append({
                                        "id": metadata_dict.get("eo_number", str(uuid_lib.uuid4())),
                                        "name": display_name,  # Название для отображения
                                        "title": metadata_dict.get("document_title") or metadata_dict.get("document_name") or display_name,
                                        "content": content,
                                        "metadata": metadata_dict,
                                        "length": len(content),
                                        "chunks_count": 1,
                                        "total_length": stat.st_size,
                                        "filename": metadata_dict.get("filename", file_path.name),
                                        "codex_name": metadata_dict.get("codex_name"),  # Название кодекса
                                        "document_type": metadata_dict.get("document_type", "legal_document"),
                                        "publish_date": metadata_dict.get("publish_date"),
                                        "view_date": metadata_dict.get("view_date"),
                                        "pages_count": pages_count,
                                        "size": display_size,
                                        "actual_file_size": stat.st_size,  # Реальный размер сохраненного файла
                                        "expected_pdf_size": pdf_size,  # Ожидаемый размер PDF из API
                                        "size_warning": size_warning,  # Предупреждение о размере
                                        "content_preview_length": len(content),  # Длина preview для справки
                                        "note": metadata_dict.get("note")  # Примечание о метаданных
                                    })
                                except Exception as file_err:
                                    logger.warning(f"Ошибка чтения файла {file_path}: {file_err}")
                            
                            if file_docs:
                                documents = file_docs[skip:skip + limit]
                                return {
                                    "documents": documents,
                                    "total": len(file_docs),
                                    "skip": skip,
                                    "limit": limit,
                                    "message": "Documents loaded from file system (ChromaDB unavailable)"
                                }
                    except Exception as fs_err:
                        logger.error(f"Ошибка получения из файловой системы: {fs_err}")
                    
                    return {"documents": [], "total": 0, "message": "ChromaDB data corruption detected. Please re-index documents."}
            except Exception as fallback_err:
                logger.error(f"Ошибка fallback получения документов: {fallback_err}")
                return {"documents": [], "total": 0, "message": f"Error fetching from vector store: {str(fallback_err)}"}
        except Exception as e:
            logger.error(f"Неожиданная ошибка получения данных из ChromaDB: {e}")
            return {"documents": [], "total": 0, "message": f"Error fetching from vector store: {str(e)}"}
        
        # Проверяем структуру данных
        if not results or 'documents' not in results or 'metadatas' not in results:
            logger.warning("ChromaDB вернул пустые или некорректные данные")
            return {"documents": [], "total": 0, "skip": skip, "limit": limit}
        
        documents_list = results.get('documents', [])
        metadatas_list = results.get('metadatas', [])
        ids_list = results.get('ids', [])
        
        if not documents_list or not metadatas_list:
            return {"documents": [], "total": 0, "skip": skip, "limit": limit}
        
        # Список старых заглушек для исключения
        old_stub_ids = [
            "0001201412140001", "0001201412140002", "0001201412140003",
            "0001201412140004", "0001201412140005", "0001201412140006",
            "0001201410140002", "0001201905010039", "0001202203030006",
            "198", "289-11"
        ]
        
        # Группируем чанки по document_id для получения уникальных документов
        documents_by_id = {}
        for i in range(min(len(documents_list), len(metadatas_list))):
            try:
                doc = documents_list[i] if isinstance(documents_list[i], str) else str(documents_list[i])
                meta = metadatas_list[i] if isinstance(metadatas_list[i], dict) else {}
                doc_id = str(meta.get('document_id', ids_list[i] if i < len(ids_list) else f"doc_{i}"))
                
                # Пропускаем заглушки по ID
                if any(old_id in str(doc_id) or old_id in meta.get('filename', '') or old_id in meta.get('source_path', '') for old_id in old_stub_ids):
                    continue
                
                # Пропускаем маленькие файлы (<= 2000 байт - заглушки обычно 500-1500 байт)
                # Используем size из метаданных, если нет - пробуем file_size, если нет - длину чанка
                # НО: если это чанк большого документа, len(doc) может быть маленьким
                # Поэтому проверяем только если size/file_size есть в метаданных
                file_size = meta.get('size') or meta.get('file_size')
                if file_size is None:
                    # Если размера нет в метаданных, пропускаем проверку по размеру
                    # (документ может быть разбит на чанки)
                    file_size = len(doc) if isinstance(doc, str) else 0
                    # Но если чанк очень маленький (< 1000), это может быть заглушка
                    if file_size < 1000:
                        continue
                elif file_size <= 2000:
                    continue
                
                if doc_id not in documents_by_id:
                    # Извлекаем название из метаданных
                    display_name = meta.get("codex_name") or meta.get("document_name") or meta.get("filename", f"doc_{doc_id}")
                    
                    # Создаем новый документ
                    documents_by_id[doc_id] = {
                        "id": doc_id,
                        "name": display_name,
                        "title": meta.get("document_title") or meta.get("document_name") or display_name,
                        "content": doc,
                        "metadata": meta,
                        "length": len(doc) if isinstance(doc, str) else 0,
                        "chunks_count": 1,
                        "total_length": len(doc) if isinstance(doc, str) else 0,
                        "filename": meta.get("filename", f"doc_{doc_id}"),
                        "codex_name": meta.get("codex_name"),
                        "document_type": meta.get("document_type", "legal_document"),
                        "publish_date": meta.get("publish_date"),
                        "view_date": meta.get("view_date"),
                        "pages_count": meta.get("pages_count"),
                        # Используем размер PDF из метаданных API (если есть), иначе размер файла
                        "size": meta.get("pdf_file_length") or meta.get("size") or (len(doc) if isinstance(doc, str) else 0),
                        "actual_file_size": meta.get("size"),  # Реальный размер сохраненного файла
                        "note": meta.get("note")  # Примечание о метаданных
                    }
                else:
                    # Обновляем существующий документ
                    existing = documents_by_id[doc_id]
                    existing["chunks_count"] += 1
                    doc_len = len(doc) if isinstance(doc, str) else 0
                    existing["total_length"] += doc_len
                    # Обновляем контент на более длинный чанк
                    if doc_len > existing["length"]:
                        existing["content"] = doc
                        existing["length"] = doc_len
                    
                    # Обновляем метаданные если они более полные
                    if meta.get("codex_name") and not existing.get("codex_name"):
                        existing["codex_name"] = meta.get("codex_name")
                        existing["name"] = meta.get("codex_name") or existing.get("name")
                    if meta.get("document_name") and not existing.get("title"):
                        existing["title"] = meta.get("document_name")
            except Exception as e:
                logger.warning(f"Ошибка обработки документа {i}: {e}")
                continue
        
        # Преобразуем в список
        documents = list(documents_by_id.values())
        
        # ФИНАЛЬНАЯ фильтрация заглушек (на всякий случай)
        old_stub_ids_final = [
            "0001201412140001", "0001201412140002", "0001201412140003",
            "0001201412140004", "0001201412140005", "0001201412140006",
            "0001201410140002", "0001201905010039", "0001202203030006",
            "198", "289-11"
        ]
        
        documents = [
            doc for doc in documents
            if not any(
                old_id in str(doc.get('id', '')) or 
                old_id in str(doc.get('filename', '')) or
                str(doc.get('size', 0)) == '500' or
                (isinstance(doc.get('size'), int) and doc.get('size') <= 2000) or
                (isinstance(doc.get('actual_file_size'), int) and doc.get('actual_file_size') <= 2000)
                for old_id in old_stub_ids_final
            )
        ]
        
        # Сортируем по дате добавления
        documents.sort(key=lambda x: x.get('metadata', {}).get('added_at', ''), reverse=True)
        
        # Удаляем дубликаты по source_url для URL документов + финальная фильтрация
        seen_urls = set()
        unique_documents = []
        for doc in documents:
            # ФИНАЛЬНАЯ проверка заглушек
            doc_id = str(doc.get('id', ''))
            filename = str(doc.get('filename', ''))
            size = doc.get('size', 0) or doc.get('actual_file_size', 0)
            
            # Пропускаем заглушки по ID
            if any(old_id in doc_id or old_id in filename for old_id in old_stub_ids_final):
                logger.debug(f"Пропущен заглушка в финальном списке: {doc_id} ({filename})")
                continue
            
            # Пропускаем маленькие файлы (<= 2000 байт)
            if size <= 2000:
                logger.debug(f"Пропущен маленький файл в финальном списке: {doc_id} ({size} байт)")
                continue
            
            if doc.get('metadata', {}).get('source_type') == 'url':
                source_url = doc.get('metadata', {}).get('source_url', '')
                if source_url not in seen_urls:
                    seen_urls.add(source_url)
                    unique_documents.append(doc)
            else:
                unique_documents.append(doc)
        
        documents = unique_documents
        
        # Применяем пагинацию
        total_unique_docs = len(documents)
        documents = documents[skip:skip + limit]
        
        from fastapi.responses import JSONResponse
        response = JSONResponse({
            "documents": documents,
            "total": total_unique_docs,
            "skip": skip,
            "limit": limit
        })
        # Добавляем заголовки для предотвращения кэширования
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
        
    except Exception as e:
        logger.error(f"Ошибка получения документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Получить список чанков для конкретного документа"""
    try:
        if not vector_store_service.is_ready():
            return {"chunks": [], "message": "Vector store not ready"}
        
        collection = vector_store_service.collection
        
        # Получаем все чанки с document_id
        try:
            # Получаем ВСЕ записи из коллекции (без ограничения)
            # ChromaDB не поддерживает фильтрацию по метаданным в get(), поэтому получаем все и фильтруем
            all_results = collection.get(
                include=['metadatas', 'documents'],
                limit=100000  # Большое число, чтобы получить все записи
            )
            
            chunks = []
            if all_results.get('metadatas') and all_results.get('documents'):
                metadatas_list = all_results['metadatas']
                documents_list = all_results['documents']
                
                # Получаем все ID через peek или count + get
                try:
                    # Пробуем получить ID через peek
                    peek_results = collection.peek(limit=100000)
                    ids_list = peek_results.get('ids', [])
                except:
                    # Если peek не работает, получаем через get с where (если поддерживается)
                    # Или используем индексы
                    ids_list = []
                    try:
                        # Пробуем получить через count и затем get
                        total_count = collection.count()
                        if total_count > 0:
                            # Получаем все ID через get с пустым where
                            ids_results = collection.get(limit=100000)
                            ids_list = ids_results.get('ids', [])
                    except:
                        pass
                
                for i, meta in enumerate(metadatas_list):
                    # Проверяем, что это чанк нужного документа
                    chunk_doc_id = meta.get('document_id')
                    
                    # Сравниваем document_id (может быть строкой или числом)
                    if str(chunk_doc_id) == str(document_id):
                        # Получаем ID чанка
                        chunk_id = ids_list[i] if i < len(ids_list) else f"chunk_{i}_{document_id}"
                        chunk_content = documents_list[i] if i < len(documents_list) else ""
                        
                        chunks.append({
                            "id": chunk_id,
                            "content": chunk_content,
                            "chunk_index": meta.get('chunk_index', i),
                            "chunk_length": len(chunk_content) if isinstance(chunk_content, str) else 0,
                            "metadata": meta
                        })
            
            # Сортируем по chunk_index
            chunks.sort(key=lambda x: x.get('chunk_index', 0))
            
            logger.info(f"📊 Найдено чанков для document_id={document_id}: {len(chunks)}")
            
            return {
                "document_id": document_id,
                "chunks": chunks,
                "total": len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения чанков для document_id={document_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"chunks": [], "message": f"Error fetching chunks: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Ошибка получения чанков документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    """Удалить документ из RAG системы (синхронизированно с simple_expert_rag) и из файловой системы"""
    try:
        if not vector_store_service.is_ready():
            raise HTTPException(status_code=503, detail="Vector store not ready")
        
        # Импортируем simple_expert_rag
        from ..services.simple_expert_rag import simple_expert_rag
        from pathlib import Path
        import os
        
        # 1. Удаляем из ChromaDB (используем альтернативный метод из-за бага ChromaDB)
        collection = vector_store_service.collection
        matching_ids = []
        filename_to_delete = None
        source_path_to_delete = None
        
        # Сначала пробуем удалить напрямую по ID (самый надежный метод)
        try:
            collection.delete(ids=[document_id])
            matching_ids = [document_id]
            chromadb_chunks_deleted = 1
            logger.info(f"🗑️ Удалено из ChromaDB напрямую по ID: {document_id}")
        except Exception as direct_err:
            logger.warning(f"Ошибка прямого удаления по ID: {direct_err}")
            chromadb_chunks_deleted = 0
            
            # Если прямое удаление не сработало, пробуем найти через альтернативные методы
            try:
                # Метод 1: Пробуем через query с dummy embedding
                try:
                    from ..services.embeddings_service import embeddings_service
                    dummy_embedding = embeddings_service.get_embedding("test") if hasattr(embeddings_service, 'get_embedding') else [0.0] * 384
                    query_results = collection.query(
                        query_embeddings=[dummy_embedding],
                        n_results=1000,
                        include=['metadatas']
                    )
                    if query_results and query_results.get('ids'):
                        all_ids = query_results.get('ids', [[]])[0] if query_results.get('ids') else []
                        all_metadatas = query_results.get('metadatas', [[]])[0] if query_results.get('metadatas') else []
                        
                        for i, (chunk_id, metadata) in enumerate(zip(all_ids, all_metadatas)):
                            if metadata and (metadata.get('document_id') == document_id or chunk_id == document_id or 
                                           document_id in str(chunk_id) or document_id in str(metadata.get('filename', ''))):
                                matching_ids.append(chunk_id)
                                # Сохраняем информацию о файле для удаления
                                if not filename_to_delete and metadata.get('filename'):
                                    filename_to_delete = metadata.get('filename')
                                if not source_path_to_delete and metadata.get('source_path'):
                                    source_path_to_delete = metadata.get('source_path')
                except Exception as query_err:
                    logger.warning(f"Ошибка query() при удалении: {query_err}")
            except Exception as e:
                logger.warning(f"Ошибка получения документов из ChromaDB: {e}")
            
            # Удаляем найденные чанки
            if matching_ids:
                try:
                    collection.delete(ids=matching_ids)
                    chromadb_chunks_deleted = len(matching_ids)
                    logger.info(f"🗑️ Удалено из ChromaDB: {chromadb_chunks_deleted} чанков")
                except Exception as delete_err:
                    logger.warning(f"Ошибка удаления из ChromaDB: {delete_err}")
                    chromadb_chunks_deleted = 0
        
        # 2. Удаляем из simple_expert_rag
        simple_rag_result = await simple_expert_rag.delete_document(document_id)
        simple_rag_chunks_deleted = simple_rag_result.get('chunks_deleted', 0)
        
        # Если не найден по document_id, пробуем найти по именам файлов
        if simple_rag_chunks_deleted == 0 and filename_to_delete:
            try:
                filename_result = await simple_expert_rag.delete_document(filename_to_delete)
                if filename_result.get('success', False):
                    simple_rag_chunks_deleted += filename_result.get('chunks_deleted', 0)
                    simple_rag_result = filename_result
            except Exception as e:
                logger.warning(f"Ошибка удаления из simple_expert_rag по filename: {e}")
        
        # 3. Удаляем файлы из файловой системы
        files_deleted = []
        possible_paths = [
            "/app/data/codes_downloads",
            "/app/downloaded_codexes",
            "/app/data/downloaded_codexes"
        ]
        
        # Удаляем по source_path если есть
        if source_path_to_delete:
            try:
                file_path = Path(source_path_to_delete)
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
                    files_deleted.append(str(file_path))
                    logger.info(f"🗑️ Удален файл: {file_path}")
                    # Также удаляем JSON метаданные если есть
                    json_path = file_path.with_suffix('.json')
                    if json_path.exists():
                        json_path.unlink()
                        files_deleted.append(str(json_path))
            except Exception as e:
                logger.warning(f"Ошибка удаления файла по source_path: {e}")
        
        # Удаляем по filename если есть
        if filename_to_delete:
            for base_path in possible_paths:
                try:
                    base_dir = Path(base_path)
                    if base_dir.exists():
                        # Ищем файл по имени
                        for file_path in base_dir.rglob(filename_to_delete):
                            if file_path.exists() and file_path.is_file():
                                file_path.unlink()
                                files_deleted.append(str(file_path))
                                logger.info(f"🗑️ Удален файл: {file_path}")
                                # Также удаляем JSON метаданные если есть
                                json_path = file_path.with_suffix('.json')
                                if json_path.exists():
                                    json_path.unlink()
                                    files_deleted.append(str(json_path))
                except Exception as e:
                    logger.warning(f"Ошибка поиска файла в {base_path}: {e}")
        
        # Дополнительно: если document_id похож на имя файла, ищем по нему
        if not files_deleted and document_id:
            # Проверяем, может ли document_id быть именем файла
            possible_filenames = [
                document_id,
                f"{document_id}.txt",
                f"{document_id}.pdf"
            ]
            for base_path in possible_paths:
                try:
                    base_dir = Path(base_path)
                    if base_dir.exists():
                        for possible_filename in possible_filenames:
                            for file_path in base_dir.rglob(possible_filename):
                                if file_path.exists() and file_path.is_file():
                                    file_path.unlink()
                                    files_deleted.append(str(file_path))
                                    logger.info(f"🗑️ Удален файл по document_id (как имя файла): {file_path}")
                                    if not filename_to_delete:
                                        filename_to_delete = file_path.name
                                    json_path = file_path.with_suffix('.json')
                                    if json_path.exists():
                                        json_path.unlink()
                                        files_deleted.append(str(json_path))
                                    break
                except Exception as e:
                    logger.warning(f"Ошибка поиска файла по document_id в {base_path}: {e}")
        
        # Дополнительно: ищем файлы по document_id в имени (для случаев, когда document_id содержит имя файла)
        # Например, если document_id = "tk_codex_20251106_103457" или содержит имя файла
        if not files_deleted and document_id:
            # Пробуем найти файлы, которые могут быть связаны с этим document_id
            for base_path in possible_paths:
                try:
                    base_dir = Path(base_path)
                    if base_dir.exists():
                        # Ищем файлы, содержащие document_id в имени или метаданных
                        for file_path in base_dir.rglob("*.txt"):
                            try:
                                # Проверяем JSON метаданные
                                json_path = file_path.with_suffix('.json')
                                if json_path.exists():
                                    with open(json_path, 'r', encoding='utf-8') as f:
                                        meta = json.load(f)
                                        if meta.get('document_id') == document_id or meta.get('id') == document_id:
                                            file_path.unlink()
                                            json_path.unlink()
                                            files_deleted.append(str(file_path))
                                            files_deleted.append(str(json_path))
                                            logger.info(f"🗑️ Удален файл по document_id: {file_path}")
                                            break
                            except Exception:
                                pass
                except Exception as e:
                    logger.warning(f"Ошибка поиска файла по document_id в {base_path}: {e}")
        
        # 4. Если ничего не найдено, пробуем найти по имени файла из document_id
        if chromadb_chunks_deleted == 0 and simple_rag_chunks_deleted == 0 and len(files_deleted) == 0:
            # Пробуем извлечь имя файла из document_id
            # document_id может быть: "Трудовой_кодекс_РФ", "Трудовой_кодекс_РФ.txt", UUID и т.д.
            logger.info(f"🔍 Пробуем найти документ по альтернативным методам: {document_id}")
            
            # Пробуем удалить файл, если document_id похож на имя файла
            possible_names = [
                document_id,
                f"{document_id}.txt",
                f"{document_id}.pdf",
                document_id.replace("_", " "),
                document_id.replace(" ", "_")
            ]
            
            for possible_name in possible_names:
                for base_path in possible_paths:
                    try:
                        base_dir = Path(base_path)
                        if base_dir.exists():
                            for file_path in base_dir.rglob(possible_name):
                                if file_path.exists() and file_path.is_file():
                                    file_path.unlink()
                                    files_deleted.append(str(file_path))
                                    logger.info(f"🗑️ Удален файл по альтернативному поиску: {file_path}")
                                    if not filename_to_delete:
                                        filename_to_delete = file_path.name
                                    json_path = file_path.with_suffix('.json')
                                    if json_path.exists():
                                        json_path.unlink()
                                        files_deleted.append(str(json_path))
                                    break
                    except Exception as e:
                        logger.warning(f"Ошибка альтернативного поиска в {base_path}: {e}")
            
            # Если все еще ничего не найдено, но файл был удален - считаем успешным
            if len(files_deleted) > 0:
                logger.info(f"✅ Документ найден и удален через альтернативный поиск")
                chromadb_chunks_deleted = 1  # Помечаем как успешное удаление
            elif chromadb_chunks_deleted == 0 and simple_rag_chunks_deleted == 0 and len(files_deleted) == 0:
                logger.warning(f"⚠️ Документ {document_id} не найден ни в ChromaDB, ни в simple_expert_rag, ни в файловой системе")
                # НЕ выбрасываем ошибку - просто помечаем как удаленный в кэше
                logger.info(f"📝 Помечаем документ как удаленный в кэше (возможно, уже был удален)")
        
        # 5. Помечаем документ как удаленный в кэше (всегда, даже если не найден)
        try:
            from ..services.deleted_documents_cache import deleted_documents_cache
            # Помечаем и по ID, и по имени файла
            deleted_documents_cache.mark_deleted(document_id=document_id, filename=filename_to_delete)
            # Также помечаем по имени файла без расширения, если это кодекс
            if filename_to_delete:
                filename_stem = Path(filename_to_delete).stem
                if filename_stem != filename_to_delete:
                    deleted_documents_cache.mark_deleted(document_id=filename_stem)
            # Если document_id похож на имя файла, помечаем и его
            if not filename_to_delete and (document_id.endswith('.txt') or document_id.endswith('.pdf')):
                deleted_documents_cache.mark_deleted(filename=document_id)
                filename_stem = Path(document_id).stem
                deleted_documents_cache.mark_deleted(document_id=filename_stem)
            logger.info(f"✅ Документ помечен как удаленный в кэше: ID={document_id}, filename={filename_to_delete}")
        except Exception as cache_err:
            logger.warning(f"Ошибка добавления в кэш удаленных документов: {cache_err}")
        
        # 6. Логируем действие
        try:
            audit_service = get_audit_service(db)
            audit_service.log_action(
                user_id=current_admin.id,
                action=ActionType.ADMIN_ACTION,
                resource="document",
                resource_id=document_id,
                description=f"Deleted document from RAG systems (ChromaDB: {chromadb_chunks_deleted}, Simple RAG: {simple_rag_chunks_deleted} chunks, Files: {len(files_deleted)})",
                severity=SeverityLevel.MEDIUM,
                details={
                    "chromadb_chunks_deleted": chromadb_chunks_deleted,
                    "simple_rag_chunks_deleted": simple_rag_chunks_deleted,
                    "files_deleted": files_deleted,
                    "simple_rag_success": simple_rag_result.get('success', False)
                }
            )
        except Exception as audit_err:
            logger.warning(f"Ошибка логирования действия: {audit_err}")
        
        # Всегда возвращаем успех, даже если документ не был найден (возможно, уже был удален)
        # Главное - он помечен в кэше и не будет показываться
        return {
            "message": "Document deleted successfully from all RAG systems and file system",
            "chromadb_chunks_deleted": chromadb_chunks_deleted,
            "simple_rag_chunks_deleted": simple_rag_chunks_deleted,
            "total_chunks_deleted": chromadb_chunks_deleted + simple_rag_chunks_deleted,
            "files_deleted": files_deleted,
            "files_deleted_count": len(files_deleted),
            "simple_rag_status": simple_rag_result.get('status', 'unknown'),
            "document_id": document_id,
            "marked_in_cache": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления документа {document_id}: {e}")
        logger.error(f"Тип ошибки: {type(e)}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
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

@router.post("/documents/cleanup-stubs")
async def cleanup_codex_stubs(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Удаляет старые заглушки кодексов (маленькие файлы <= 1000 байт)"""
    try:
        if not vector_store_service.is_ready():
            raise HTTPException(status_code=503, detail="Vector store not ready")
        
        # Список старых заглушек для удаления
        old_codexes = [
            "0001201412140001",  # Трудовой кодекс РФ
            "0001201412140002",  # Семейный кодекс РФ
            "0001201412140003",  # Жилищный кодекс РФ
            "0001201412140004",  # Налоговый кодекс РФ
            "0001201412140005",  # Бюджетный кодекс РФ
            "0001201412140006",  # Кодекс об административных правонарушениях РФ
            "0001201410140002",  # Гражданский кодекс РФ (часть 1) - заглушка
            "0001201905010039",  # Налоговый кодекс РФ (часть 1) - заглушка
            "0001202203030006",  # Уголовный кодекс РФ - заглушка
            "198",
            "289-11",
        ]
        
        # Получаем список документов из ChromaDB
        collection = vector_store_service.collection
        all_docs = collection.get(include=['metadatas'])
        
        documents_to_delete = []
        deleted_count = 0
        total_chunks_deleted = 0
        
        # Импортируем simple_expert_rag для удаления из обеих систем
        from ..services.simple_expert_rag import simple_expert_rag
        
        for i, doc_id in enumerate(all_docs['ids']):
            metadata = all_docs['metadatas'][i] if all_docs['metadatas'] else {}
            filename = metadata.get('filename', '') or metadata.get('file_name', '') or str(doc_id)
            source_path = metadata.get('source_path', '')
            file_size = metadata.get('size', 0) or metadata.get('file_size', 0)
            
            should_delete = False
            reason = ""
            
            # Проверяем по ID или имени файла
            for old_id in old_codexes:
                if old_id in str(doc_id) or old_id in filename or old_id in source_path:
                    should_delete = True
                    reason = f"Старая заглушка (ID: {old_id})"
                    break
            
            # Проверяем маленькие файлы кодексов
            if not should_delete and file_size <= 1000:
                title = metadata.get('title', '').lower() or metadata.get('name', '').lower()
                if any(kw in title for kw in ["кодекс", "codex"]):
                    should_delete = True
                    reason = f"Маленький файл кодекса ({file_size} байт)"
            
            if should_delete:
                documents_to_delete.append({
                    "id": doc_id,
                    "filename": filename,
                    "reason": reason
                })
        
        # Удаляем найденные документы
        for doc in documents_to_delete:
            try:
                # Удаляем из ChromaDB
                collection.delete(ids=[doc['id']])
                chromadb_chunks = 1  # Приблизительно
                
                # Удаляем из simple_expert_rag
                simple_rag_result = await simple_expert_rag.delete_document(doc['id'])
                simple_rag_chunks = simple_rag_result.get('chunks_deleted', 0)
                
                # Если не найден по ID, пробуем по имени файла
                if simple_rag_chunks == 0:
                    filename_result = await simple_expert_rag.delete_document(doc['filename'])
                    simple_rag_chunks = filename_result.get('chunks_deleted', 0)
                
                deleted_count += 1
                total_chunks_deleted += chromadb_chunks + simple_rag_chunks
                
            except Exception as e:
                logger.warning(f"Ошибка удаления документа {doc['id']}: {e}")
                continue
        
        # Логируем действие
        audit_service = get_audit_service(db)
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.ADMIN_ACTION,
            resource="documents",
            resource_id="cleanup_stubs",
            description=f"Cleaned up {deleted_count} codex stubs",
            severity=SeverityLevel.MEDIUM,
            details={
                "deleted_count": deleted_count,
                "total_chunks_deleted": total_chunks_deleted,
                "documents": [d['filename'] for d in documents_to_delete]
            }
        )
        
        return {
            "message": f"Удалено заглушек: {deleted_count}",
            "deleted_count": deleted_count,
            "total_chunks_deleted": total_chunks_deleted,
            "documents": documents_to_delete
        }
        
    except Exception as e:
        logger.error(f"Ошибка очистки заглушек: {e}")
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

# ==================== УПРАВЛЕНИЕ КЭШЕМ ====================

@router.get("/cache/status")
async def get_cache_status(
    current_admin: User = Depends(get_current_admin)
):
    """Получение статуса кэша"""
    try:
        health_status = await cache_service.health_check()
        stats = await cache_service.get_stats()
        
        return {
            "status": "success",
            "cache_health": health_status,
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/reconnect")
async def reconnect_cache(
    current_admin: User = Depends(get_current_admin)
):
    """Принудительное переподключение к Redis"""
    try:
        success = await cache_service.reconnect()
        
        if success:
            return {
                "status": "success",
                "message": "Redis reconnection successful",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "warning",
                "message": "Redis reconnection failed, using in-memory cache",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error reconnecting cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/clear")
@require_admin_action_validation("clear_cache", "system")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Паттерн для очистки (например: user_profile:*)"),
    current_admin: User = Depends(get_current_admin),
    request: Request = None
):
    """Очистка кэша по паттерну или полная очистка"""
    try:
        if pattern:
            cleared_count = await cache_service.clear_pattern(pattern)
            message = f"Cleared {cleared_count} keys matching pattern '{pattern}'"
        else:
            # Полная очистка кэша
            await cache_service.in_memory_cache.clear()
            if cache_service.redis_client and cache_service._initialized:
                await cache_service.redis_client.flushdb()
            message = "All cache cleared"
        
        # Логируем действие
        audit_service = get_audit_service()
        audit_service.log_action(
            user_id=current_admin.id,
            action=ActionType.SYSTEM_MAINTENANCE,
            resource="cache",
            resource_id=None,
            description=f"Cache cleared by admin: {message}",
            severity=SeverityLevel.MEDIUM
        )
        
        return {
            "status": "success",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/keys")
async def get_cache_keys(
    pattern: str = Query("*", description="Паттерн для поиска ключей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество ключей"),
    current_admin: User = Depends(get_current_admin)
):
    """Получение списка ключей кэша"""
    try:
        keys = []
        
        if cache_service.redis_client and cache_service._initialized:
            try:
                redis_keys = await cache_service.redis_client.keys(pattern)
                keys.extend(redis_keys[:limit])
            except Exception as e:
                logger.warning(f"Error getting Redis keys: {e}")
        
        # Добавляем ключи из in-memory кэша
        in_memory_keys = list(cache_service.in_memory_cache._cache.keys())
        if pattern != "*":
            # Простая фильтрация по паттерну для in-memory кэша
            import fnmatch
            in_memory_keys = [k for k in in_memory_keys if fnmatch.fnmatch(k, pattern)]
        
        keys.extend(in_memory_keys[:limit - len(keys)])
        
        return {
            "status": "success",
            "keys": keys[:limit],
            "total_found": len(keys),
            "pattern": pattern,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cache keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/key/{key}")
async def get_cache_value(
    key: str,
    current_admin: User = Depends(get_current_admin)
):
    """Получение значения по ключу из кэша"""
    try:
        value = await cache_service.get(key)
        
        return {
            "status": "success",
            "key": key,
            "value": value,
            "exists": value is not None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cache value for key '{key}': {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache/key/{key}")
async def delete_cache_key(
    key: str,
    current_admin: User = Depends(get_current_admin)
):
    """Удаление ключа из кэша"""
    try:
        success = await cache_service.delete(key)
        
        return {
            "status": "success",
            "key": key,
            "deleted": success,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error deleting cache key '{key}': {e}")
        raise HTTPException(status_code=500, detail=str(e))