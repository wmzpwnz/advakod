"""
Сервис для интеграции кодексов с RAG системой
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json

from .document_service import DocumentService
from .vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)

class CodesRAGIntegration:
    def __init__(self, codes_dir: str = "downloaded_codexes"):
        self.codes_dir = Path(codes_dir)
        self.document_service = DocumentService()
        self.vector_store = VectorStoreService()
        
        # Директория для метаданных интеграции
        self.metadata_dir = Path("rag_integration/metadata")
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def integrate_codex(self, file_path: Path) -> Dict:
        """Интегрирует один кодекс в RAG систему"""
        try:
            logger.info(f"📄 Интеграция кодекса: {file_path.name}")
            
            # Обработка документа
            result = self.document_service.process_document(file_path)
            
            if not result['success']:
                return {
                    'success': False,
                    'error': result['error'],
                    'file': str(file_path)
                }
            
            # Добавление в векторное хранилище
            chunks = result['chunks']
            embeddings = result['embeddings']
            
            vector_result = self.vector_store.add_documents(
                documents=chunks,
                embeddings=embeddings,
                metadata={
                    'source': str(file_path),
                    'type': 'codex',
                    'processed_at': datetime.now().isoformat()
                }
            )
            
            if not vector_result['success']:
                return {
                    'success': False,
                    'error': f"Ошибка добавления в векторное хранилище: {vector_result['error']}",
                    'file': str(file_path)
                }
            
            logger.info(f"✅ Кодекс интегрирован: {file_path.name} ({len(chunks)} чанков)")
            
            return {
                'success': True,
                'file': str(file_path),
                'chunks_count': len(chunks),
                'vector_ids': vector_result['ids']
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка интеграции {file_path.name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file': str(file_path)
            }

    def integrate_all_codexes(self) -> Dict:
        """Интегрирует все кодексы в RAG систему"""
        logger.info("🔗 Начало интеграции кодексов с RAG системой")
        
        if not self.codes_dir.exists():
            return {
                'success': False,
                'error': f"Директория кодексов не найдена: {self.codes_dir}"
            }
        
        pdf_files = list(self.codes_dir.glob("*.pdf"))
        
        if not pdf_files:
            return {
                'success': False,
                'error': "PDF файлы кодексов не найдены"
            }
        
        logger.info(f"📁 Найдено {len(pdf_files)} PDF файлов")
        
        results = []
        total_chunks = 0
        successful_files = 0
        
        for file_path in pdf_files:
            result = self.integrate_codex(file_path)
            results.append(result)
            
            if result['success']:
                successful_files += 1
                total_chunks += result['chunks_count']
        
        # Сохранение отчета интеграции
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(pdf_files),
            'successful_files': successful_files,
            'total_chunks': total_chunks,
            'results': results
        }
        
        report_file = self.metadata_dir / f"integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 Отчет интеграции сохранен: {report_file}")
        
        success = successful_files > 0
        
        logger.info(f"✅ Интеграция завершена: {successful_files}/{len(pdf_files)} файлов, {total_chunks} чанков")
        
        return {
            'success': success,
            'processed_files': successful_files,
            'total_files': len(pdf_files),
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
        
        pdf_files = list(self.codes_dir.glob("*.pdf"))
        
        # Подсчет интегрированных файлов через векторное хранилище
        integrated_count = 0
        total_chunks = 0
        
        try:
            # Получаем все документы из векторного хранилища
            all_docs = self.vector_store.get_all_documents()
            
            for doc in all_docs:
                if doc.get('metadata', {}).get('type') == 'codex':
                    integrated_count += 1
                    # Подсчитываем чанки для этого документа
                    chunks = self.vector_store.search_similar(
                        query=doc.get('content', ''),
                        top_k=1000,
                        filter_metadata={'source': doc.get('metadata', {}).get('source')}
                    )
                    total_chunks += len(chunks.get('documents', []))
        
        except Exception as e:
            logger.warning(f"Не удалось получить статус интеграции: {e}")
        
        return {
            'available_files': len(pdf_files),
            'integrated_files': integrated_count,
            'total_chunks': total_chunks,
            'codes_dir': str(self.codes_dir)
        }


