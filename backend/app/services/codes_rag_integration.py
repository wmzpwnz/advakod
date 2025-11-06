"""
Сервис для интеграции кодексов с RAG системой
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json

from .document_service import DocumentService
from .vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)

class CodesRAGIntegration:
    def __init__(self, codes_dir: str = "data/codes_downloads"):
        self.codes_dir = Path(codes_dir)
        self.document_service = DocumentService()
        self.vector_store = VectorStoreService()
        
        # Директория для метаданных интеграции
        # Используем абсолютный путь внутри контейнера или /app/data
        import os
        base_dir = os.getenv("DATA_DIR", "/app/data")
        self.metadata_dir = Path(base_dir) / "rag_integration" / "metadata"
        try:
            self.metadata_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            # Если нет прав на создание, используем временную директорию
            import tempfile
            temp_base = Path(tempfile.gettempdir()) / "rag_integration" / "metadata"
            temp_base.mkdir(parents=True, exist_ok=True)
            self.metadata_dir = temp_base
            logger.warning(f"⚠️ Не удалось создать директорию в {base_dir}, используем временную: {temp_base}")

    def _load_metadata(self, file_path: Path) -> Optional[Dict]:
        """Загружает метаданные из JSON файла"""
        try:
            metadata_file = file_path.with_suffix('.json')
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить метаданные для {file_path.name}: {e}")
        return None
    
    async def integrate_codex(self, file_path: Path) -> Dict:
        """Интегрирует один кодекс в RAG систему"""
        try:
            logger.info(f"📄 Интеграция кодекса: {file_path.name}")
            
            # Загружаем метаданные из JSON файла
            metadata = self._load_metadata(file_path)
            
            # Формируем метаданные для DocumentService
            doc_metadata = {
                'source': str(file_path),
                'type': 'codex',
                'processed_at': datetime.now().isoformat()
            }
            
            # Добавляем метаданные из API если они есть
            if metadata:
                doc_metadata.update({
                    'codex_name': metadata.get('codex_name'),
                    'document_name': metadata.get('name'),
                    'document_title': metadata.get('title'),
                    'document_number': metadata.get('number'),
                    'document_date': metadata.get('document_date'),
                    'publish_date': metadata.get('publish_date'),
                    'view_date': metadata.get('view_date'),
                    'document_type': metadata.get('document_type'),
                    'pages_count': metadata.get('pages_count'),
                    'signatory_authorities': metadata.get('signatory_authorities', []),
                    'eo_number': metadata.get('eo_number'),
                    'source_url': metadata.get('source_url'),
                    'filename': metadata.get('file_name', file_path.name)
                })
            
            # Обработка документа через DocumentService.process_file (асинхронный метод)
            result = await self.document_service.process_file(
                str(file_path),
                metadata=doc_metadata
            )
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Неизвестная ошибка')
                logger.error(f"❌ Ошибка обработки документа: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'file': str(file_path)
                }
            
            # process_file уже добавляет документ в векторное хранилище
            # Проверяем результат
            document_id = result.get('document_id', '')
            chunks_count = result.get('chunks_count', 0)
            
            logger.info(f"✅ Кодекс интегрирован: {file_path.name} (ID: {document_id}, чанков: {chunks_count})")
            
            return {
                'success': True,
                'file': str(file_path),
                'document_id': document_id,
                'chunks_count': chunks_count,
                'vector_ids': result.get('vector_ids', [])
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка интеграции {file_path.name}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'file': str(file_path)
            }

    async def integrate_all_codexes(self) -> Dict:
        """Интегрирует все кодексы в RAG систему"""
        logger.info("🔗 Начало интеграции кодексов с RAG системой")
        
        if not self.codes_dir.exists():
            return {
                'success': False,
                'error': f"Директория кодексов не найдена: {self.codes_dir}"
            }
        
        # Ищем PDF, TXT и HTML файлы
        pdf_files = list(self.codes_dir.glob("*.pdf"))
        txt_files = list(self.codes_dir.glob("*.txt"))
        html_files = list(self.codes_dir.glob("*.html"))
        all_files = pdf_files + txt_files + html_files
        
        if not all_files:
            return {
                'success': False,
                'error': "Файлы кодексов не найдены (PDF/TXT/HTML)"
            }
        
        logger.info(f"📁 Найдено файлов: {len(pdf_files)} PDF, {len(txt_files)} TXT, {len(html_files)} HTML (всего: {len(all_files)})")
        
        results = []
        total_chunks = 0
        successful_files = 0
        
        # Обрабатываем файлы последовательно (чтобы не перегружать систему)
        for file_path in all_files:
            result = await self.integrate_codex(file_path)
            results.append(result)
            
            if result['success']:
                successful_files += 1
                total_chunks += result.get('chunks_count', 0)
        
        # Сохранение отчета интеграции
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(all_files),
            'pdf_files': len(pdf_files),
            'txt_files': len(txt_files),
            'html_files': len(html_files),
            'successful_files': successful_files,
            'total_chunks': total_chunks,
            'results': results
        }
        
        report_file = self.metadata_dir / f"integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 Отчет интеграции сохранен: {report_file}")
        
        success = successful_files > 0
        
        logger.info(f"✅ Интеграция завершена: {successful_files}/{len(all_files)} файлов, {total_chunks} чанков")
        
        return {
            'success': success,
            'processed_files': successful_files,
            'total_files': len(all_files),
            'total_chunks': total_chunks,
            'report_file': str(report_file),
            'results': results
        }

    def get_integration_status(self) -> Dict:
        """Возвращает статус интеграции"""
        if not self.codes_dir.exists():
            return {
                'available_files': 0,
                'integrated_files': 0,
                'total_chunks': 0
            }
        
        # Ищем PDF, TXT и HTML файлы
        pdf_files = list(self.codes_dir.glob("*.pdf"))
        txt_files = list(self.codes_dir.glob("*.txt"))
        html_files = list(self.codes_dir.glob("*.html"))
        all_files = pdf_files + txt_files + html_files
        
        # Подсчет интегрированных файлов через векторное хранилище
        integrated_count = 0
        total_chunks = 0
        
        try:
            # Проверяем наличие файлов метаданных интеграции
            metadata_dir = Path("rag_integration/metadata")
            if metadata_dir.exists():
                # Считаем файлы метаданных как интегрированные
                metadata_files = list(metadata_dir.glob("*.json"))
                integrated_count = len(metadata_files)
                
                # Подсчитываем общее количество чанков из метаданных
                for metadata_file in metadata_files:
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            total_chunks += metadata.get('total_chunks', 0)
                    except Exception:
                        pass
        
        except Exception as e:
            logger.warning(f"Не удалось получить статус интеграции: {e}")
        
        return {
            'available_files': len(all_files),
            'pdf_files': len(pdf_files),
            'txt_files': len(txt_files),
            'html_files': len(html_files),
            'integrated_files': integrated_count,
            'total_chunks': total_chunks,
            'codes_dir': str(self.codes_dir)
        }



