#!/usr/bin/env python3
"""
Интеграция скачанных кодексов с существующей RAG системой проекта
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Добавляем путь к backend для импорта модулей
sys.path.append('/root/advakod/backend')

from app.services.vector_store_service import VectorStoreService
from app.services.embeddings_service import EmbeddingsService
from app.services.document_service import DocumentService

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGIntegrationManager:
    """Менеджер интеграции с существующей RAG системой"""
    
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.embeddings_service = EmbeddingsService()
        self.document_service = DocumentService()
        
        # Пути к нашим скачанным данным
        self.chunks_dir = Path("/root/advakod/final_system/rag_integration/chunks")
        self.processed_docs_dir = Path("/root/advakod/final_system/rag_integration/processed_documents")
        
        self.integrated_count = 0
        self.failed_count = 0
        
        logger.info("✅ RAGIntegrationManager инициализирован")
    
    def initialize_services(self):
        """Инициализирует сервисы RAG системы"""
        logger.info("🚀 Инициализируем сервисы RAG системы...")
        
        # Инициализируем векторное хранилище
        self.vector_store.initialize()
        if not self.vector_store.is_ready():
            logger.error("❌ Не удалось инициализировать векторное хранилище")
            return False
        
        # Инициализируем сервис эмбеддингов
        try:
            self.embeddings_service.initialize()
            logger.info("✅ Сервис эмбеддингов инициализирован")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка инициализации сервиса эмбеддингов: {e}")
        
        logger.info("✅ Все сервисы инициализированы")
        return True
    
    def load_chunks_from_files(self):
        """Загружает чанки из JSON файлов"""
        if not self.chunks_dir.exists():
            logger.error(f"❌ Директория с чанками не найдена: {self.chunks_dir}")
            return []
        
        chunks = []
        chunk_files = list(self.chunks_dir.glob("*.json"))
        
        logger.info(f"📄 Найдено {len(chunk_files)} файлов чанков")
        
        for chunk_file in chunk_files:
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    chunk_data = json.load(f)
                    chunks.append(chunk_data)
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки чанка {chunk_file}: {e}")
                self.failed_count += 1
        
        logger.info(f"✅ Загружено {len(chunks)} чанков")
        return chunks
    
    def prepare_chunks_for_rag(self, chunks):
        """Подготавливает чанки для интеграции с RAG"""
        prepared_chunks = []
        
        for chunk in chunks:
            try:
                # Извлекаем необходимые данные
                chunk_id = chunk.get('id', '')
                text = chunk.get('text', '')
                metadata = chunk.get('metadata', {})
                
                if not text or len(text.strip()) < 10:
                    logger.warning(f"⚠️ Пропускаем чанк {chunk_id} - слишком короткий текст")
                    continue
                
                # Подготавливаем метаданные для RAG
                rag_metadata = {
                    'source': 'pravo.gov.ru',
                    'document_type': metadata.get('document_type', 'legal_document'),
                    'file_type': metadata.get('file_type', 'unknown'),
                    'file_name': metadata.get('file_name', ''),
                    'legal_score': metadata.get('legal_score', 0),
                    'is_valid': metadata.get('is_valid', False),
                    'chunk_index': metadata.get('chunk_index', 0),
                    'total_chunks': metadata.get('total_chunks', 1),
                    'processing_timestamp': metadata.get('processing_timestamp', datetime.now().isoformat()),
                    'integration_timestamp': datetime.now().isoformat()
                }
                
                prepared_chunk = {
                    'id': chunk_id,
                    'text': text,
                    'metadata': rag_metadata
                }
                
                prepared_chunks.append(prepared_chunk)
                
            except Exception as e:
                logger.error(f"❌ Ошибка подготовки чанка: {e}")
                self.failed_count += 1
        
        logger.info(f"✅ Подготовлено {len(prepared_chunks)} чанков для RAG")
        return prepared_chunks
    
    def integrate_chunks_with_vector_store(self, chunks):
        """Интегрирует чанки с векторным хранилищем"""
        logger.info("🔗 Интегрируем чанки с векторным хранилищем...")
        
        for i, chunk in enumerate(chunks, 1):
            try:
                chunk_id = chunk['id']
                text = chunk['text']
                metadata = chunk['metadata']
                
                logger.info(f"📥 Интегрируем чанк {i}/{len(chunks)}: {chunk_id}")
                
                # Генерируем эмбеддинг для чанка
                try:
                    embedding = self.embeddings_service.generate_embedding(text)
                    if embedding is None:
                        logger.warning(f"⚠️ Не удалось сгенерировать эмбеддинг для {chunk_id}")
                        continue
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка генерации эмбеддинга для {chunk_id}: {e}")
                    continue
                
                # Добавляем в векторное хранилище
                try:
                    self.vector_store.add_document(
                        document_id=chunk_id,
                        text=text,
                        embedding=embedding,
                        metadata=metadata
                    )
                    
                    self.integrated_count += 1
                    logger.info(f"✅ Чанк {chunk_id} успешно интегрирован")
                    
                except Exception as e:
                    logger.error(f"❌ Ошибка добавления чанка {chunk_id} в векторное хранилище: {e}")
                    self.failed_count += 1
                
            except Exception as e:
                logger.error(f"❌ Ошибка интеграции чанка {i}: {e}")
                self.failed_count += 1
        
        logger.info(f"🎉 Интеграция завершена: {self.integrated_count} успешно, {self.failed_count} ошибок")
    
    def create_integration_report(self):
        """Создает отчет об интеграции"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'integration_summary': {
                'total_chunks_processed': self.integrated_count + self.failed_count,
                'successfully_integrated': self.integrated_count,
                'failed_integrations': self.failed_count,
                'success_rate': (self.integrated_count / (self.integrated_count + self.failed_count) * 100) if (self.integrated_count + self.failed_count) > 0 else 0
            },
            'rag_system_status': {
                'vector_store_status': self.vector_store.get_status(),
                'embeddings_service_ready': hasattr(self.embeddings_service, 'is_ready') and self.embeddings_service.is_ready()
            },
            'source_data': {
                'chunks_directory': str(self.chunks_dir),
                'processed_documents_directory': str(self.processed_docs_dir),
                'source': 'pravo.gov.ru'
            }
        }
        
        # Сохраняем отчет
        report_file = Path("/root/advakod/rag_integration_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 Отчет интеграции сохранен: {report_file}")
        return report
    
    def run_integration(self):
        """Запускает полную интеграцию"""
        logger.info("🚀 Запуск интеграции с существующей RAG системой")
        start_time = datetime.now()
        
        try:
            # 1. Инициализируем сервисы
            if not self.initialize_services():
                return False
            
            # 2. Загружаем чанки
            chunks = self.load_chunks_from_files()
            if not chunks:
                logger.error("❌ Не удалось загрузить чанки")
                return False
            
            # 3. Подготавливаем чанки для RAG
            prepared_chunks = self.prepare_chunks_for_rag(chunks)
            if not prepared_chunks:
                logger.error("❌ Не удалось подготовить чанки")
                return False
            
            # 4. Интегрируем с векторным хранилищем
            self.integrate_chunks_with_vector_store(prepared_chunks)
            
            # 5. Создаем отчет
            report = self.create_integration_report()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("=" * 60)
            logger.info("🎉 ИНТЕГРАЦИЯ ЗАВЕРШЕНА!")
            logger.info("=" * 60)
            logger.info(f"⏱️ Время выполнения: {duration}")
            logger.info(f"📊 Обработано чанков: {report['integration_summary']['total_chunks_processed']}")
            logger.info(f"✅ Успешно интегрировано: {report['integration_summary']['successfully_integrated']}")
            logger.info(f"❌ Ошибок: {report['integration_summary']['failed_integrations']}")
            logger.info(f"📈 Процент успеха: {report['integration_summary']['success_rate']:.1f}%")
            
            return report
            
        except Exception as e:
            logger.error(f"💥 Критическая ошибка интеграции: {e}")
            return False

