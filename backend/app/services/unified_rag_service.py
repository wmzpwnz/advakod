"""
Unified RAG Service - единый сервис для Retrieval-Augmented Generation
Объединяет функциональность enhanced_rag_service.py, integrated_rag_service.py, simple_expert_rag.py
"""

import logging
import time
import asyncio
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, date
import numpy as np
from functools import lru_cache

from ..core.config import settings
from ..core.cache import cache_service
from .vector_store_service import vector_store_service
from .embeddings_service import embeddings_service

logger = logging.getLogger(__name__)


@dataclass
class DocumentSource:
    """Источник документа для RAG"""
    content: str
    metadata: Dict[str, Any]
    similarity: float
    relevance: float
    source_type: str  # "semantic", "keyword", "hybrid"
    chunk_id: Optional[str] = None


@dataclass
class RAGResponse:
    """Ответ RAG системы"""
    answer: str
    sources: List[DocumentSource]
    confidence: float
    search_time: float
    generation_time: float
    total_time: float
    search_metadata: Dict[str, Any]


@dataclass
class RAGMetrics:
    """Метрики производительности RAG"""
    search_time_avg: float
    generation_time_avg: float
    cache_hit_rate: float
    vector_store_size: int
    embedding_generation_time: float
    total_searches: int
    successful_searches: int
    failed_searches: int


class SearchStrategy:
    """Стратегии поиска"""
    SEMANTIC_ONLY = "semantic_only"
    KEYWORD_ONLY = "keyword_only"
    HYBRID = "hybrid"
    AUTO = "auto"


