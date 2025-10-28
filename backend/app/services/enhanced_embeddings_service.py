"""
Enhanced Embeddings Service with Redis Caching
Реализует M-03: улучшенное кэширование эмбеддингов с Redis и TTL
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import List, Dict, Any, Optional, Union
import numpy as np
import redis
import pickle
from dataclasses import dataclass
from datetime import timedelta
from functools import wraps

from sentence_transformers import SentenceTransformer
from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Statistics for embedding cache"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_size: int = 0
    average_embedding_time: float = 0.0
    total_embedding_time: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests
    
    @property 
    def miss_rate(self) -> float:
        return 1.0 - self.hit_rate


class EmbeddingCache:
    """Redis-based cache for embeddings with TTL"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None, 
                 default_ttl: int = 3600, max_local_cache: int = 1000):
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.max_local_cache = max_local_cache
        
        # Local LRU cache as fallback and speed optimization
        self.local_cache: Dict[str, Dict[str, Any]] = {}
        self.local_access_order: List[str] = []
        
        # Cache statistics
        self.stats = CacheStats()
        
        # Try to connect to Redis
        if not self.redis_client:
            try:
                redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/1')
                self.redis_client = redis.from_url(redis_url, decode_responses=False)
                # Test connection
                self.redis_client.ping()
                logger.info("✅ Connected to Redis for embedding cache")
            except Exception as e:
                logger.warning(f"⚠️ Redis not available, using local cache only: {e}")
                self.redis_client = None
    
    def _create_cache_key(self, text: str, model_name: str = "default") -> str:
        """Create consistent cache key for text"""
        # Normalize text
        normalized_text = text.strip().lower()
        
        # Create hash
        text_hash = hashlib.sha256(
            f"{model_name}:{normalized_text}".encode('utf-8')
        ).hexdigest()
        
        return f"embedding:{model_name}:{text_hash}"
    
    def _manage_local_cache_size(self):
        """Keep local cache within size limits"""
        while len(self.local_cache) > self.max_local_cache:
            # Remove oldest entry
            oldest_key = self.local_access_order.pop(0)
            if oldest_key in self.local_cache:
                del self.local_cache[oldest_key]
    
    def _update_local_access(self, key: str):
        """Update access order for LRU eviction"""
        if key in self.local_access_order:
            self.local_access_order.remove(key)
        self.local_access_order.append(key)
    
    async def get(self, text: str, model_name: str = "default") -> Optional[List[float]]:
        """Get embedding from cache"""
        cache_key = self._create_cache_key(text, model_name)
        self.stats.total_requests += 1
        
        # Check local cache first (fastest)
        if cache_key in self.local_cache:
            entry = self.local_cache[cache_key]
            if time.time() - entry['timestamp'] < self.default_ttl:
                self._update_local_access(cache_key)
                self.stats.cache_hits += 1
                logger.debug(f"🎯 Local cache hit for embedding")
                return entry['embedding']
            else:
                # Expired entry
                del self.local_cache[cache_key]
                if cache_key in self.local_access_order:
                    self.local_access_order.remove(cache_key)
        
        # Check Redis cache
        if self.redis_client:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    embedding = pickle.loads(cached_data)
                    
                    # Store in local cache for faster access
                    self.local_cache[cache_key] = {
                        'embedding': embedding,
                        'timestamp': time.time()
                    }
                    self._update_local_access(cache_key)
                    self._manage_local_cache_size()
                    
                    self.stats.cache_hits += 1
                    logger.debug(f"🎯 Redis cache hit for embedding")
                    return embedding
            except Exception as e:
                logger.warning(f"Redis cache read error: {e}")
        
        # Cache miss
        self.stats.cache_misses += 1
        return None
    
    async def set(self, text: str, embedding: List[float], 
                  model_name: str = "default", ttl: Optional[int] = None):
        """Store embedding in cache"""
        cache_key = self._create_cache_key(text, model_name)
        ttl = ttl or self.default_ttl
        
        # Store in local cache
        self.local_cache[cache_key] = {
            'embedding': embedding,
            'timestamp': time.time()
        }
        self._update_local_access(cache_key)
        self._manage_local_cache_size()
        
        # Store in Redis with TTL
        if self.redis_client:
            try:
                serialized_embedding = pickle.dumps(embedding)
                self.redis_client.setex(cache_key, ttl, serialized_embedding)
                logger.debug(f"💾 Stored embedding in Redis cache (TTL: {ttl}s)")
            except Exception as e:
                logger.warning(f"Redis cache write error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        redis_info = {}
        if self.redis_client:
            try:
                redis_info = self.redis_client.info('memory')
            except Exception:
                redis_info = {"error": "Redis unavailable"}
        
        return {
            "cache_stats": {
                "total_requests": self.stats.total_requests,
                "cache_hits": self.stats.cache_hits,
                "cache_misses": self.stats.cache_misses,
                "hit_rate": self.stats.hit_rate,
                "miss_rate": self.stats.miss_rate
            },
            "local_cache": {
                "size": len(self.local_cache),
                "max_size": self.max_local_cache,
                "utilization": len(self.local_cache) / self.max_local_cache
            },
            "redis_info": redis_info,
            "config": {
                "default_ttl": self.default_ttl,
                "redis_available": self.redis_client is not None
            }
        }
    
    async def clear(self, pattern: str = "embedding:*"):
        """Clear cache entries matching pattern"""
        cleared_local = 0
        cleared_redis = 0
        
        # Clear local cache
        keys_to_remove = []
        for key in self.local_cache:
            if pattern.replace("*", "") in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.local_cache[key]
            if key in self.local_access_order:
                self.local_access_order.remove(key)
            cleared_local += 1
        
        # Clear Redis cache
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    cleared_redis = self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis cache clear error: {e}")
        
        logger.info(f"🧹 Cleared {cleared_local} local + {cleared_redis} Redis cache entries")
        return {"local_cleared": cleared_local, "redis_cleared": cleared_redis}


class EnhancedEmbeddingsService:
    """Enhanced embeddings service with Redis caching and performance optimizations"""
    
    def __init__(self, cache_ttl: int = 3600, max_local_cache: int = 1000):
        self.model = None
        self.model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.is_loading = False
        self.load_error = None
        
        # Enhanced caching
        self.cache = EmbeddingCache(default_ttl=cache_ttl, max_local_cache=max_local_cache)
        
        # Performance tracking
        self.generation_stats = {
            "total_requests": 0,
            "total_generation_time": 0.0,
            "average_generation_time": 0.0,
            "batch_requests": 0,
            "single_requests": 0
        }
        
        # Model warming cache
        self._model_warm = False
    
    async def _load_model_async(self):
        """Asynchronous model loading"""
        if self.model is not None:
            logger.info("📦 Embeddings model already loaded")
            return
        
        if self.is_loading:
            logger.info("⏳ Embeddings model already loading...")
            return
        
        self.is_loading = True
        try:
            logger.info(f"🚀 Loading embeddings model: {self.model_name}")
            start_time = time.time()
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, SentenceTransformer, self.model_name
            )
            
            load_time = time.time() - start_time
            logger.info(f"✅ Embeddings model loaded in {load_time:.2f}s")
            
            # Warm up the model
            await self._warm_up_model()
            
        except Exception as e:
            self.load_error = str(e)
            logger.error(f"❌ Failed to load embeddings model: {e}")
            
            # Try fallback model
            try:
                logger.info("🔄 Trying fallback model...")
                self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
                loop = asyncio.get_event_loop()
                self.model = await loop.run_in_executor(
                    None, SentenceTransformer, self.model_name
                )
                logger.info(f"✅ Fallback model loaded: {self.model_name}")
                await self._warm_up_model()
            except Exception as e2:
                logger.error(f"❌ Failed to load fallback model: {e2}")
                self.load_error = str(e2)
        finally:
            self.is_loading = False
    
    async def _warm_up_model(self):
        """Warm up the model with a test embedding"""
        if self.model and not self._model_warm:
            try:
                logger.info("🔥 Warming up embeddings model...")
                test_texts = [
                    "Тест модели эмбеддингов",
                    "Test embeddings model",
                    "Это пример юридического текста для тестирования"
                ]
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.model.encode, test_texts)
                
                self._model_warm = True
                logger.info("✅ Model warmed up successfully")
            except Exception as e:
                logger.warning(f"⚠️ Model warm-up failed: {e}")
    
    def is_ready(self) -> bool:
        """Check if service is ready"""
        return self.model is not None and not self.is_loading
    
    async def encode_text(self, text: str, use_cache: bool = True) -> Optional[List[float]]:
        """Generate embedding for single text with caching"""
        if not text or not text.strip():
            return None
        
        # Ensure model is loaded
        if not self.is_ready():
            await self._load_model_async()
        
        if not self.is_ready():
            logger.warning("⚠️ Embeddings model not ready")
            return None
        
        # Check cache first
        if use_cache:
            cached_embedding = await self.cache.get(text, self.model_name)
            if cached_embedding is not None:
                return cached_embedding
        
        # Generate embedding
        start_time = time.time()
        try:
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, self.model.encode, text.strip()
            )
            
            generation_time = time.time() - start_time
            self._update_generation_stats(generation_time, is_batch=False)
            
            embedding_list = embedding.tolist()
            
            # Cache the result
            if use_cache:
                await self.cache.set(text, embedding_list, self.model_name)
            
            logger.debug(f"✅ Generated embedding in {generation_time:.3f}s")
            return embedding_list
            
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            return None
    
    async def encode_texts(self, texts: List[str], use_cache: bool = True, 
                          batch_size: int = 32) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts with intelligent caching and batching"""
        if not texts:
            return []
        
        # Ensure model is loaded
        if not self.is_ready():
            await self._load_model_async()
        
        if not self.is_ready():
            logger.warning("⚠️ Embeddings model not ready")
            return [None] * len(texts)
        
        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []
        
        # Check cache for each text
        if use_cache:
            for i, text in enumerate(texts):
                if text and text.strip():
                    cached_embedding = await self.cache.get(text, self.model_name)
                    if cached_embedding is not None:
                        results[i] = cached_embedding
                    else:
                        uncached_indices.append(i)
                        uncached_texts.append(text.strip())
        else:
            uncached_indices = list(range(len(texts)))
            uncached_texts = [text.strip() for text in texts if text and text.strip()]
        
        # Generate embeddings for uncached texts in batches
        if uncached_texts:
            start_time = time.time()
            
            try:
                # Process in batches to manage memory
                for batch_start in range(0, len(uncached_texts), batch_size):
                    batch_end = min(batch_start + batch_size, len(uncached_texts))
                    batch_texts = uncached_texts[batch_start:batch_end]
                    batch_indices = uncached_indices[batch_start:batch_end]
                    
                    # Generate batch embeddings
                    loop = asyncio.get_event_loop()
                    batch_embeddings = await loop.run_in_executor(
                        None, self.model.encode, batch_texts
                    )
                    
                    # Store results and cache
                    for j, embedding in enumerate(batch_embeddings):
                        original_index = batch_indices[j]
                        embedding_list = embedding.tolist()
                        results[original_index] = embedding_list
                        
                        # Cache individual embeddings
                        if use_cache:
                            await self.cache.set(
                                batch_texts[j], embedding_list, self.model_name
                            )
                
                generation_time = time.time() - start_time
                self._update_generation_stats(generation_time, is_batch=True)
                
                logger.info(
                    f"✅ Generated {len(uncached_texts)} embeddings in {generation_time:.3f}s "
                    f"({len(uncached_texts)/generation_time:.1f} texts/sec)"
                )
                
            except Exception as e:
                logger.error(f"❌ Batch embedding generation failed: {e}")
                # Fill remaining with None
                for i in uncached_indices:
                    if results[i] is None:
                        results[i] = None
        
        return results
    
    def _update_generation_stats(self, generation_time: float, is_batch: bool = False):
        """Update performance statistics"""
        self.generation_stats["total_requests"] += 1
        self.generation_stats["total_generation_time"] += generation_time
        self.generation_stats["average_generation_time"] = (
            self.generation_stats["total_generation_time"] / 
            self.generation_stats["total_requests"]
        )
        
        if is_batch:
            self.generation_stats["batch_requests"] += 1
        else:
            self.generation_stats["single_requests"] += 1
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
            
        except Exception as e:
            logger.error(f"❌ Similarity calculation failed: {e}")
            return 0.0
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive service status"""
        return {
            "model_status": {
                "loaded": self.model is not None,
                "loading": self.is_loading,
                "warm": self._model_warm,
                "model_name": self.model_name,
                "load_error": self.load_error
            },
            "performance_stats": self.generation_stats,
            "cache_stats": self.cache.get_stats()
        }
    
    async def clear_cache(self, pattern: str = "embedding:*") -> Dict[str, int]:
        """Clear embedding cache"""
        return await self.cache.clear(pattern)
    
    async def preload_embeddings(self, texts: List[str]) -> Dict[str, Any]:
        """Preload embeddings for a list of texts"""
        logger.info(f"🔄 Preloading embeddings for {len(texts)} texts...")
        
        start_time = time.time()
        embeddings = await self.encode_texts(texts, use_cache=True)
        
        successful = sum(1 for emb in embeddings if emb is not None)
        failed = len(texts) - successful
        
        preload_time = time.time() - start_time
        
        result = {
            "total_texts": len(texts),
            "successful": successful,
            "failed": failed,
            "preload_time": preload_time,
            "texts_per_second": len(texts) / preload_time if preload_time > 0 else 0
        }
        
        logger.info(f"✅ Preloaded {successful}/{len(texts)} embeddings in {preload_time:.2f}s")
        return result


# Global enhanced instance
enhanced_embeddings_service = EnhancedEmbeddingsService()

# Backward compatibility
embeddings_service = enhanced_embeddings_service