def main():
    """Основная функция"""
    print("🚀 Интеграция скачанных кодексов с существующей RAG системой")
    print("=" * 60)
    
    integration_manager = RAGIntegrationManager()
    report = integration_manager.run_integration()
    
    if report:
        print(f"\n📊 ИТОГОВЫЙ ОТЧЕТ ИНТЕГРАЦИИ:")
        print(f"   📄 Обработано чанков: {report['integration_summary']['total_chunks_processed']}")
        print(f"   ✅ Успешно интегрировано: {report['integration_summary']['successfully_integrated']}")
        print(f"   ❌ Ошибок: {report['integration_summary']['failed_integrations']}")
        print(f"   📈 Процент успеха: {report['integration_summary']['success_rate']:.1f}%")
        
        print(f"\n🔗 СТАТУС RAG СИСТЕМЫ:")
        vs_status = report['rag_system_status']['vector_store_status']
        print(f"   📊 Векторное хранилище: {'✅ Готово' if vs_status['initialized'] else '❌ Не готово'}")
        print(f"   📁 Путь к БД: {vs_status['db_path']}")
        print(f"   📄 Документов в коллекции: {vs_status['documents_count']}")
        
        print(f"\n🎉 Интеграция завершена! Теперь RAG система содержит скачанные кодексы.")
    else:
        print(f"\n❌ Интеграция завершилась с ошибками!")

if __name__ == "__main__":
    main()

