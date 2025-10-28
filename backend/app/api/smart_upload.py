"""
API для интеллектуальной загрузки документов
"""

import asyncio
import logging
import time
from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ..services.smart_document_processor import smart_document_processor
from ..services.vector_store_service import vector_store_service
from ..core.security import validate_file_type, validate_file_size

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/smart-upload", tags=["Smart Upload"])


@router.post("/upload-document")
async def upload_document_with_analysis(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> JSONResponse:
    """
    Загружает документ с интеллектуальным анализом
    """
    try:
        # Валидация файла
        if not validate_file_type(file.filename):
            raise HTTPException(
                status_code=400, 
                detail="Неподдерживаемый тип файла. Поддерживаются: .pdf, .docx, .txt"
            )
        
        if not validate_file_size(file.size):
            raise HTTPException(
                status_code=400,
                detail="Файл слишком большой. Максимальный размер: 50MB"
            )
        
        # Читаем содержимое файла
        content = await file.read()
        
        # Конвертируем в текст (упрощенная версия)
        text_content = content.decode('utf-8', errors='ignore')
        
        logger.info(f"📁 Начинаем интеллектуальную обработку файла: {file.filename}")
        
        # Обрабатываем документ
        result = await smart_document_processor.process_document(
            file_path=file.filename,
            content=text_content
        )
        
        if result["success"]:
            # Добавляем задачу в фоновые задачи для дополнительной обработки
            background_tasks.add_task(
                post_process_document,
                file.filename,
                result["metadata"]
            )
            
            return JSONResponse({
                "success": True,
                "message": "Документ успешно загружен и проанализирован",
                "filename": file.filename,
                "processing_time": result["processing_time"],
                "chunks_created": result["chunks_count"],
                "articles_found": result["articles_count"],
                "sections_found": result["sections_count"],
                "document_type": result["metadata"]["document_type"],
                "structure_score": result["metadata"]["structure_score"]
            })
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка обработки документа: {result.get('error', 'Неизвестная ошибка')}"
            )
            
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-multiple")
async def upload_multiple_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
) -> JSONResponse:
    """
    Загружает несколько документов с анализом
    """
    results = []
    errors = []
    
    for file in files:
        try:
            # Валидация файла
            if not validate_file_type(file.filename):
                errors.append({
                    "filename": file.filename,
                    "error": "Неподдерживаемый тип файла"
                })
                continue
            
            if not validate_file_size(file.size):
                errors.append({
                    "filename": file.filename,
                    "error": "Файл слишком большой"
                })
                continue
            
            # Читаем содержимое
            content = await file.read()
            text_content = content.decode('utf-8', errors='ignore')
            
            # Обрабатываем документ
            result = await smart_document_processor.process_document(
                file_path=file.filename,
                content=text_content
            )
            
            if result["success"]:
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "chunks_created": result["chunks_count"],
                    "articles_found": result["articles_count"],
                    "document_type": result["metadata"]["document_type"]
                })
                
                # Добавляем в фоновые задачи
                background_tasks.add_task(
                    post_process_document,
                    file.filename,
                    result["metadata"]
                )
            else:
                errors.append({
                    "filename": file.filename,
                    "error": result.get("error", "Ошибка обработки")
                })
                
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return JSONResponse({
        "success": len(results) > 0,
        "processed_files": len(results),
        "total_files": len(files),
        "results": results,
        "errors": errors
    })


