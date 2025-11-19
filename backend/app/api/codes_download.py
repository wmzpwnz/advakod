"""
API endpoints для работы с кодексами
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List
import logging
from datetime import datetime

from ..services.codes_downloader import CodesDownloader
from ..services.codes_rag_integration import CodesRAGIntegration
from ..services.codes_monitor import CodesMonitor
from ..services.hybrid_codes_downloader import HybridCodesDownloader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/codes", tags=["codes"])

# Инициализация сервисов
downloader = CodesDownloader()
rag_integration = CodesRAGIntegration()
monitor = CodesMonitor()
hybrid_downloader = None  # Инициализируется при первом использовании

@router.get("/list")
async def get_codes_list():
    """Получает список доступных кодексов"""
    try:
        return {
            "codexes": list(downloader.codexes.keys()),
            "total_count": len(downloader.codexes)
        }
    except Exception as e:
        logger.error(f"Ошибка получения списка кодексов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download")
async def start_codes_download(background_tasks: BackgroundTasks):
    """Запускает скачивание кодексов в фоновом режиме"""
    try:
        background_tasks.add_task(downloader.download_all_codexes)
        return {"message": "Скачивание кодексов запущено в фоновом режиме"}
    except Exception as e:
        logger.error(f"Ошибка запуска скачивания: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_codes_status():
    """Получает статус скачанных кодексов"""
    try:
        status = downloader.get_status()
        return status
    except Exception as e:
        logger.error(f"Ошибка получения статуса: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/integrate")
async def start_codes_integration(background_tasks: BackgroundTasks):
    """Запускает интеграцию кодексов с RAG системой"""
    try:
        background_tasks.add_task(rag_integration.integrate_all_codexes)
        return {"message": "Интеграция кодексов запущена в фоновом режиме"}
    except Exception as e:
        logger.error(f"Ошибка запуска интеграции: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integration-status")
async def get_integration_status():
    """Получает статус интеграции кодексов"""
    try:
        status = rag_integration.get_integration_status()
        return status
    except Exception as e:
        logger.error(f"Ошибка получения статуса интеграции: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitor")
async def get_system_monitor():
    """Получает общий статус системы кодексов"""
    try:
        status = monitor.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Ошибка получения статуса мониторинга: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_system_alerts():
    """Получает алерты системы"""
    try:
        alerts = monitor.check_system_alerts()
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        logger.error(f"Ошибка получения алертов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/download")
async def get_download_history(days: int = 7):
    """Получает историю скачиваний"""
    try:
        history = monitor.get_download_history(days)
        return {"history": history, "days": days}
    except Exception as e:
        logger.error(f"Ошибка получения истории скачиваний: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/integration")
async def get_integration_history(days: int = 7):
    """Получает историю интеграций"""
    try:
        history = monitor.get_integration_history(days)
        return {"history": history, "days": days}
    except Exception as e:
        logger.error(f"Ошибка получения истории интеграций: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ГИБРИДНЫЙ ЗАГРУЗЧИК ====================

@router.post("/hybrid/download")
async def start_hybrid_download(background_tasks: BackgroundTasks):
    """Запускает гибридную загрузку кодексов (PDF через API + HTML парсинг) с автоматической интеграцией в RAG"""
    try:
        async def run_hybrid_download_async():
            """Async функция для загрузки и интеграции"""
            try:
                from ..services.document_service import document_service
                from pathlib import Path
                
                # ШАГ 1: Загружаем все кодексы
                async with HybridCodesDownloader() as downloader:
                    download_result = await downloader.download_all_codexes()
                
                logger.info("📚 Загрузка кодексов завершена, начинаем интеграцию в RAG...")
                
                # ШАГ 2: Интегрируем все загруженные файлы в RAG с разбиением на чанки
                codes_dir = downloader.output_dir
                integration_results = []
                total_chunks = 0
                
                # Ищем все загруженные файлы
                txt_files = list(codes_dir.glob("*.txt"))
                pdf_files = list(codes_dir.glob("*.pdf"))
                all_files = txt_files + pdf_files
                
                logger.info(f"📁 Найдено файлов для интеграции: {len(all_files)}")
                
                for file_path in all_files:
                    try:
                        # Определяем название кодекса из имени файла
                        codex_name = file_path.stem.replace('_', ' ')
                        
                        # Подготавливаем метаданные
                        file_size = file_path.stat().st_size
                        metadata = {
                            'codex_name': codex_name,
                            'document_name': codex_name,
                            'source_path': str(file_path),
                            'size': file_size,
                            'file_size': file_size,
                            'type': 'legal_document',
                            'language': 'ru',
                            'method_used': 'hybrid_download',
                            'upload_date': datetime.now().isoformat(),
                            'added_at': datetime.now().isoformat(),
                            'document_type': 'codex'
                        }
                        
                        # Интегрируем в RAG с разбиением на чанки
                        logger.info(f"📚 Интегрируем в RAG: {file_path.name}")
                        process_result = await document_service.process_file(
                            str(file_path),
                            metadata=metadata
                        )
                        
                        if process_result.get("success", False):
                            chunks_count = process_result.get("chunks_count", 0)
                            total_chunks += chunks_count
                            integration_results.append({
                                "file": file_path.name,
                                "success": True,
                                "chunks_count": chunks_count
                            })
                            logger.info(f"✅ Интегрирован: {file_path.name} ({chunks_count} чанков)")
                        else:
                            error_msg = process_result.get("error", "Неизвестная ошибка")
                            integration_results.append({
                                "file": file_path.name,
                                "success": False,
                                "error": error_msg
                            })
                            logger.warning(f"⚠️ Ошибка интеграции {file_path.name}: {error_msg}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка интеграции {file_path.name}: {e}")
                        integration_results.append({
                            "file": file_path.name,
                            "success": False,
                            "error": str(e)
                        })
                
                logger.info(f"✅ Интеграция завершена: {len([r for r in integration_results if r.get('success')])}/{len(all_files)} файлов, {total_chunks} чанков")
                
                return {
                    "download": download_result,
                    "integration": {
                        "total_files": len(all_files),
                        "successful_files": len([r for r in integration_results if r.get('success')]),
                        "total_chunks": total_chunks,
                        "results": integration_results
                    }
                }
            except Exception as e:
                logger.error(f"Ошибка в фоновой загрузке: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        def run_hybrid_download_sync():
            """Синхронная обертка для background_tasks"""
            import asyncio
            try:
                # Создаем новый event loop для фоновой задачи
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(run_hybrid_download_async())
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"Ошибка в sync обертке: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Запускаем в фоне через background_tasks
        background_tasks.add_task(run_hybrid_download_sync)
        
        return {
            "message": "Гибридная загрузка кодексов запущена в фоновом режиме с автоматической интеграцией в RAG",
            "method": "hybrid",
            "description": "Использует PDF через API (быстро) + HTML парсинг (надежно) + автоматическое разбиение на чанки"
        }
    except Exception as e:
        logger.error(f"Ошибка запуска гибридной загрузки: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hybrid/download/test")
async def test_hybrid_download_one(codex_name: str = "Трудовой кодекс РФ"):
    """Тестирует гибридную загрузку на одном кодексе"""
    try:
        async with HybridCodesDownloader() as downloader:
            if codex_name not in downloader.codexes:
                return {
                    "success": False,
                    "result": {"error": f"Кодекс '{codex_name}' не найден в списке"},
                    "message": "Кодекс не найден"
                }
            
            codex_info = downloader.codexes[codex_name]
            result = await downloader.download_codex(codex_name, codex_info)
            
            # Если загрузка не удалась, формируем понятное сообщение об ошибке
            if not result.get("success", False):
                errors = result.get("errors", [])
                error_msg = "; ".join(errors) if errors else "Неизвестная ошибка"
                
                # Проверяем доступность Selenium
                from app.services.hybrid_codes_downloader import SELENIUM_AVAILABLE
                selenium_status = "недоступен" if not SELENIUM_AVAILABLE else "доступен"
                
                # Формируем детальное сообщение
                detailed_error = f"Не удалось загрузить кодекс. "
                if not SELENIUM_AVAILABLE:
                    detailed_error += "Selenium недоступен (HTML парсинг отключен). "
                if codex_info.get("eo_number"):
                    detailed_error += f"PDF API вернул ошибку для eo_number={codex_info.get('eo_number')}. "
                detailed_error += f"Детали: {error_msg}"
                
                return {
                    "success": False,
                    "result": {
                        "error": detailed_error,
                        "errors": errors,
                        "selenium_available": SELENIUM_AVAILABLE,
                        "eo_number": codex_info.get("eo_number"),
                        "html_url": codex_info.get("html_url")
                    },
                    "message": "Тест завершен с ошибкой"
                }
            
            # Автоматически загружаем файл в RAG систему после успешной загрузки
            # Используем document_service.process_file() для умного разбиения на чанки
            if result.get("success") and result.get("file_path"):
                try:
                    from ..services.document_service import document_service
                    from pathlib import Path
                    import os
                    
                    file_path = Path(result["file_path"])
                    if file_path.exists():
                        logger.info(f"📚 Загружаем файл в RAG систему с умным разбиением на чанки: {file_path}")
                        
                        # Подготавливаем метаданные
                        file_size = file_path.stat().st_size
                        metadata = {
                            'codex_name': codex_name,
                            'document_name': codex_name,
                            'source_path': str(file_path),
                            'size': file_size,
                            'file_size': file_size,
                            'type': 'legal_document',
                            'language': 'ru',
                            'method_used': result.get('method_used', 'unknown'),
                            'upload_date': datetime.now().isoformat(),
                            'added_at': datetime.now().isoformat(),
                            'document_type': 'codex'
                        }
                        
                        # Используем document_service.process_file() для умного разбиения на чанки
                        # Этот метод автоматически:
                        # 1. Извлекает текст из файла
                        # 2. Разбивает на чанки (chunk_size=1000, chunk_overlap=200)
                        # 3. Добавляет каждый чанк в ChromaDB с правильными метаданными
                        process_result = await document_service.process_file(
                            str(file_path),
                            metadata=metadata
                        )
                        
                        if process_result.get("success", False):
                            chunks_count = process_result.get("chunks_count", 0)
                            document_id = process_result.get("document_id", "unknown")
                            logger.info(f"✅ Файл успешно загружен в RAG систему: {document_id}")
                            logger.info(f"   Разбито на чанков: {chunks_count}")
                            result["rag_integrated"] = True
                            result["document_id"] = document_id
                            result["chunks_count"] = chunks_count
                        else:
                            error_msg = process_result.get("error", "Неизвестная ошибка")
                            logger.warning(f"⚠️ Не удалось загрузить файл в RAG систему: {error_msg}")
                            result["rag_integrated"] = False
                            result["rag_error"] = error_msg
                except Exception as e:
                    logger.error(f"❌ Ошибка загрузки в RAG систему: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    result["rag_integrated"] = False
                    result["rag_error"] = str(e)
            
            return {
                "success": True,
                "result": result,
                "message": "Тест завершен успешно"
            }
    except Exception as e:
        logger.error(f"Ошибка тестирования гибридной загрузки: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hybrid/status")
async def get_hybrid_status():
    """Получает статус гибридной загрузки"""
    try:
        downloader = HybridCodesDownloader()
        status = downloader.get_status()
        return {
            "status": "ready",
            "codexes_count": len(downloader.codexes),
            "codexes_list": list(downloader.codexes.keys()),
            "output_dir": str(downloader.output_dir),
            **status
        }
    except Exception as e:
        logger.error(f"Ошибка получения статуса гибридной загрузки: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hybrid/list")
async def get_hybrid_codexes_list():
    """Получает список кодексов для гибридной загрузки"""
    try:
        downloader = HybridCodesDownloader()
        codexes_info = []
        for name, info in downloader.codexes.items():
            codexes_info.append({
                "name": name,
                "html_url": info.get("html_url"),
                "eo_number": info.get("eo_number"),
                "expected_pages": info.get("expected_pages")
            })
        
        return {
            "total_count": len(codexes_info),
            "codexes": codexes_info
        }
    except Exception as e:
        logger.error(f"Ошибка получения списка кодексов: {e}")
        raise HTTPException(status_code=500, detail=str(e))