class UnifiedRAGService:
    """Единый сервис для Retrieval-Augmented Generation"""
    
    def __init__(self):
        self.vector_store = vector_store_service
        self.embeddings_service = embeddings_service
        self.cache_service = cache_service
        
        # Настройки поиска
        self.search_config = {
            "max_results": getattr(settings, "RAG_MAX_RESULTS", 20),
            "similarity_threshold": getattr(settings, "RAG_SIMILARITY_THRESHOLD", 0.7),
            "rerank_top_k": getattr(settings, "RAG_RERANK_TOP_K", 5),
            "context_window": getattr(settings, "RAG_CONTEXT_WINDOW", 4000),
            "chunk_overlap": getattr(settings, "RAG_CHUNK_OVERLAP", 200),
            "enable_reranking": getattr(settings, "RAG_ENABLE_RERANKING", True),
            "enable_hybrid_search": getattr(settings, "RAG_ENABLE_HYBRID_SEARCH", True)
        }
        
        # Кэширование
        self._search_cache = {}
        self._cache_ttl = 300  # 5 минут
        self._max_cache_size = 200
        
        # Статистика производительности
        self._stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_search_time": 0.0,
            "average_generation_time": 0.0,
            "average_embedding_time": 0.0,
            "last_search_time": 0.0,
            "vector_store_size": 0
        }
        
        # История поиска для аналитики
        self._search_history = []
        self._max_history = 1000
        
        # Флаг инициализации
        self._initialized = False
        
        # RRF параметры для гибридного поиска
        self._rrf_k = 60  # Параметр для Reciprocal Rank Fusion
        
    async def initialize(self):
        """Асинхронная инициализация RAG сервиса"""
        try:
            logger.info("🚀 Инициализация UnifiedRAGService...")
            start_time = time.time()
            
            # Инициализируем зависимые сервисы
            if not self.vector_store.is_ready():
                await asyncio.to_thread(self.vector_store.initialize)
            
            # Проверяем embeddings service
            if not hasattr(self.embeddings_service, '_model_loaded') or not self.embeddings_service._model_loaded:
                await asyncio.to_thread(self.embeddings_service.load_model)
            
            # Обновляем статистику
            await self._update_vector_store_stats()
            
            self._initialized = True
            duration = time.time() - start_time
            
            logger.info("✅ UnifiedRAGService инициализирован успешно за %.2f секунд", duration)
            
        except Exception as e:
            logger.error("❌ Ошибка инициализации UnifiedRAGService: %s", e)
            self._initialized = False
            raise

    def is_ready(self) -> bool:
        """Проверяет готовность сервиса"""
        return (self._initialized and 
                self.vector_store.is_ready() and
                hasattr(self.embeddings_service, '_model_loaded') and 
                self.embeddings_service._model_loaded)

    async def search_and_generate(
        self,
        query: str,
        max_results: int = 10,
        similarity_threshold: float = 0.7,
        situation_date: Optional[Union[str, date, datetime]] = None,
        strategy: str = SearchStrategy.HYBRID,
        enable_reranking: bool = True,
        context_window: int = None
    ) -> RAGResponse:
        """Основной метод поиска и генерации ответа"""
        
        if not self.is_ready():
            logger.warning("UnifiedRAGService не готов к работе")
            return RAGResponse(
                answer="Сервис временно недоступен. Попробуйте позже.",
                sources=[],
                confidence=0.0,
                search_time=0.0,
                generation_time=0.0,
                total_time=0.0,
                search_metadata={"error": "service_not_ready"}
            )
        
        total_start_time = time.time()
        
        try:
            # Проверяем кэш
            cache_key = self._generate_cache_key(query, max_results, similarity_threshold, 
                                               str(situation_date), strategy)
            
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                self._stats["cache_hits"] += 1
                logger.info("🎯 Кэш попадание для RAG запроса: '%s'", query[:50])
                return cached_response
            
            self._stats["cache_misses"] += 1
            
            # 1. Поиск документов
            search_start_time = time.time()
            sources = await self._search_documents(
                query, max_results, similarity_threshold, situation_date, strategy
            )
            search_time = time.time() - search_start_time
            
            # 2. Переранжирование (если включено)
            if enable_reranking and len(sources) > 1:
                sources = await self._rerank_sources(query, sources)
            
            # 3. Построение контекста
            context_window = context_window or self.search_config["context_window"]
            context = self._build_context(sources, context_window)
            
            # 4. Генерация ответа (заглушка - в реальной системе здесь был бы вызов LLM)
            generation_start_time = time.time()
            answer = await self._generate_answer(query, context, sources)
            generation_time = time.time() - generation_start_time
            
            # 5. Расчет уверенности
            confidence = self._calculate_confidence(sources, query)
            
            total_time = time.time() - total_start_time
            
            # Создаем ответ
            response = RAGResponse(
                answer=answer,
                sources=sources[:self.search_config["rerank_top_k"]],
                confidence=confidence,
                search_time=search_time,
                generation_time=generation_time,
                total_time=total_time,
                search_metadata={
                    "strategy": strategy,
                    "total_sources": len(sources),
                    "reranking_enabled": enable_reranking,
                    "situation_date": str(situation_date) if situation_date else None
                }
            )
            
            # Кэшируем ответ
            await self._cache_response(cache_key, response)
            
            # Обновляем статистику
            self._update_search_stats(True, search_time, generation_time)
            
            # Добавляем в историю
            self._add_to_history(query, response)
            
            logger.info("✅ RAG поиск завершен: %d источников, уверенность %.2f, время %.2fs", 
                       len(sources), confidence, total_time)
            
            return response
            
        except Exception as e:
            total_time = time.time() - total_start_time
            self._update_search_stats(False, 0, 0)
            logger.error("❌ Ошибка в RAG поиске: %s", e)
            
            return RAGResponse(
                answer="Извините, произошла ошибка при поиске информации. Попробуйте переформулировать вопрос.",
                sources=[],
                confidence=0.0,
                search_time=0.0,
                generation_time=0.0,
                total_time=total_time,
                search_metadata={"error": str(e)}
            )

    async def _search_documents(
        self,
        query: str,
        max_results: int,
        similarity_threshold: float,
        situation_date: Optional[Union[str, date, datetime]],
        strategy: str
    ) -> List[DocumentSource]:
        """Поиск документов с использованием выбранной стратегии"""
        
        if strategy == SearchStrategy.SEMANTIC_ONLY:
            return await self._semantic_search(query, max_results, similarity_threshold, situation_date)
        elif strategy == SearchStrategy.KEYWORD_ONLY:
            return await self._keyword_search(query, max_results, situation_date)
        elif strategy == SearchStrategy.HYBRID:
            return await self._hybrid_search(query, max_results, similarity_threshold, situation_date)
        else:  # AUTO
            # Автоматический выбор стратегии на основе запроса
            if len(query.split()) <= 3:
                return await self._keyword_search(query, max_results, situation_date)
            else:
                return await self._hybrid_search(query, max_results, similarity_threshold, situation_date)

    async def _semantic_search(
        self,
        query: str,
        max_results: int,
        similarity_threshold: float,
        situation_date: Optional[Union[str, date, datetime]]
    ) -> List[DocumentSource]:
        """Семантический поиск через векторное хранилище"""
        
        try:
            # Получаем результаты из векторного хранилища
            results = await self.vector_store.search_similar(
                query=query,
                limit=max_results,
                min_similarity=similarity_threshold,
                situation_date=situation_date
            )
            
            sources = []
            for result in results:
                source = DocumentSource(
                    content=result["content"],
                    metadata=result["metadata"],
                    similarity=result["similarity"],
                    relevance=result["similarity"],  # Для семантического поиска similarity = relevance
                    source_type="semantic",
                    chunk_id=result["metadata"].get("chunk_id")
                )
                sources.append(source)
            
            logger.info("🔍 Семантический поиск: найдено %d документов", len(sources))
            return sources
            
        except Exception as e:
            logger.error("❌ Ошибка семантического поиска: %s", e)
            return []

    async def _keyword_search(
        self,
        query: str,
        max_results: int,
        situation_date: Optional[Union[str, date, datetime]]
    ) -> List[DocumentSource]:
        """Поиск по ключевым словам (простая реализация)"""
        
        try:
            # Простая реализация - используем семантический поиск с низким порогом
            results = await self.vector_store.search_similar(
                query=query,
                limit=max_results * 2,  # Берем больше результатов для фильтрации
                min_similarity=0.3,  # Низкий порог для keyword поиска
                situation_date=situation_date
            )
            
            # Фильтруем по наличию ключевых слов
            query_words = set(query.lower().split())
            filtered_results = []
            
            for result in results:
                content_words = set(result["content"].lower().split())
                # Проверяем пересечение ключевых слов
                word_overlap = len(query_words.intersection(content_words))
                if word_overlap > 0:
                    # Рассчитываем релевантность на основе пересечения слов
                    relevance = word_overlap / len(query_words)
                    
                    source = DocumentSource(
                        content=result["content"],
                        metadata=result["metadata"],
                        similarity=result["similarity"],
                        relevance=relevance,
                        source_type="keyword",
                        chunk_id=result["metadata"].get("chunk_id")
                    )
                    filtered_results.append(source)
            
            # Сортируем по релевантности и ограничиваем количество
            filtered_results.sort(key=lambda x: x.relevance, reverse=True)
            final_results = filtered_results[:max_results]
            
            logger.info("🔍 Поиск по ключевым словам: найдено %d документов", len(final_results))
            return final_results
            
        except Exception as e:
            logger.error("❌ Ошибка поиска по ключевым словам: %s", e)
            return []

    async def _hybrid_search(
        self,
        query: str,
        max_results: int,
        similarity_threshold: float,
        situation_date: Optional[Union[str, date, datetime]]
    ) -> List[DocumentSource]:
        """Гибридный поиск с использованием RRF (Reciprocal Rank Fusion)"""
        
        try:
            # Выполняем оба типа поиска параллельно
            semantic_task = self._semantic_search(query, max_results, similarity_threshold, situation_date)
            keyword_task = self._keyword_search(query, max_results, situation_date)
            
            semantic_results, keyword_results = await asyncio.gather(semantic_task, keyword_task)
            
            # Применяем RRF для объединения результатов
            combined_results = self._apply_rrf(semantic_results, keyword_results)
            
            # Ограничиваем количество результатов
            final_results = combined_results[:max_results]
            
            logger.info("🔍 Гибридный поиск: семантический=%d, ключевые слова=%d, итого=%d", 
                       len(semantic_results), len(keyword_results), len(final_results))
            
            return final_results
            
        except Exception as e:
            logger.error("❌ Ошибка гибридного поиска: %s", e)
            # Fallback на семантический поиск
            return await self._semantic_search(query, max_results, similarity_threshold, situation_date)

    def _apply_rrf(self, semantic_results: List[DocumentSource], keyword_results: List[DocumentSource]) -> List[DocumentSource]:
        """Применяет Reciprocal Rank Fusion для объединения результатов"""
        
        # Создаем словарь для объединения результатов по содержимому
        combined_scores = {}
        
        # Обрабатываем семантические результаты
        for rank, source in enumerate(semantic_results, 1):
            content_hash = hashlib.md5(source.content.encode()).hexdigest()
            if content_hash not in combined_scores:
                combined_scores[content_hash] = {
                    "source": source,
                    "rrf_score": 0.0
                }
            combined_scores[content_hash]["rrf_score"] += 1.0 / (self._rrf_k + rank)
        
        # Обрабатываем результаты по ключевым словам
        for rank, source in enumerate(keyword_results, 1):
            content_hash = hashlib.md5(source.content.encode()).hexdigest()
            if content_hash not in combined_scores:
                combined_scores[content_hash] = {
                    "source": source,
                    "rrf_score": 0.0
                }
            combined_scores[content_hash]["rrf_score"] += 1.0 / (self._rrf_k + rank)
        
        # Создаем финальный список с обновленными источниками
        final_results = []
        for item in combined_scores.values():
            source = item["source"]
            # Обновляем тип источника и релевантность
            source.source_type = "hybrid"
            source.relevance = item["rrf_score"]
            final_results.append(source)
        
        # Сортируем по RRF score
        final_results.sort(key=lambda x: x.relevance, reverse=True)
        
        return final_results

    async def _rerank_sources(self, query: str, sources: List[DocumentSource]) -> List[DocumentSource]:
        """Переранжирование источников (простая реализация)"""
        
        try:
            # Простое переранжирование на основе длины пересечения с запросом
            query_words = set(query.lower().split())
            
            for source in sources:
                content_words = set(source.content.lower().split())
                word_overlap = len(query_words.intersection(content_words))
                
                # Комбинируем исходную релевантность с пересечением слов
                rerank_score = (source.relevance * 0.7) + (word_overlap / len(query_words) * 0.3)
                source.relevance = rerank_score
            
            # Пересортировываем
            sources.sort(key=lambda x: x.relevance, reverse=True)
            
            logger.info("🔄 Переранжирование завершено для %d источников", len(sources))
            return sources
            
        except Exception as e:
            logger.error("❌ Ошибка переранжирования: %s", e)
            return sources

    def _build_context(self, sources: List[DocumentSource], max_length: int) -> str:
        """Строит контекст из найденных источников"""
        
        context_parts = []
        current_length = 0
        
        for i, source in enumerate(sources):
            # Добавляем заголовок источника
            source_header = f"\n=== ИСТОЧНИК {i+1} ===\n"
            source_text = source_header + source.content + "\n"
            
            # Проверяем, не превышаем ли лимит
            if current_length + len(source_text) > max_length:
                # Обрезаем последний источник, если нужно
                remaining_space = max_length - current_length - len(source_header)
                if remaining_space > 100:  # Минимум 100 символов для осмысленного текста
                    truncated_content = source.content[:remaining_space] + "..."
                    context_parts.append(source_header + truncated_content)
                break
            
            context_parts.append(source_text)
            current_length += len(source_text)
        
        context = "".join(context_parts)
        logger.info("📝 Построен контекст длиной %d символов из %d источников", 
                   len(context), len(context_parts))
        
        return context

    async def _generate_answer(self, query: str, context: str, sources: List[DocumentSource]) -> str:
        """Генерирует ответ на основе контекста (заглушка)"""
        
        # В реальной реализации здесь был бы вызов LLM
        # Пока возвращаем простой ответ на основе найденных источников
        
        if not sources:
            return "К сожалению, не удалось найти релевантную информацию по вашему запросу. Попробуйте переформулировать вопрос или обратитесь к специалисту."
        
        # Простая генерация ответа на основе метаданных источников
        answer_parts = [
            f"На основе анализа {len(sources)} релевантных документов:",
            ""
        ]
        
        for i, source in enumerate(sources[:3], 1):  # Берем только первые 3 источника
            metadata = source.metadata
            source_info = f"{i}. "
            
            if "article" in metadata:
                source_info += f"Статья {metadata['article']}"
            if "title" in metadata:
                source_info += f" - {metadata['title']}"
            if "source" in metadata:
                source_info += f" ({metadata['source']})"
            
            # Добавляем краткую выдержку
            content_preview = source.content[:200] + "..." if len(source.content) > 200 else source.content
            source_info += f"\n   {content_preview}\n"
            
            answer_parts.append(source_info)
        
        answer_parts.extend([
            "",
            "⚠️ Для получения точной правовой консультации рекомендуется обратиться к квалифицированному юристу.",
            "",
            f"Найдено источников: {len(sources)} | Уверенность: {self._calculate_confidence(sources, query):.1%}"
        ])
        
        return "\n".join(answer_parts)

    def _calculate_confidence(self, sources: List[DocumentSource], query: str) -> float:
        """Рассчитывает уверенность в ответе"""
        
        if not sources:
            return 0.0
        
        # Базовая уверенность на основе количества и качества источников
        base_confidence = min(len(sources) / 5.0, 1.0)  # Максимум при 5+ источниках
        
        # Средняя релевантность источников
        avg_relevance = sum(source.relevance for source in sources) / len(sources)
        
        # Комбинируем факторы
        confidence = (base_confidence * 0.4) + (avg_relevance * 0.6)
        
        return min(confidence, 1.0)

    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        document_id: Optional[str] = None,
        chunk_size: int = 1000
    ) -> bool:
        """Добавляет документ в RAG систему"""
        
        if not self.is_ready():
            logger.warning("UnifiedRAGService не готов для добавления документов")
            return False
        
        try:
            # Разбиваем документ на чанки
            chunks = self._split_document(content, chunk_size)
            
            success_count = 0
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_id": f"{document_id or 'doc'}_{i}",
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
                
                # Добавляем чанк в векторное хранилище
                success = await self.vector_store.add_document(
                    content=chunk,
                    metadata=chunk_metadata,
                    document_id=chunk_metadata["chunk_id"]
                )
                
                if success:
                    success_count += 1
            
            # Обновляем статистику
            await self._update_vector_store_stats()
            
            logger.info("✅ Документ добавлен: %d/%d чанков успешно", success_count, len(chunks))
            return success_count == len(chunks)
            
        except Exception as e:
            logger.error("❌ Ошибка добавления документа: %s", e)
            return False

    def _split_document(self, content: str, chunk_size: int) -> List[str]:
        """Разбивает документ на чанки с перекрытием"""
        
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        overlap = self.search_config["chunk_overlap"]
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            
            # Пытаемся найти границу предложения
            if end < len(content):
                # Ищем ближайшую точку или перенос строки
                for i in range(end, max(start + chunk_size // 2, end - 100), -1):
                    if content[i] in '.!?\n':
                        end = i + 1
                        break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Следующий чанк начинается с перекрытием
            start = end - overlap
            
            if start >= len(content):
                break
        
        return chunks

    def _generate_cache_key(self, query: str, max_results: int, similarity_threshold: float, 
                          situation_date: str, strategy: str) -> str:
        """Генерирует ключ для кэширования"""
        key_data = f"{query}:{max_results}:{similarity_threshold}:{situation_date}:{strategy}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def _get_cached_response(self, cache_key: str) -> Optional[RAGResponse]:
        """Получает ответ из кэша"""
        try:
            if cache_key in self._search_cache:
                timestamp, response = self._search_cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    return response
                else:
                    # Удаляем устаревшую запись
                    del self._search_cache[cache_key]
        except Exception as e:
            logger.error("❌ Ошибка получения из кэша: %s", e)
        
        return None

    async def _cache_response(self, cache_key: str, response: RAGResponse):
        """Кэширует ответ"""
        try:
            # Очищаем кэш если он переполнен
            if len(self._search_cache) >= self._max_cache_size:
                # Удаляем самые старые записи
                sorted_items = sorted(self._search_cache.items(), key=lambda x: x[1][0])
                items_to_remove = len(self._search_cache) - self._max_cache_size + 10
                for i in range(items_to_remove):
                    del self._search_cache[sorted_items[i][0]]
            
            self._search_cache[cache_key] = (time.time(), response)
            
        except Exception as e:
            logger.error("❌ Ошибка кэширования: %s", e)

    async def _update_vector_store_stats(self):
        """Обновляет статистику векторного хранилища"""
        try:
            status = self.vector_store.get_status()
            self._stats["vector_store_size"] = status.get("documents_count", 0)
        except Exception as e:
            logger.error("❌ Ошибка обновления статистики: %s", e)

    def _update_search_stats(self, success: bool, search_time: float, generation_time: float):
        """Обновляет статистику поиска"""
        self._stats["total_searches"] += 1
        
        if success:
            self._stats["successful_searches"] += 1
        else:
            self._stats["failed_searches"] += 1
        
        self._stats["last_search_time"] = search_time
        
        # Обновляем средние времена
        if self._stats["successful_searches"] > 0:
            total_search_time = self._stats["average_search_time"] * (self._stats["successful_searches"] - 1)
            self._stats["average_search_time"] = (total_search_time + search_time) / self._stats["successful_searches"]
            
            total_gen_time = self._stats["average_generation_time"] * (self._stats["successful_searches"] - 1)
            self._stats["average_generation_time"] = (total_gen_time + generation_time) / self._stats["successful_searches"]

    def _add_to_history(self, query: str, response: RAGResponse):
        """Добавляет поиск в историю"""
        history_entry = {
            "timestamp": datetime.now(),
            "query": query,
            "sources_count": len(response.sources),
            "confidence": response.confidence,
            "search_time": response.search_time,
            "generation_time": response.generation_time,
            "total_time": response.total_time
        }
        
        self._search_history.append(history_entry)
        
        # Ограничиваем размер истории
        if len(self._search_history) > self._max_history:
            self._search_history = self._search_history[-self._max_history:]

    def get_metrics(self) -> RAGMetrics:
        """Возвращает метрики производительности"""
        cache_hit_rate = 0.0
        if self._stats["total_searches"] > 0:
            cache_hit_rate = self._stats["cache_hits"] / self._stats["total_searches"]
        
        return RAGMetrics(
            search_time_avg=self._stats["average_search_time"],
            generation_time_avg=self._stats["average_generation_time"],
            cache_hit_rate=cache_hit_rate,
            vector_store_size=self._stats["vector_store_size"],
            embedding_generation_time=self._stats["average_embedding_time"],
            total_searches=self._stats["total_searches"],
            successful_searches=self._stats["successful_searches"],
            failed_searches=self._stats["failed_searches"]
        )

    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья сервиса"""
        return {
            "status": "healthy" if self.is_ready() else "unhealthy",
            "initialized": self._initialized,
            "vector_store_ready": self.vector_store.is_ready(),
            "embeddings_ready": hasattr(self.embeddings_service, '_model_loaded') and self.embeddings_service._model_loaded,
            "cache_size": len(self._search_cache),
            "vector_store_size": self._stats["vector_store_size"],
            "metrics": self.get_metrics().__dict__
        }

    def get_stats(self) -> Dict[str, Any]:
        """Возвращает подробную статистику"""
        return {
            "performance": self._stats.copy(),
            "cache": {
                "size": len(self._search_cache),
                "max_size": self._max_cache_size,
                "ttl": self._cache_ttl
            },
            "history": {
                "size": len(self._search_history),
                "max_size": self._max_history
            },
            "config": self.search_config.copy()
        }


# Глобальный экземпляр сервиса
unified_rag_service = UnifiedRAGService()