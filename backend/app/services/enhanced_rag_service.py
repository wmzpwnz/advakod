"""
Улучшенная RAG система с семантическим поиском и ранжированием
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
from dataclasses import dataclass
from functools import lru_cache

from ..core.performance_optimizer import monitor_performance, response_cache
from ..core.security import validate_and_sanitize_query
from .embeddings_service import embeddings_service
from .vector_store_service import vector_store_service

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Результат поиска"""
    content: str
    score: float
    metadata: Dict[str, Any]
    source: str
    relevance: float


@dataclass
class RAGResponse:
    """Ответ RAG системы"""
    answer: str
    sources: List[SearchResult]
    confidence: float
    processing_time: float
    search_metadata: Dict[str, Any]


class EnhancedRAGService:
    """Улучшенная RAG система с семантическим поиском"""
    
    def __init__(self):
        self.embeddings_service = embeddings_service
        self.vector_store_service = vector_store_service
        self.response_cache = response_cache
        
        # Настройки поиска
        self.search_config = {
            "max_results": 10,
            "similarity_threshold": 0.7,
            "rerank_top_k": 5,
            "context_window": 2000
        }
        
        # Кэш для эмбеддингов
        self.embeddings_cache = {}
        
        # Статистика
        self.stats = {
            "total_searches": 0,
            "cache_hits": 0,
            "average_search_time": 0.0,
            "average_rerank_time": 0.0
        }
    
    async def initialize(self):
        """Инициализирует RAG систему"""
        try:
            logger.info("🔄 Initializing Enhanced RAG service...")
            start_time = time.time()
            
            # Инициализируем сервисы
            await asyncio.to_thread(self.embeddings_service.load_model)
            await asyncio.to_thread(self.vector_store_service.initialize)
            
            duration = time.time() - start_time
            logger.info(f"✅ Enhanced RAG service initialized in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Enhanced RAG service: {e}")
            raise
    
    @monitor_performance("enhanced_rag_search")
    async def search_legal_documents(
        self, 
        query: str, 
        context: str = None,
        user_id: str = None,
        ip_address: str = None,
        situation_date: Optional[str] = None
    ) -> RAGResponse:
        """Поиск в юридических документах с улучшенным ранжированием"""
        
        # Валидируем запрос
        validation_result = validate_and_sanitize_query(query, user_id, ip_address)
        if not validation_result["is_safe"]:
            return RAGResponse(
                answer="Извините, ваш запрос содержит потенциально опасный контент.",
                sources=[],
                confidence=0.0,
                processing_time=0.0,
                search_metadata={"error": "unsafe_query"}
            )
        
        sanitized_query = validation_result["sanitized_query"]
        
        # Проверяем кэш
        cached_response = self.response_cache.get_cached_response(sanitized_query, context)
        if cached_response:
            self.stats["cache_hits"] += 1
            logger.info("📦 Cache hit for RAG search")
            return RAGResponse(**cached_response)
        
        start_time = time.time()
        
        try:
            # 1. Семантический поиск с учетом даты
            semantic_results = await self._semantic_search(sanitized_query, situation_date)
            
            # 2. Поиск по ключевым словам
            keyword_results = await self._keyword_search(sanitized_query)
            
            # 3. Объединяем и ранжируем результаты
            combined_results = self._combine_and_rank_results(
                semantic_results, keyword_results
            )
            
            # 4. Переранжируем результаты
            reranked_results = await self._rerank_results(sanitized_query, combined_results)
            
            # 5. Формируем контекст
            context_text = self._build_context(reranked_results)
            
            # 6. Генерируем ответ
            answer = await self._generate_answer(sanitized_query, context_text)
            
            processing_time = time.time() - start_time
            
            # Формируем ответ
            response = RAGResponse(
                answer=answer,
                sources=reranked_results[:self.search_config["rerank_top_k"]],
                confidence=self._calculate_confidence(reranked_results),
                processing_time=processing_time,
                search_metadata={
                    "semantic_results": len(semantic_results),
                    "keyword_results": len(keyword_results),
                    "total_results": len(combined_results),
                    "reranked_results": len(reranked_results)
                }
            )
            
            # Кэшируем результат
            self.response_cache.cache_response(
                sanitized_query, 
                response.__dict__, 
                context
            )
            
            # Обновляем статистику
            self.stats["total_searches"] += 1
            self._update_average_search_time(processing_time)
            
            logger.info(f"✅ Enhanced RAG search completed in {processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Error in Enhanced RAG search: {e}")
            
            return RAGResponse(
                answer="Извините, произошла ошибка при поиске в правовой базе.",
                sources=[],
                confidence=0.0,
                processing_time=processing_time,
                search_metadata={"error": str(e)}
            )
    
    async def _semantic_search(self, query: str, situation_date: Optional[str] = None) -> List[SearchResult]:
        """Семантический поиск по эмбеддингам с учетом даты"""
        try:
            # Специальная обработка для поиска статей УК РФ
            enhanced_query = self._enhance_uk_search_query(query)
            
            # Поиск в векторной базе с учетом даты
            search_results = await self.vector_store_service.search_similar(
                query=enhanced_query,
                limit=self.search_config["max_results"],
                min_similarity=0.1,  # Снижаем порог для лучшего поиска
                situation_date=situation_date
            )
            
            # Преобразуем в SearchResult
            results = []
            for result in search_results:
                # Повышаем релевантность для статей УК РФ
                relevance_boost = self._calculate_uk_relevance_boost(query, result["content"])
                
                search_result = SearchResult(
                    content=result["content"],
                    score=float(result["similarity"]) + relevance_boost,
                    metadata=result["metadata"],
                    source=result["metadata"].get("source", "unknown"),
                    relevance=float(result["similarity"]) + relevance_boost
                )
                results.append(search_result)
            
            # Сортируем по релевантности
            results.sort(key=lambda x: x.relevance, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    async def _keyword_search(self, query: str) -> List[SearchResult]:
        """Поиск по ключевым словам"""
        try:
            # Извлекаем ключевые слова
            keywords = self._extract_keywords(query)
            
            # Используем семантический поиск с ключевыми словами
            keyword_query = " ".join(keywords)
            search_results = await self.vector_store_service.search_similar(
                query=keyword_query,
                limit=self.search_config["max_results"],
                min_similarity=0.1
            )
            
            # Преобразуем в SearchResult
            results = []
            for result in search_results:
                search_result = SearchResult(
                    content=result["content"],
                    score=float(result["similarity"]) * 0.8,  # Немного снижаем релевантность
                    metadata=result["metadata"],
                    source=result["metadata"].get("source", "unknown"),
                    relevance=float(result["similarity"]) * 0.8
                )
                results.append(search_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    def _combine_and_rank_results(
        self, 
        semantic_results: List[SearchResult], 
        keyword_results: List[SearchResult]
    ) -> List[SearchResult]:
        """Объединяет и ранжирует результаты с помощью RRF (Reciprocal Rank Fusion)"""
        from collections import defaultdict
        
        # RRF параметр (k) - обычно 60 по исследованиям
        k = 60
        
        # Создаем словарь для RRF скоров
        rrf_scores = defaultdict(float)
        doc_content_map = {}  # Сохраняем объекты SearchResult
        
        # Обрабатываем семантические результаты
        for rank, result in enumerate(semantic_results):
            # Используем первые 100 символов как ключ для дедупликации
            content_key = result.content[:100] if result.content else f"semantic_{rank}"
            
            # RRF формула: score = 1 / (k + rank)
            rrf_score = 1.0 / (k + rank + 1)  # +1 потому что rank начинается с 0
            rrf_scores[content_key] += rrf_score
            
            # Сохраняем объект с лучшим исходным скором
            if content_key not in doc_content_map or result.score > doc_content_map[content_key].score:
                # Обновляем relevance для комбинированного скора
                result.relevance = rrf_scores[content_key]
                doc_content_map[content_key] = result
        
        # Обрабатываем результаты по ключевым словам
        for rank, result in enumerate(keyword_results):
            content_key = result.content[:100] if result.content else f"keyword_{rank}"
            
            # RRF скор для BM25/keyword результатов
            rrf_score = 1.0 / (k + rank + 1)
            rrf_scores[content_key] += rrf_score
            
            if content_key not in doc_content_map:
                # Новый документ из keyword поиска
                result.relevance = rrf_scores[content_key]
                doc_content_map[content_key] = result
            else:
                # Обновляем существующий результат
                doc_content_map[content_key].relevance = rrf_scores[content_key]
        
        # Сортируем по RRF скору
        ranked_results = sorted(
            doc_content_map.values(), 
            key=lambda x: x.relevance, 
            reverse=True
        )
        
        logger.info(
            f"🔄 RRF объединение: {len(semantic_results)} семантических + "
            f"{len(keyword_results)} keyword → {len(ranked_results)} объединенных результатов"
        )
        
        return ranked_results[:self.search_config["max_results"]]
    
    async def _rerank_results(
        self, 
        query: str, 
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """Переранжирует результаты с учетом контекста"""
        
        if not results:
            return results
        
        try:
            start_time = time.time()
            
            # Получаем эмбеддинг запроса
            query_embedding = await self._get_query_embedding(query)
            
            # Переранжируем результаты
            reranked = []
            for result in results:
                # Вычисляем дополнительную релевантность
                content_embedding = await self._get_query_embedding(result.content)
                
                # Косинусное сходство
                similarity = np.dot(query_embedding, content_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(content_embedding)
                )
                
                # Обновляем релевантность
                result.relevance = (result.relevance + similarity) / 2
                reranked.append(result)
            
            # Сортируем по новой релевантности
            reranked.sort(key=lambda x: x.relevance, reverse=True)
            
            rerank_time = time.time() - start_time
            self._update_average_rerank_time(rerank_time)
            
            return reranked
            
        except Exception as e:
            logger.error(f"Error in reranking: {e}")
            return results
    
    def _build_context(self, results: List[SearchResult]) -> str:
        """Строит контекст из результатов поиска"""
        context_parts = []
        current_length = 0
        
        for result in results:
            content = result.content
            if current_length + len(content) > self.search_config["context_window"]:
                # Обрезаем последний фрагмент
                remaining = self.search_config["context_window"] - current_length
                if remaining > 100:  # Минимальная длина фрагмента
                    content = content[:remaining] + "..."
                    context_parts.append(content)
                break
            
            context_parts.append(content)
            current_length += len(content)
        
        return "\n\n".join(context_parts)
    
    async def _generate_answer(self, query: str, context: str) -> str:
        """Генерирует ответ на основе контекста"""
        # Проверяем, есть ли полная информация в контексте
        if len(context.strip()) < 200:
            return "Извините, в базе данных не найдена полная информация по вашему запросу. Рекомендую обратиться к актуальным правовым источникам."
        
        # Если контекст достаточный, используем его
        return f"На основе анализа правовой базы данных:\n\n{context}\n\nЭтот ответ основан на {len(context.split())} словах из правовых документов."
    
    def _calculate_confidence(self, results: List[SearchResult]) -> float:
        """Вычисляет уверенность в ответе"""
        if not results:
            return 0.0
        
        # Средняя релевантность топ-результатов
        top_results = results[:3]
        avg_relevance = sum(r.relevance for r in top_results) / len(top_results)
        
        # Нормализуем до 0-1
        confidence = min(avg_relevance, 1.0)
        
        return confidence
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Извлекает ключевые слова из запроса"""
        # Простое извлечение ключевых слов
        import re
        
        # Удаляем стоп-слова
        stop_words = {
            "как", "что", "где", "когда", "почему", "зачем", "кто", "какой",
            "какая", "какое", "какие", "это", "то", "в", "на", "с", "по", "для",
            "от", "до", "из", "к", "у", "о", "об", "про", "при", "без", "через"
        }
        
        # Извлекаем слова
        words = re.findall(r'\b[а-яё]+\b', query.lower())
        
        # Фильтруем стоп-слова и короткие слова
        keywords = [
            word for word in words 
            if word not in stop_words and len(word) > 2
        ]
        
        return keywords[:10]  # Ограничиваем количество ключевых слов
    
    @lru_cache(maxsize=1000)
    async def _get_query_embedding(self, query: str) -> np.ndarray:
        """Получает эмбеддинг запроса с кэшированием"""
        try:
            embedding = await self.embeddings_service.encode_text(query)
            if embedding is None:
                return np.zeros(384)  # Размер эмбеддинга по умолчанию
            return np.array(embedding)
        except Exception as e:
            logger.error(f"Error getting query embedding: {e}")
            return np.zeros(384)  # Размер эмбеддинга по умолчанию
    
    def _update_average_search_time(self, new_time: float):
        """Обновляет среднее время поиска"""
        total_searches = self.stats["total_searches"]
        if total_searches == 1:
            self.stats["average_search_time"] = new_time
        else:
            alpha = 0.1
            self.stats["average_search_time"] = (
                alpha * new_time + (1 - alpha) * self.stats["average_search_time"]
            )
    
    def _update_average_rerank_time(self, new_time: float):
        """Обновляет среднее время переранжирования"""
        if self.stats["average_rerank_time"] == 0:
            self.stats["average_rerank_time"] = new_time
        else:
            alpha = 0.1
            self.stats["average_rerank_time"] = (
                alpha * new_time + (1 - alpha) * self.stats["average_rerank_time"]
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику RAG системы"""
        return {
            "rag_stats": self.stats,
            "search_config": self.search_config,
            "cache_stats": self.response_cache.get_stats()
        }
    
    def _enhance_uk_search_query(self, query: str) -> str:
        """Улучшает поисковый запрос для статей УК РФ"""
        query_lower = query.lower()
        
        # Если запрос содержит номер статьи УК РФ
        if any(keyword in query_lower for keyword in ['статья', 'ст.', 'ук рф', 'уголовный кодекс']):
            # Добавляем синонимы и ключевые слова
            enhanced_query = f"{query} мошенничество хищение обман злоупотребление доверием уголовный кодекс"
            
            # Если есть номер статьи, добавляем его в разных форматах
            import re
            article_match = re.search(r'(\d+(?:\.\d+)?)', query)
            if article_match:
                article_num = article_match.group(1)
                enhanced_query += f" статья {article_num} ст {article_num}"
            
            return enhanced_query
        
        return query
    
    def _calculate_uk_relevance_boost(self, query: str, content: str) -> float:
        """Вычисляет дополнительную релевантность для статей УК РФ"""
        boost = 0.0
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Если в контенте есть номер статьи из запроса
        import re
        article_match = re.search(r'(\d+(?:\.\d+)?)', query_lower)
        if article_match:
            article_num = article_match.group(1)
            if f"статья {article_num}" in content_lower or f"ст. {article_num}" in content_lower:
                boost += 0.3  # Значительный буст для точного совпадения статьи
        
        # Буст для ключевых слов УК РФ
        uk_keywords = ['мошенничество', 'хищение', 'обман', 'злоупотребление доверием']
        for keyword in uk_keywords:
            if keyword in query_lower and keyword in content_lower:
                boost += 0.1
        
        # Буст для документов УК РФ
        if 'уголовный кодекс' in content_lower or 'ук рф' in content_lower:
            boost += 0.2
        
        return min(boost, 0.5)  # Ограничиваем максимальный буст

    def clear_cache(self):
        """Очищает кэш"""
        self.response_cache.cache.clear()
        self.embeddings_cache.clear()
        logger.info("🧹 Enhanced RAG cache cleared")


# Глобальный экземпляр
enhanced_rag_service = EnhancedRAGService()
