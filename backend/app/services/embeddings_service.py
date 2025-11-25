"""
Сервис для работы с эмбеддингами (векторными представлениями текста)
Используется для RAG (Retrieval-Augmented Generation)
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
import threading
import time

logger = logging.getLogger(__name__)

# Import enhanced embeddings service
from .enhanced_embeddings_service import enhanced_embeddings_service

# Re-export for backward compatibility
embeddings_service = enhanced_embeddings_service

# Keep original class for compatibility
class EmbeddingsService:
    """Сервис для генерации эмбеддингов из текста"""
    
    def __init__(self):
        self.model = None
        self.model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # Поддерживает русский язык
        self.is_loading = False
        self.load_error = None
        
    def _load_model_sync(self):
        """Синхронная загрузка модели в отдельном потоке"""
        try:
            logger.info(f"🚀 Загружаем embeddings модель: {self.model_name}")
            start_time = time.time()
            
            # Пробуем загрузить модель с таймаутом
            import requests
            requests.adapters.DEFAULT_RETRIES = 3
            
            self.model = SentenceTransformer(self.model_name)
            
            load_time = time.time() - start_time
            logger.info(f"✅ Embeddings модель загружена за {load_time:.2f} секунд")
            
            # Тестируем модель
            test_text = "Тест embeddings модели"
            test_embedding = self.model.encode(test_text)
            logger.info(f"✅ Тест прошел успешно. Размер вектора: {len(test_embedding)}")
            
        except Exception as e:
            self.load_error = str(e)
            logger.error(f"❌ Ошибка загрузки embeddings модели: {e}")
            logger.info("🔄 Пробуем использовать упрощенную модель...")
            
            try:
                # Пробуем более простую модель
                self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"✅ Упрощенная модель загружена: {self.model_name}")
            except Exception as e2:
                logger.error(f"❌ Не удалось загрузить даже упрощенную модель: {e2}")
        finally:
            self.is_loading = False
    
    def load_model(self):
        """Синхронная загрузка модели"""
        if self.model is not None:
            logger.info("Embeddings модель уже загружена")
            return
            
        if self.is_loading:
            logger.info("Embeddings модель уже загружается...")
            return
            
        self.is_loading = True
        # Загружаем синхронно
        self._load_model_sync()
    
    def is_ready(self) -> bool:
        """Проверяет, готова ли модель к работе"""
        return self.model is not None and not self.is_loading
    
    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус сервиса"""
        return {
            "model_loaded": self.model is not None,
            "is_loading": self.is_loading,
            "load_error": self.load_error,
            "model_name": self.model_name
        }
    
    async def encode_text(self, text: str) -> Optional[List[float]]:
        """Генерирует эмбеддинг для одного текста"""
        # Загружаем модель только при первом использовании
        if not self.is_ready():
            logger.info("🔄 Embeddings модель не загружена, загружаем по требованию...")
            self.load_model()
        
        if not self.is_ready():
            logger.warning("Embeddings модель не готова")
            return None
            
        try:
            # Выполняем в отдельном потоке, чтобы не блокировать event loop
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self.model.encode, 
                text
            )
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Ошибка генерации эмбеддинга: {e}")
            return None
    
    async def encode_texts(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Генерирует эмбеддинги для списка текстов"""
        if not self.is_ready():
            logger.warning("Embeddings модель не готова")
            return [None] * len(texts)
            
        try:
            # Выполняем в отдельном потоке
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                self.model.encode, 
                texts
            )
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Ошибка генерации эмбеддингов: {e}")
            return [None] * len(texts)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Вычисляет косинусное сходство между двумя эмбеддингами"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Косинусное сходство
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Ошибка вычисления сходства: {e}")
            return 0.0

# Глобальный экземпляр сервиса
embeddings_service = EmbeddingsService()
