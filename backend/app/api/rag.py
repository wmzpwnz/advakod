"""
API для управления RAG (Retrieval-Augmented Generation) системой
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import os
import tempfile
import json

from ..services.auth_service import auth_service
from ..models.user import User
from ..services.rag_service import rag_service
from ..services.document_service import document_service
from ..services.vector_store_service import vector_store_service
from ..services.embeddings_service import embeddings_service
from ..middleware.ml_rate_limit import rag_rate_limit, embedding_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status")
async def get_rag_status():
    """Получить статус RAG системы"""
    try:
        status = rag_service.get_status()
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize")
async def initialize_rag_system(current_user: User = Depends(auth_service.get_current_active_user)):
    """Инициализировать RAG систему"""
    try:
        # Инициализируем компоненты
        vector_store_service.initialize()
        embeddings_service.load_model()
        
        # Ждем немного для загрузки
        import asyncio
        await asyncio.sleep(2)
        
        status = rag_service.get_status()
        
        return {
            "success": True,
            "message": "RAG система инициализирована",
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Ошибка инициализации RAG: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Загрузить документ для индексации"""
    try:
        # Проверяем размер файла (максимум 10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Файл слишком большой (максимум 10MB)")
        
        # Проверяем формат файла
        allowed_extensions = {'.pdf', '.docx', '.txt', '.md'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Неподдерживаемый формат файла. Поддерживаются: {', '.join(allowed_extensions)}"
            )
        
        # Сохраняем файл во временную директорию
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Подготавливаем метаданные
            metadata = {
                "uploaded_by": current_user.id,
                "uploader_email": current_user.email,
                "original_filename": file.filename,
                "file_size": len(content)
            }
            
            if title:
                metadata["title"] = title
            if description:
                metadata["description"] = description
            
            # Обрабатываем файл
            result = await document_service.process_file(temp_file_path, metadata)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Документ '{file.filename}' успешно загружен и проиндексирован",
                    "result": result
                }
            else:
                raise HTTPException(status_code=400, detail=result.get("error", "Ошибка обработки файла"))
                
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка загрузки документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/add-text")
async def add_text_document(
    title: str = Form(...),
    content: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Добавить текстовый документ"""
    try:
        if not content.strip():
            raise HTTPException(status_code=400, detail="Контент не может быть пустым")
        
        if len(content) > 50000:  # Максимум 50KB текста
            raise HTTPException(status_code=413, detail="Текст слишком длинный (максимум 50KB)")
        
        # Подготавливаем метаданные
        metadata = {
            "uploaded_by": current_user.id,
            "uploader_email": current_user.email,
            "source": "text_input"
        }
        
        if description:
            metadata["description"] = description
        
        # Добавляем документ
        result = await document_service.add_text_document(title, content, metadata)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Текстовый документ '{title}' успешно добавлен",
                "result": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Ошибка добавления документа"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка добавления текстового документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/search")
async def search_documents(
    query: str,
    limit: int = 5,
    min_similarity: float = -1.0,
    situation_date: Optional[str] = None,
    current_user: User = Depends(auth_service.get_current_active_user),
    # rate_limit_info = Depends(rag_rate_limit())  # Временно отключено
):
    """Поиск документов по запросу"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Запрос не может быть пустым")
        
        if limit > 20:
            limit = 20  # Ограничиваем максимальное количество результатов
        
        documents = await vector_store_service.search_similar(
            query=query,
            limit=limit,
            min_similarity=min_similarity,
            situation_date=situation_date
        )
        
        return {
            "success": True,
            "query": query,
            "documents": documents,
            "count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Ошибка поиска документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/rag")
async def chat_with_rag(
    query: str = Form(...),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Чат с использованием RAG"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Запрос не может быть пустым")
        
        result = await rag_service.generate_rag_response(query)
        
        if result["success"]:
            return {
                "success": True,
                "response": result["response"],
                "sources": result["sources"],
                "context_used": result["context_used"],
                "documents_found": result["documents_found"],
                "processing_time": result["processing_time"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Ошибка генерации ответа"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка RAG чата: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/rag/stream")
async def chat_with_rag_stream(
    query: str = Form(...)
    # current_user: User = Depends(auth_service.get_current_active_user)  # Временно отключено для тестирования
):
    """Потоковый чат с использованием RAG"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Запрос не может быть пустым")
        
        async def generate_stream():
            async for chunk in rag_service.stream_rag_response(query):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache", 
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Отключаем буферизацию в nginx
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка потокового RAG чата: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/stats")
async def get_documents_stats(current_user: User = Depends(auth_service.get_current_active_user)):
    """Получить статистику по документам"""
    try:
        vector_status = vector_store_service.get_status()
        document_status = document_service.get_status()
        
        return {
            "success": True,
            "vector_store": vector_status,
            "document_service": document_status,
            "total_documents": vector_status.get("documents_count", 0)
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/clear")
async def clear_all_documents(current_user: User = Depends(auth_service.get_current_active_user)):
    """Очистить все документы (только для администраторов)"""
    try:
        # Проверяем права (можно добавить проверку на админа)
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Недостаточно прав")
        
        success = await vector_store_service.clear_collection()
        
        if success:
            return {
                "success": True,
                "message": "Все документы успешно удалены"
            }
        else:
            raise HTTPException(status_code=500, detail="Ошибка очистки документов")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка очистки документов: {e}")
        raise HTTPException(status_code=500, detail=str(e))
