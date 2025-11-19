"""
Сервис для работы с векторной базой данных (ChromaDB)
Хранит и индексирует документы для RAG системы
"""

import logging
import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Any, Optional, Tuple, Union
import uuid
import json
from datetime import datetime, date
from ..core.date_utils import DateUtils

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Сервис для работы с векторной базой данных"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.collection_name = os.getenv("CHROMA_COLLECTION_NAME", "legal_documents")
        # Используем относительный путь от корня проекта
        self.db_path = os.getenv("CHROMA_DB_PATH", os.path.join(os.getcwd(), "data", "chroma_db"))
        self.is_initialized = False
        # НЕ инициализируем при создании - только при первом использовании
        
    def _check_schema_compatibility(self) -> bool:
        """Проверяет совместимость схемы ChromaDB"""
        try:
            import sqlite3
            sqlite_path = os.path.join(self.db_path, "chroma.sqlite3")
            
            if not os.path.exists(sqlite_path):
                # Новая база данных - схема будет создана автоматически
                logger.info("📁 База данных ChromaDB не существует - будет создана новая")
                return True
                
            with sqlite3.connect(sqlite_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем наличие таблицы collections
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='collections'")
                if not cursor.fetchone():
                    logger.info("📋 Таблица collections не существует - будет создана")
                    return True  # Таблица не существует - будет создана
                
                # Проверяем наличие колонки topic в таблице collections
                cursor.execute("PRAGMA table_info(collections)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'topic' not in columns:
                    logger.warning("⚠️ Обнаружена несовместимость схемы ChromaDB: отсутствует колонка 'topic'")
                    return False
                
                logger.info("✅ Схема ChromaDB совместима")
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ Не удалось проверить схему ChromaDB: {e}")
            return True  # Продолжаем инициализацию
    
    def _migrate_schema_if_needed(self) -> bool:
        """Выполняет миграцию схемы если необходимо"""
        try:
            if self._check_schema_compatibility():
                return True
                
            logger.info("🔄 Выполняем миграцию схемы ChromaDB...")
            
            # Импортируем и запускаем миграцию
            import subprocess
            import sys
            
            migration_script = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "scripts", "chromadb_migration.py"
            )
            
            if os.path.exists(migration_script):
                result = subprocess.run([
                    sys.executable, migration_script, 
                    "--db-path", self.db_path,
                    "--force"
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("✅ Миграция схемы ChromaDB выполнена успешно")
                    return True
                else:
                    logger.error(f"❌ Ошибка миграции схемы: {result.stderr}")
                    return False
            else:
                logger.error(f"❌ Скрипт миграции не найден: {migration_script}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при миграции схемы: {e}")
            return False

    def initialize(self):
        """Инициализация ChromaDB"""
        try:
            # Создаем папку для базы данных
            os.makedirs(self.db_path, exist_ok=True)
            
            logger.info(f"🚀 Инициализируем ChromaDB в {self.db_path}")
            
            # Проверяем и мигрируем схему если необходимо
            if not self._migrate_schema_if_needed():
                logger.error("❌ Не удалось выполнить миграцию схемы ChromaDB")
                self.is_initialized = False
                return
            
            # Создаем клиент ChromaDB
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Получаем или создаем коллекцию
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"✅ Найдена существующая коллекция: {self.collection_name}")
                # Проверяем, есть ли embedding function у существующей коллекции
                # Если коллекция была создана без embedding function, ChromaDB требует embeddings при добавлении
            except Exception:
                # Используем встроенную embedding function ChromaDB
                try:
                    from chromadb.utils import embedding_functions
                    default_ef = embedding_functions.DefaultEmbeddingFunction()
                    logger.info("✅ Используем DefaultEmbeddingFunction для новой коллекции")
                except (ImportError, AttributeError) as e:
                    # Если не удалось импортировать, используем None
                    default_ef = None
                    logger.warning(f"⚠️ DefaultEmbeddingFunction не доступна ({e}), коллекция будет создана без embedding function")
                
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Коллекция юридических документов для RAG"},
                    embedding_function=default_ef
                )
                logger.info(f"✅ Создана новая коллекция: {self.collection_name}")
            
            self.is_initialized = True
            logger.info("✅ ChromaDB успешно инициализирована")
            
            # Проверяем количество документов
            try:
                count = self.collection.count()
                logger.info(f"📊 В коллекции {count} документов")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось получить количество документов: {e}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации ChromaDB: {e}")
            logger.error(f"Возможные причины:")
            logger.error(f"  1. Несовместимость версий ChromaDB")
            logger.error(f"  2. Поврежденная база данных")
            logger.error(f"  3. Проблемы с правами доступа")
            logger.error(f"Попробуйте запустить миграцию: python scripts/chromadb_migration.py")
            self.is_initialized = False
    
    def is_ready(self) -> bool:
        """Проверяет, готова ли база данных к работе"""
        return self.is_initialized and self.client is not None and self.collection is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус сервиса"""
        count = 0
        if self.is_ready():
            try:
                count = self.collection.count()
            except:
                count = 0
                
        return {
            "initialized": self.is_initialized,
            "db_path": self.db_path,
            "collection_name": self.collection_name,
            "documents_count": count
        }
    
    def _validate_embedding(self, embedding) -> list:
        """Validates embedding data before storing"""
        import numpy as np
        
        if embedding is None:
            raise ValueError("Embedding cannot be None")
            
        try:
            # Convert to numpy array for validation
            arr = np.asarray(embedding, dtype=float)
            
            # Check dimensions
            if arr.ndim != 1:
                raise ValueError(f"Embedding must be 1-dimensional, got {arr.ndim}D")
                
            # Check for invalid values
            if np.isnan(arr).any():
                raise ValueError("Embedding contains NaN values")
                
            if np.isinf(arr).any():
                raise ValueError("Embedding contains infinite values")
                
            # Check reasonable size (typical embeddings are 384-1536 dimensions)
            if len(arr) < 50 or len(arr) > 5000:
                raise ValueError(f"Embedding dimension {len(arr)} seems unreasonable")
                
            return arr.tolist()
            
        except (ValueError, TypeError) as e:
            logger.error(f"Embedding validation failed: {e}")
            raise ValueError(f"Invalid embedding data: {e}")
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validates and sanitizes metadata"""
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")
            
        # Allowed metadata keys to prevent injection
        ALLOWED_KEYS = {
            "source", "article", "valid_from", "valid_to", "edition",
            "title", "filename", "content_length", "added_at", "part", "item",
            # Ключи для группировки документов и чанков
            "document_id", "chunk_index", "chunk_length", "is_chunk",
            # Ключи для кодексов
            "codex_name", "document_name", "document_type", "type",
            # Дополнительные метаданные
            "file_size", "size", "file_hash", "file_extension", "processed_at",
            "chunks_count", "total_length", "validation_confidence", "legal_score",
            "is_validated", "version", "status", "is_draft", "pages",
            "source_path", "language", "method_used", "upload_date"
        }
        
        sanitized = {}
        for key, value in metadata.items():
            if key in ALLOWED_KEYS:
                # Ensure values are safe types
                if isinstance(value, (str, int, float, bool, type(None))):
                    sanitized[key] = value
                else:
                    sanitized[key] = str(value)
                    
        return sanitized 
    def add_document(self, 
                    content: str, 
                    metadata: Dict[str, Any],
                    document_id: Optional[str] = None,
                    embedding: Optional[List[float]] = None) -> bool:
        """Добавляет документ в векторную базу данных"""
        # Инициализируем только при первом использовании
        if not self.is_ready():
            logger.info("🔄 Vector store не инициализирован, инициализируем по требованию...")
            self.initialize()
        
        if not self.is_ready():
            logger.warning("VectorStore не готов")
            return False
            
        try:
            # Validate inputs
            if not content or not content.strip():
                raise ValueError("Document content cannot be empty")
                
            # Validate and sanitize metadata
            sanitized_metadata = self._validate_metadata(metadata)
            
            # Validate embedding if provided
            if embedding is not None:
                validated_embedding = self._validate_embedding(embedding)
            else:
                validated_embedding = None
            
            # Генерируем ID если не предоставлен
            if not document_id:
                document_id = str(uuid.uuid4())
            
            # Добавляем метаданные
            sanitized_metadata.update({
                "added_at": datetime.now().isoformat(),
                "content_length": len(content)
            })
            
            # Добавляем документ в коллекцию
            if validated_embedding:
                self.collection.add(
                    documents=[content],
                    metadatas=[sanitized_metadata],
                    ids=[document_id],
                    embeddings=[validated_embedding]
                )
            else:
                self.collection.add(
                    documents=[content],
                    metadatas=[sanitized_metadata],
                    ids=[document_id]
                )
            
            logger.info(f"✅ Документ добавлен: {document_id} (длина: {len(content)} символов)")
            return True
            
        except ValueError as e:
            logger.error(f"❌ Ошибка валидации при добавлении документа: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка добавления документа: {e}")
            return False
    
    async def add_documents(self, 
                           documents: List[Dict[str, Any]]) -> int:
        """Добавляет несколько документов в базу данных"""
        if not self.is_ready():
            logger.warning("VectorStore не готов")
            return 0
            
        added_count = 0
        for doc in documents:
            success = await self.add_document(
                content=doc.get("content", ""),
                metadata=doc.get("metadata", {}),
                document_id=doc.get("id")
            )
            if success:
                added_count += 1
                
        logger.info(f"✅ Добавлено документов: {added_count}/{len(documents)}")
        return added_count
    
    async def search_similar(self, 
                           query: str, 
                           limit: int = 5,
                           min_similarity: float = 0.5,
                           situation_date: Optional[Union[str, date, datetime]] = None) -> List[Dict[str, Any]]:
        """Ищет похожие документы по запросу"""
        if not self.is_ready():
            logger.warning("VectorStore не готов")
            return []
            
        try:
            # Create date filter if situation_date is provided
            where_filter = None
            if situation_date:
                where_filter = DateUtils.create_date_filter(situation_date)
                logger.info(f"📅 Применяем фильтр по дате: {situation_date} -> {where_filter}")
            
            logger.info(f"🔍 Выполняем поиск: '{query[:50]}...' (limit={limit}, min_similarity={min_similarity})")
            
            # Выполняем поиск с учетом фильтра по дате
            search_kwargs = {
                "query_texts": [query],
                "n_results": limit,
                "include": ['documents', 'metadatas', 'distances']
            }
            
            if where_filter:
                search_kwargs["where"] = where_filter
                
            results = self.collection.query(**search_kwargs)
            
            logger.info(f"📊 Результаты поиска: {len(results.get('documents', [[]])[0])} документов найдено")
            
            # Обрабатываем результаты
            documents = []
            if results['documents'] and len(results['documents']) > 0:
                docs = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                distances = results['distances'][0] if results['distances'] else []
                
                logger.info(f"📋 Обрабатываем {len(docs)} документов, {len(metadatas)} метаданных, {len(distances)} расстояний")
                
                for i, content in enumerate(docs):
                    # ChromaDB возвращает расстояние (чем меньше, тем лучше)
                    # Конвертируем в сходство (чем больше, тем лучше)
                    distance = distances[i] if i < len(distances) else 1.0
                    # Для косинусного расстояния: similarity = 1 - distance
                    # Но ChromaDB может возвращать различные типы расстояний
                    # Используем более безопасное преобразование
                    if distance <= 1.0:
                        similarity = 1.0 - distance
                    else:
                        # Для евклидова расстояния используем другую формулу
                        similarity = 1.0 / (1.0 + distance)
                    
                    logger.info(f"📄 Документ {i+1}: similarity={similarity:.3f}, distance={distance:.3f}, content_length={len(content)}")
                    
                    if similarity >= min_similarity:
                        documents.append({
                            "content": content,
                            "metadata": metadatas[i] if i < len(metadatas) else {},
                            "similarity": similarity,
                            "distance": distance
                        })
                        logger.info(f"✅ Документ {i+1} прошел фильтр по сходству")
                    else:
                        logger.info(f"❌ Документ {i+1} не прошел фильтр по сходству (similarity={similarity:.3f} < {min_similarity})")
            
            logger.info(f"🔍 Итоговый результат: {len(documents)} документов после фильтрации")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return []
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Получает документ по ID"""
        if not self.is_ready():
            logger.warning("VectorStore не готов")
            return None
            
        try:
            results = self.collection.get(
                ids=[document_id],
                include=['documents', 'metadatas']
            )
            
            if results['documents'] and len(results['documents']) > 0:
                return {
                    "id": document_id,
                    "content": results['documents'][0],
                    "metadata": results['metadatas'][0] if results['metadatas'] else {}
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения документа {document_id}: {e}")
            
        return None
    
    async def delete_document(self, document_id: str) -> bool:
        """Удаляет документ по ID"""
        if not self.is_ready():
            logger.warning("VectorStore не готов")
            return False
            
        try:
            self.collection.delete(ids=[document_id])
            logger.info(f"🗑️ Документ удален: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления документа {document_id}: {e}")
            return False
    
    async def clear_collection(self) -> bool:
        """Очищает всю коллекцию"""
        if not self.is_ready():
            logger.warning("VectorStore не готов")
            return False
            
        try:
            # Удаляем коллекцию и создаем новую
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Коллекция юридических документов для RAG"}
            )
            logger.info("🗑️ Коллекция очищена")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки коллекции: {e}")
            return False

# Глобальный экземпляр сервиса
vector_store_service = VectorStoreService()
