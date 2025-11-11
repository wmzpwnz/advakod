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

def determine_document_type(file_name: str, document_id: str, text_content: str = "") -> str:
    """
    Определяет тип документа на основе имени файла, ID и содержимого
    
    Типы:
    - codex: кодекс
    - federal_law: федеральный закон
    - supreme_court_resolution: постановление Верховного суда
    - resolution: постановление
    - decree: указ
    - order: приказ
    - other: другое
    """
    file_name_lower = file_name.lower()
    doc_id_lower = document_id.lower()
    text_lower = text_content.lower()[:5000] if text_content else ""  # Первые 5000 символов для анализа
    
    # Кодексы - по префиксу или имени файла
    if doc_id_lower.startswith('codex_') or 'кодекс' in file_name_lower:
        return "codex"
    
    # Анализ содержимого для PDF и других документов
    if text_lower:
        # Постановление Верховного суда
        if ('постановление' in text_lower and 
            ('верховн' in text_lower or 'верховного суда' in text_lower or 'вс рф' in text_lower)):
            return "supreme_court_resolution"
        
        # Федеральный закон
        if ('федеральный закон' in text_lower or 
            'фз' in text_lower or 
            'федеральный закон рф' in text_lower):
            return "federal_law"
        
        # Постановление (общее)
        if 'постановление' in text_lower:
            return "resolution"
        
        # Указ
        if 'указ' in text_lower and ('президента' in text_lower or 'президент' in text_lower):
            return "decree"
        
        # Приказ
        if 'приказ' in text_lower:
            return "order"
    
    # По умолчанию - другое
    return "other"

class VectorStoreService:
    """Сервис для работы с векторной базой данных"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.collection_name = os.getenv("CHROMA_COLLECTION_NAME", "legal_documents")
        # Используем относительный путь от корня проекта
        self.db_path = os.getenv("CHROMA_DB_PATH", os.path.join(os.getcwd(), "backend", "data", "chroma_db"))
        self.is_initialized = False
        # НЕ инициализируем при создании - только при первом использовании
        
        # Настройки гибридной классификации
        self.use_ai_classification = os.getenv("USE_AI_CLASSIFICATION", "true").lower() == "true"
        self._classification_cache = {}  # Кэш для результатов классификации
        self._ai_classifier = None  # Ленивая загрузка AI-классификатора
        
    def initialize(self):
        """Инициализация ChromaDB"""
        try:
            # Создаем папку для базы данных
            os.makedirs(self.db_path, exist_ok=True)
            
            logger.info(f"🚀 Инициализируем ChromaDB в {self.db_path}")
            
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
            except Exception:
                # Для версии 0.4.18 используем DefaultEmbeddingFunction
                try:
                    from chromadb.utils import embedding_functions
                    default_ef = embedding_functions.DefaultEmbeddingFunction()
                except ImportError:
                    # Если не доступно, используем None (для новых версий)
                    default_ef = None
                
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
            "title", "filename", "file_name", "file_path", "content_length", "added_at", 
            "part", "item", "document_type", "document_id", "chunk_index",
            "start_position", "end_position", "chunk_length", "total_chunks",
            "processing_timestamp", "source_type", "text_length"
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
            
            # Определяем тип документа, если не указан (гибридный подход)
            if "document_type" not in sanitized_metadata:
                file_name = sanitized_metadata.get("file_name", sanitized_metadata.get("filename", ""))
                doc_type = self._determine_document_type_hybrid(
                    file_name=file_name,
                    document_id=document_id,
                    text_content=content
                )
                sanitized_metadata["document_type"] = doc_type
            
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
                    similarity = 1.0 - distance  # Приблизительное преобразование
                    
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
            try:
                from chromadb.utils import embedding_functions
                default_ef = embedding_functions.DefaultEmbeddingFunction()
            except ImportError:
                default_ef = None
            
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Коллекция юридических документов для RAG"},
                embedding_function=default_ef
            )
            logger.info("🗑️ Коллекция очищена")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки коллекции: {e}")
            return False
    
    def _determine_document_type_hybrid(
        self,
        file_name: str,
        document_id: str,
        text_content: str = ""
    ) -> str:
        """
        Гибридный подход к определению типа документа:
        1. Сначала правило-основанная проверка (быстро)
        2. Если не уверены (other) → используем AI (точно)
        3. Кэшируем результаты
        """
        # Проверяем кэш
        cache_key = f"{document_id}:{file_name}"
        if cache_key in self._classification_cache:
            return self._classification_cache[cache_key]
        
        # Шаг 1: Правило-основанная проверка (быстро)
        rule_type = determine_document_type(file_name, document_id, text_content)
        
        # Шаг 2: Если уверены - возвращаем сразу и кэшируем
        if rule_type != 'other' and (
            document_id.startswith('codex_') or 
            'кодекс' in file_name.lower() or
            ('федеральный закон' in text_content.lower()[:1000] if text_content else False) or
            ('фз' in text_content.lower()[:500] if text_content else False)
        ):
            self._classification_cache[cache_key] = rule_type
            return rule_type
        
        # Шаг 3: Если не уверены (other) и AI включен - используем AI
        if rule_type == 'other' and self.use_ai_classification and text_content:
            try:
                # Ленивая загрузка AI-классификатора
                if self._ai_classifier is None:
                    try:
                        from .ai_document_classifier import ai_document_classifier
                        self._ai_classifier = ai_document_classifier
                    except ImportError:
                        logger.warning("AI-классификатор недоступен, используем rule-based")
                        self.use_ai_classification = False
                        self._classification_cache[cache_key] = rule_type
                        return rule_type
                
                # Используем AI (синхронная версия для совместимости)
                try:
                    from .ai_document_classifier import classify_document_with_ai_sync
                    ai_type = classify_document_with_ai_sync(
                        text_content[:2000],  # Первые 2000 символов для анализа
                        file_name,
                        document_id
                    )
                    
                    if ai_type != 'other':
                        logger.info(f"✅ AI определил тип: {ai_type} (было: {rule_type})")
                        self._classification_cache[cache_key] = ai_type
                        return ai_type
                except Exception as e:
                    logger.debug(f"⚠️ AI-классификация недоступна для этого документа: {e}")
            
            except Exception as e:
                logger.warning(f"⚠️ AI-классификация недоступна: {e}")
        
        # Возвращаем rule-based результат и кэшируем
        self._classification_cache[cache_key] = rule_type
        return rule_type

# Глобальный экземпляр сервиса
vector_store_service = VectorStoreService()
