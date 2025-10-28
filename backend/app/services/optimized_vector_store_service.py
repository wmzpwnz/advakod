"""
Optimized Vector Store Service - улучшенная версия сервиса для работы с векторной базой данных
Основан на vector_store_service.py с оптимизациями производительности и кэшированием
"""

import logging
import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Any, Optional, Tuple, Union
import uuid
import json
import asyncio
from datetime import datetime, date
from ..core.date_utils import DateUtils
from ..core.cache import cache_service

logger = logging.getLogger(__name__)

class OptimizedVectorStoreService:
    """Оптимизированный сервис для работы с векторной базой данных"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.collection_name = os.getenv("CHROMA_COLLECTION_NAME", "legal_documents")
        self.db_path = os.getenv("CHROMA_DB_PATH", os.path.join(os.getcwd(), "backend", "data", "chroma_db"))
        self.is_initialized = False
        
        # Кэширование для оптимизации
        self._search_cache = {}
        self._cache_ttl = 300  # 5 минут
        self._max_cache_size = 100
        
        # Статистика производительности
        self._stats = {
            "total_searches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_documents": 0,
            "average_search_time": 0.0,
            "last_search_time": 0.0
        }
        
        # Пул соединений для оптимизации
        self._connection_pool_size = 5
        self._active_connections = 0
        
    async def initialize(self):
        """Асинхронная инициализация ChromaDB с оптимизациями"""
        try:
            logger.info("🚀 Инициализация OptimizedVectorStoreService...")
            
            # Создаем папку для базы данных
            os.makedirs(self.db_path, exist_ok=True)
            
            logger.info(f"🚀 Инициализируем оптимизированный ChromaDB в {self.db_path}")
            
            # Создаем клиент ChromaDB с оптимизированными настройками
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    # Оптимизации для производительности
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.db_path
                )
            )
            
            # Получаем или создаем коллекцию
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"✅ Найдена существующая коллекция: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Оптимизированная коллекция юридических документов для RAG"},
                    embedding_function=None
                )
                logger.info(f"✅ Создана новая оптимизированная коллекция: {self.collection_name}")
            
            self.is_initialized = True
            
            # Обновляем статистику
            try:
                count = self.collection.count()
                self._stats["total_documents"] = count
                logger.info(f"📊 В оптимизированной коллекции {count} документов")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось получить количество документов: {e}")
            
            logger.info("✅ OptimizedVectorStoreService успешно инициализирован")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации OptimizedVectorStoreService: {e}")
            self.is_initialized = False
            raise
    
    def is_ready(self) -> bool:
        """Проверяет, готова ли база данных к работе"""
        return self.is_initialized and self.client is not None and self.collection is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Возвращает расширенный статус сервиса"""
        count = 0
        if self.is_ready():
            try:
                count = self.collection.count()
                self._stats["total_documents"] = count
            except:
                count = 0
                
        return {
            "initialized": self.is_initialized,
            "db_path": self.db_path,
            "collection_name": self.collection_name,
            "documents_count": count,
            "cache_size": len(self._search_cache),
            "max_cache_size": self._max_cache_size,
            "active_connections": self._active_connections,
            "stats": self._stats.copy()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Возвращает сводку производительности"""
        cache_hit_rate = 0.0
        if self._stats["total_searches"] > 0:
            cache_hit_rate = self._stats["cache_hits"] / self._stats["total_searches"]
            
        return {
            "total_searches": self._stats["total_searches"],
            "cache_hit_rate": cache_hit_rate,
            "average_search_time": self._stats["average_search_time"],
            "total_documents": self._stats["total_documents"],
            "cache_size": len(self._search_cache)
        }
    
    def _generate_cache_key(self, query: str, limit: int, min_similarity: float, situation_date: Optional[str] = None) -> str:
        """Генерирует ключ для кэширования поиска"""
        import hashlib
        key_data = f"{query}:{limit}:{min_similarity}:{situation_date or 'none'}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _clean_cache(self):
        """Очищает устаревшие записи из кэша"""
        current_time = datetime.now().timestamp()
        expired_keys = []
        
        for key, (timestamp, _) in self._search_cache.items():
            if current_time - timestamp > self._cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._search_cache[key]
        
        # Ограничиваем размер кэша
        if len(self._search_cache) > self._max_cache_size:
            # Удаляем самые старые записи
            sorted_items = sorted(self._search_cache.items(), key=lambda x: x[1][0])
            items_to_remove = len(self._search_cache) - self._max_cache_size
            for i in range(items_to_remove):
                del self._search_cache[sorted_items[i][0]]
    
    def _validate_embedding(self, embedding) -> list:
        """Validates embedding data before storing"""
        import numpy as np
        
        if embedding is None:
            raise ValueError("Embedding cannot be None")
            
        try:
            arr = np.asarray(embedding, dtype=float)
            
            if arr.ndim != 1:
                raise ValueError(f"Embedding must be 1-dimensional, got {arr.ndim}D")
                
            if np.isnan(arr).any():
                raise ValueError("Embedding contains NaN values")
                
            if np.isinf(arr).any():
                raise ValueError("Embedding contains infinite values")
                
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
            
        ALLOWED_KEYS = {
            "source", "article", "valid_from", "valid_to", "edition",
            "title", "filename", "content_length", "added_at", "part", "item"
        }
        
        sanitized = {}
        for key, value in metadata.items():
            if key in ALLOWED_KEYS:
                if isinstance(value, (str, int, float, bool, type(None))):
                    sanitized[key] = value
                else:
                    sanitized[key] = str(value)
                    
        return sanitized 
    
    async def add_document(self, 
                          content: str, 
                          metadata: Dict[str, Any],
                          document_id: Optional[str] = None,
                          embedding: Optional[List[float]] = None) -> bool:
        """Добавляет документ в векторную базу данных с оптимизациями"""
        if not self.is_ready():
            logger.info("🔄 Optimized Vector store не инициализирован, инициализируем по требованию...")
            await self.initialize()
        
        if not self.is_ready():
            logger.warning("OptimizedVectorStore не готов")
            return False
            
        try:
            # Validate inputs
            if not content or not content.strip():
                raise ValueError("Document content cannot be empty")
                
            sanitized_metadata = self._validate_metadata(metadata)
            
            if embedding is not None:
                validated_embedding = self._validate_embedding(embedding)
            else:
                validated_embedding = None
            
            if not document_id:
                document_id = str(uuid.uuid4())
            
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
            
            # Обновляем статистику
            self._stats["total_documents"] += 1
            
            # Очищаем кэш поиска, так как добавлен новый документ
            self._search_cache.clear()
            
            logger.info(f"✅ Документ добавлен в оптимизированное хранилище: {document_id} (длина: {len(content)} символов)")
            return True
            
        except ValueError as e:
            logger.error(f"❌ Ошибка валидации при добавлении документа: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка добавления документа в оптимизированное хранилище: {e}")
            return False
    
    async def search_similar(self, 
                           query: str, 
                           limit: int = 5,
                           min_similarity: float = 0.5,
                           situation_date: Optional[Union[str, date, datetime]] = None) -> List[Dict[str, Any]]:
        """Оптимизированный поиск похожих документов с кэшированием"""
        if not self.is_ready():
            logger.warning("OptimizedVectorStore не готов")
            return []
        
        start_time = datetime.now().timestamp()
        
        try:
            # Проверяем кэш
            cache_key = self._generate_cache_key(query, limit, min_similarity, str(situation_date) if situation_date else None)
            
            # Очищаем устаревшие записи
            self._clean_cache()
            
            if cache_key in self._search_cache:
                timestamp, cached_results = self._search_cache[cache_key]
                if datetime.now().timestamp() - timestamp < self._cache_ttl:
                    self._stats["cache_hits"] += 1
                    self._stats["total_searches"] += 1
                    logger.info(f"🎯 Кэш попадание для запроса: '{query[:50]}...'")
                    return cached_results
            
            # Кэш промах - выполняем поиск
            self._stats["cache_misses"] += 1
            
            # Create date filter if situation_date is provided
            where_filter = None
            if situation_date:
                where_filter = DateUtils.create_date_filter(situation_date)
                logger.info(f"📅 Применяем фильтр по дате: {situation_date} -> {where_filter}")
            
            logger.info(f"🔍 Выполняем оптимизированный поиск: '{query[:50]}...' (limit={limit}, min_similarity={min_similarity})")
            
            # Выполняем поиск с учетом фильтра по дате
            search_kwargs = {
                "query_texts": [query],
                "n_results": limit,
                "include": ['documents', 'metadatas', 'distances']
            }
            
            if where_filter:
                search_kwargs["where"] = where_filter
                
            results = self.collection.query(**search_kwargs)
            
            logger.info(f"📊 Результаты оптимизированного поиска: {len(results.get('documents', [[]])[0])} документов найдено")
            
            # Обрабатываем результаты
            documents = []
            if results['documents'] and len(results['documents']) > 0:
                docs = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                distances = results['distances'][0] if results['distances'] else []
                
                for i, content in enumerate(docs):
                    distance = distances[i] if i < len(distances) else 1.0
                    similarity = 1.0 - distance
                    
                    if similarity >= min_similarity:
                        documents.append({
                            "content": content,
                            "metadata": metadatas[i] if i < len(metadatas) else {},
                            "similarity": similarity,
                            "distance": distance
                        })
            
            # Кэшируем результаты
            self._search_cache[cache_key] = (datetime.now().timestamp(), documents)
            
            # Обновляем статистику
            search_time = datetime.now().timestamp() - start_time
            self._stats["total_searches"] += 1
            self._stats["last_search_time"] = search_time
            
            if self._stats["total_searches"] > 0:
                total_time = self._stats["average_search_time"] * (self._stats["total_searches"] - 1)
                self._stats["average_search_time"] = (total_time + search_time) / self._stats["total_searches"]
            
            logger.info(f"🔍 Оптимизированный поиск завершен: {len(documents)} документов (время: {search_time:.3f}с)")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Ошибка оптимизированного поиска: {e}")
            return []
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Получает документ по ID с кэшированием"""
        if not self.is_ready():
            logger.warning("OptimizedVectorStore не готов")
            return None
            
        try:
            # Проверяем кэш документов
            doc_cache_key = f"doc_{document_id}"
            if doc_cache_key in self._search_cache:
                timestamp, cached_doc = self._search_cache[doc_cache_key]
                if datetime.now().timestamp() - timestamp < self._cache_ttl:
                    return cached_doc
            
            results = self.collection.get(
                ids=[document_id],
                include=['documents', 'metadatas']
            )
            
            if results['documents'] and len(results['documents']) > 0:
                doc = {
                    "id": document_id,
                    "content": results['documents'][0],
                    "metadata": results['metadatas'][0] if results['metadatas'] else {}
                }
                
                # Кэшируем документ
                self._search_cache[doc_cache_key] = (datetime.now().timestamp(), doc)
                return doc
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения документа {document_id}: {e}")
            
        return None
    
    async def delete_document(self, document_id: str) -> bool:
        """Удаляет документ по ID"""
        if not self.is_ready():
            logger.warning("OptimizedVectorStore не готов")
            return False
            
        try:
            self.collection.delete(ids=[document_id])
            
            # Обновляем статистику
            self._stats["total_documents"] = max(0, self._stats["total_documents"] - 1)
            
            # Очищаем кэш
            self._search_cache.clear()
            
            logger.info(f"🗑️ Документ удален из оптимизированного хранилища: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка удаления документа {document_id}: {e}")
            return False
    
    async def clear_collection(self) -> bool:
        """Очищает всю коллекцию"""
        if not self.is_ready():
            logger.warning("OptimizedVectorStore не готов")
            return False
            
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Оптимизированная коллекция юридических документов для RAG"}
            )
            
            # Сбрасываем статистику и кэш
            self._stats["total_documents"] = 0
            self._search_cache.clear()
            
            logger.info("🗑️ Оптимизированная коллекция очищена")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки оптимизированной коллекции: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья оптимизированного сервиса"""
        return {
            "status": "healthy" if self.is_ready() else "unhealthy",
            "initialized": self.is_initialized,
            "documents_count": self._stats["total_documents"],
            "cache_size": len(self._search_cache),
            "performance": self.get_performance_summary()
        }


# Глобальный экземпляр сервиса
optimized_vector_store_service = OptimizedVectorStoreService()