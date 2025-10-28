from typing import List, Dict, Tuple, Optional
import logging
import numpy as np
from sentence_transformers import CrossEncoder
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class RerankService:
    def __init__(self):
        self.model = None
        self._model_loaded = False
        self.executor = ThreadPoolExecutor(max_workers=2)
        
    def _load_model(self):
        """Загрузка cross-encoder модели для ранжирования"""
        try:
            logger.info("Загружаем cross-encoder модель для ранжирования")
            # Используем легкую модель для быстрого ранжирования
            self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            self._model_loaded = True
            logger.info("Cross-encoder модель успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка загрузки cross-encoder модели: {e}")
            # Fallback к простому ранжированию по длине
            self._model_loaded = False
    
    async def rerank_snippets(
        self, 
        query: str, 
        snippets: List[Dict[str, str]], 
        top_k: int = 5
    ) -> List[Dict[str, str]]:
        """
        Ранжирование сниппетов по релевантности к запросу
        
        Args:
            query: Поисковый запрос
            snippets: Список сниппетов с текстом
            top_k: Количество лучших результатов
            
        Returns:
            Отсортированный список сниппетов по релевантности
        """
        if not snippets:
            return []
        
        if not self._model_loaded:
            self._load_model()
        
        try:
            if self.model:
                # Используем cross-encoder для точного ранжирования
                return await self._cross_encoder_rerank(query, snippets, top_k)
            else:
                # Fallback к простому ранжированию
                return self._simple_rerank(query, snippets, top_k)
                
        except Exception as e:
            logger.error(f"Ошибка ранжирования: {e}")
            return self._simple_rerank(query, snippets, top_k)
    
    async def _cross_encoder_rerank(
        self, 
        query: str, 
        snippets: List[Dict[str, str]], 
        top_k: int
    ) -> List[Dict[str, str]]:
        """Ранжирование с помощью cross-encoder модели"""
        
        # Подготавливаем пары (запрос, сниппет)
        pairs = []
        for snippet in snippets:
            text = snippet.get('text', snippet.get('content', ''))
            if text:
                pairs.append((query, text))
        
        if not pairs:
            return snippets[:top_k]
        
        # Выполняем ранжирование в отдельном потоке
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            self.executor, 
            self.model.predict, 
            pairs
        )
        
        # Сортируем по убыванию релевантности
        scored_snippets = list(zip(snippets, scores))
        scored_snippets.sort(key=lambda x: x[1], reverse=True)
        
        # Возвращаем топ-k результатов
        reranked = [snippet for snippet, score in scored_snippets[:top_k]]
        
        logger.info(f"Ранжирование завершено: {len(snippets)} -> {len(reranked)} сниппетов")
        return reranked
    
    def _simple_rerank(
        self, 
        query: str, 
        snippets: List[Dict[str, str]], 
        top_k: int
    ) -> List[Dict[str, str]]:
        """Простое ранжирование по ключевым словам"""
        
        query_words = set(query.lower().split())
        
        def calculate_score(snippet):
            text = snippet.get('text', snippet.get('content', '')).lower()
            text_words = set(text.split())
            
            # Подсчет пересечений слов
            intersection = len(query_words.intersection(text_words))
            union = len(query_words.union(text_words))
            
            # Jaccard similarity
            if union == 0:
                return 0
            return intersection / union
        
        # Сортируем по релевантности
        scored_snippets = [(snippet, calculate_score(snippet)) for snippet in snippets]
        scored_snippets.sort(key=lambda x: x[1], reverse=True)
        
        return [snippet for snippet, score in scored_snippets[:top_k]]
    
    async def rerank_with_context(
        self,
        query: str,
        snippets: List[Dict[str, str]],
        context: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, str]]:
        """
        Ранжирование с учетом контекста предыдущих сообщений
        
        Args:
            query: Текущий запрос
            snippets: Список сниппетов
            context: Контекст предыдущих сообщений
            top_k: Количество лучших результатов
        """
        if context:
            # Объединяем запрос с контекстом для лучшего понимания
            enhanced_query = f"{context}\n\n{query}"
            return await self.rerank_snippets(enhanced_query, snippets, top_k)
        else:
            return await self.rerank_snippets(query, snippets, top_k)
    
    def get_rerank_stats(self) -> Dict[str, any]:
        """Получение статистики работы сервиса ранжирования"""
        return {
            "model_loaded": self._model_loaded,
            "model_name": "cross-encoder/ms-marco-MiniLM-L-6-v2" if self._model_loaded else None,
            "executor_threads": self.executor._max_workers
        }


# Глобальный экземпляр сервиса
rerank_service = RerankService()