@router.get("/analysis-status/{filename}")
async def get_analysis_status(filename: str) -> JSONResponse:
    """
    Получает статус анализа документа
    """
    try:
        # Проверяем, есть ли документ в базе
        collection = vector_store_service.collection
        results = collection.get(
            where={"filename": filename},
            include=["metadatas"]
        )
        
        if not results["ids"]:
            return JSONResponse({
                "found": False,
                "message": "Документ не найден в базе данных"
            })
        
        # Анализируем метаданные
        metadatas = results["metadatas"]
        document_type = metadatas[0].get("document_type", "неизвестно")
        structure_score = metadatas[0].get("structure_score", 0.0)
        total_chunks = metadatas[0].get("total_chunks", 0)
        
        # Подсчитываем типы чанков
        chunk_types = {}
        for meta in metadatas:
            chunk_type = meta.get("chunk_type", "неизвестно")
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        return JSONResponse({
            "found": True,
            "filename": filename,
            "document_type": document_type,
            "structure_score": structure_score,
            "total_chunks": total_chunks,
            "chunk_types": chunk_types,
            "analysis_quality": "высокое" if structure_score > 0.7 else "среднее" if structure_score > 0.4 else "низкое"
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database-stats")
async def get_database_stats() -> JSONResponse:
    """
    Получает статистику базы данных
    """
    try:
        collection = vector_store_service.collection
        count = collection.count()
        
        if count == 0:
            return JSONResponse({
                "total_chunks": 0,
                "documents": [],
                "message": "База данных пуста"
            })
        
        # Получаем все метаданные
        results = collection.get(include=["metadatas"])
        metadatas = results["metadatas"]
        
        # Группируем по документам
        documents = {}
        for meta in metadatas:
            filename = meta.get("filename", "неизвестно")
            if filename not in documents:
                documents[filename] = {
                    "filename": filename,
                    "document_type": meta.get("document_type", "неизвестно"),
                    "structure_score": meta.get("structure_score", 0.0),
                    "chunks_count": 0,
                    "chunk_types": {}
                }
            
            documents[filename]["chunks_count"] += 1
            chunk_type = meta.get("chunk_type", "неизвестно")
            documents[filename]["chunk_types"][chunk_type] = documents[filename]["chunk_types"].get(chunk_type, 0) + 1
        
        # Подсчитываем общую статистику
        total_chunks = count
        document_count = len(documents)
        
        # Анализируем качество
        high_quality = sum(1 for doc in documents.values() if doc["structure_score"] > 0.7)
        medium_quality = sum(1 for doc in documents.values() if 0.4 <= doc["structure_score"] <= 0.7)
        low_quality = sum(1 for doc in documents.values() if doc["structure_score"] < 0.4)
        
        return JSONResponse({
            "total_chunks": total_chunks,
            "document_count": document_count,
            "documents": list(documents.values()),
            "quality_analysis": {
                "high_quality": high_quality,
                "medium_quality": medium_quality,
                "low_quality": low_quality
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/document/{filename}")
async def delete_document(filename: str) -> JSONResponse:
    """
    Удаляет документ из базы данных
    """
    try:
        collection = vector_store_service.collection
        
        # Находим все чанки документа
        results = collection.get(
            where={"filename": filename},
            include=["metadatas"]
        )
        
        if not results["ids"]:
            return JSONResponse({
                "success": False,
                "message": "Документ не найден в базе данных"
            })
        
        # Удаляем все чанки
        collection.delete(ids=results["ids"])
        
        logger.info(f"🗑️ Удален документ: {filename} ({len(results['ids'])} чанков)")
        
        return JSONResponse({
            "success": True,
            "message": f"Документ {filename} успешно удален",
            "deleted_chunks": len(results["ids"])
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка удаления документа: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def post_process_document(filename: str, metadata: Dict[str, Any]):
    """
    Дополнительная обработка документа в фоновом режиме
    """
    try:
        logger.info(f"🔄 Дополнительная обработка документа: {filename}")
        
        # Здесь можно добавить:
        # - Создание индексов
        # - Анализ связей между документами
        # - Обновление статистики
        # - Создание резюме документа
        
        # Пример: создание резюме документа
        if metadata.get("document_type") == "уголовный_кодекс":
            logger.info(f"📋 Создаем резюме УК РФ: {filename}")
            # Здесь можно добавить создание резюме
        
        logger.info(f"✅ Дополнительная обработка завершена: {filename}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка дополнительной обработки: {e}")


@router.post("/reprocess-document/{filename}")
async def reprocess_document(filename: str) -> JSONResponse:
    """
    Переобрабатывает существующий документ
    """
    try:
        # Сначала удаляем старые данные
        collection = vector_store_service.collection
        results = collection.get(
            where={"filename": filename},
            include=["metadatas"]
        )
        
        if results["ids"]:
            collection.delete(ids=results["ids"])
            logger.info(f"🗑️ Удалены старые данные для {filename}")
        
        # Здесь нужно было бы загрузить файл заново
        # Но для демонстрации просто возвращаем успех
        
        return JSONResponse({
            "success": True,
            "message": f"Документ {filename} готов к переобработке. Загрузите файл заново."
        })
        
    except Exception as e:
        logger.error(f"❌ Ошибка переобработки: {e}")
        raise HTTPException(status_code=500, detail=str(e))
