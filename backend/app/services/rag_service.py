"""
RAG (Retrieval-Augmented Generation) сервис
Объединяет поиск релевантных документов с генерацией ответов AI моделью
Теперь с поддержкой улучшенного поиска, факт-чекинга и explainability
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .embeddings_service import embeddings_service
from .vector_store_service import vector_store_service
from .document_service import document_service
from .unified_llm_service import unified_llm_service
from .integrated_rag_service import integrated_rag_service
from .simple_expert_rag import simple_expert_rag

logger = logging.getLogger(__name__)

class RAGService:
    """Сервис для RAG (Retrieval-Augmented Generation)"""
    
    def __init__(self):
        self.min_similarity_threshold = -1.0  # Минимальное сходство для включения документа (отрицательные значения нормальны)
        self.max_context_documents = 5       # Максимальное количество документов в контексте
        self.max_context_length = 4000       # Максимальная длина контекста в символах
        self.use_enhanced_search = True      # Использовать улучшенный поиск
        self.enable_fact_checking = True     # Включить факт-чекинг
        self.enable_explainability = True    # Включить explainability
        
    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус RAG системы"""
        return {
            "embeddings_ready": embeddings_service.is_ready(),
            "vector_store_ready": vector_store_service.is_ready(),
            "ai_model_ready": unified_llm_service.is_model_loaded(),
            "min_similarity_threshold": self.min_similarity_threshold,
            "max_context_documents": self.max_context_documents,
            "max_context_length": self.max_context_length,
            "embeddings_status": embeddings_service.get_status(),
            "vector_store_status": vector_store_service.get_status(),
            "enhancements": {
                "enhanced_search_enabled": self.use_enhanced_search,
                "fact_checking_enabled": self.enable_fact_checking,
                "explainability_enabled": self.enable_explainability,
                "integrated_rag_status": integrated_rag_service.get_status() if hasattr(integrated_rag_service, 'get_status') else {}
            }
        }
    
    def is_ready(self) -> bool:
        """Проверяет, готова ли RAG система к работе"""
        return (
            embeddings_service.is_ready() and 
            vector_store_service.is_ready() and 
            unified_llm_service.is_model_loaded()
        )
    
    async def retrieve_relevant_documents(self, query: str) -> List[Dict[str, Any]]:
        """Находит релевантные документы для запроса"""
        try:
            # Используем simple_expert_rag для поиска
            if not simple_expert_rag.initialized:
                await simple_expert_rag.initialize()
            
            # Ищем документы в simple_expert_rag
            search_results = await simple_expert_rag.search_documents(
                query=query,
                top_k=self.max_context_documents * 2
            )
            
            # Конвертируем результаты в нужный формат
            relevant_docs = []
            total_length = 0
            
            for result in search_results:
                similarity = result.get('final_score', 0.0)
                content = result.get('content', '')
                metadata = result.get('metadata', {})
                
                # Проверяем пороговое значение сходства
                if similarity < self.min_similarity_threshold:
                    continue
                
                # Проверяем ограничение по длине
                if total_length + len(content) > self.max_context_length:
                    # Обрезаем документ, если он не помещается полностью
                    remaining_length = self.max_context_length - total_length
                    if remaining_length > 200:  # Минимальная полезная длина
                        content = content[:remaining_length] + "..."
                        relevant_docs.append({
                            'content': content,
                            'similarity': similarity,
                            'metadata': metadata
                        })
                    break
                
                relevant_docs.append({
                    'content': content,
                    'similarity': similarity,
                    'metadata': metadata
                })
                total_length += len(content)
                
                # Проверяем максимальное количество документов
                if len(relevant_docs) >= self.max_context_documents:
                    break
            
            logger.info(f"🔍 Найдено релевантных документов: {len(relevant_docs)} для запроса: '{query[:50]}...'")
            
            return relevant_docs
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска релевантных документов: {e}")
            return []
    
    def _build_context_prompt(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """Создает промпт с контекстом из найденных документов"""
        if not documents:
            return unified_llm_service.create_legal_prompt(query)
        
        # Собираем контекст из документов
        context_parts = []
        context_parts.append("=== КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ ===")
        
        for i, doc in enumerate(documents, 1):
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            similarity = doc.get('similarity', 0.0)
            
            # Добавляем информацию об источнике
            source_info = ""
            if 'title' in metadata:
                source_info = f"Источник: {metadata['title']}"
            elif 'filename' in metadata:
                source_info = f"Файл: {metadata['filename']}"
            else:
                source_info = f"Документ {i}"
            
            context_parts.append(f"\n--- {source_info} (релевантность: {similarity:.2f}) ---")
            context_parts.append(content.strip())
        
        context_parts.append("\n=== КОНЕЦ КОНТЕКСТА ===\n")
        
        # Создаем контекст как строку
        context = "\n".join(context_parts)
        
        # Используем правильный формат промпта Saiga с контекстом
        return unified_llm_service.create_legal_prompt(query, context=context)
    
    async def generate_rag_response(self, query: str) -> Dict[str, Any]:
        """Генерирует ответ с использованием RAG (с улучшениями или без)"""
        if not self.is_ready():
            logger.warning("RAG система не готова")
            return {
                "success": False,
                "error": "RAG система не готова",
                "response": "",
                "sources": [],
                "context_used": False
            }
        
        try:
            start_time = datetime.now()
            
            # Пробуем использовать улучшенный поиск
            if self.use_enhanced_search:
                try:
                    return await self._generate_enhanced_response(query, start_time)
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка улучшенного поиска, переключаемся на обычный: {e}")
                    self.use_enhanced_search = False
            
            # Обычный RAG поиск
            return await self._generate_standard_response(query, start_time)
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации RAG ответа: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "",
                "sources": [],
                "context_used": False
            }
    
    async def _generate_enhanced_response(self, query: str, start_time: datetime) -> Dict[str, Any]:
        """Генерация ответа с улучшениями"""
        logger.info(f"🚀 Используем улучшенный RAG поиск для: '{query[:50]}...'")
        
        # 1. Улучшенный поиск
        search_data = await integrated_rag_service.search_with_enhancements(
            query=query,
            use_enhanced=True,
            top_k=self.max_context_documents * 2,
            rerank_top_k=self.max_context_documents
        )
        
        if not search_data.get("success"):
            raise Exception("Ошибка улучшенного поиска")
        
        # 2. Подготовка контекста для генерации
        context_documents = search_data.get("context_documents", [])
        if context_documents:
            enhanced_prompt = self._build_context_prompt(query, context_documents)
            context_used = True
            logger.info(f"📚 Используем контекст из {len(context_documents)} документов")
        else:
            enhanced_prompt = unified_llm_service.create_legal_prompt(query)
            context_used = False
            logger.info("📝 Используем базовый промпт без дополнительного контекста")
        
        # 3. Генерация ответа
        logger.info("🤖 Генерируем ответ с помощью AI модели")
        response_text = ""
        async for chunk in unified_llm_service.generate_response(
            prompt=enhanced_prompt,
            max_tokens=2500,
            stream=True
        ):
            response_text += chunk
        
        if not response_text:
            raise Exception("AI модель не смогла сгенерировать ответ")
        
        # 4. Улучшения (факт-чекинг и explainability)
        enhanced_result = await integrated_rag_service.generate_enhanced_response(
            query=query,
            search_data=search_data,
            response_text=response_text,
            enable_fact_checking=self.enable_fact_checking,
            enable_explainability=self.enable_explainability
        )
        
        # 5. Подготовка источников
        sources = self._prepare_sources_from_search_data(search_data)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Улучшенный RAG ответ сгенерирован за {processing_time:.2f} сек")
        
        return {
            "success": True,
            "response": response_text,
            "sources": sources,
            "context_used": context_used,
            "documents_found": len(context_documents),
            "processing_time": processing_time,
            "query": query,
            "enhancements": enhanced_result.get("enhancements", {}),
            "search_type": search_data.get("search_type", "enhanced")
        }
    
    async def _generate_standard_response(self, query: str, start_time: datetime) -> Dict[str, Any]:
        """Генерация стандартного RAG ответа"""
        logger.info(f"🔍 Используем стандартный RAG поиск для: '{query[:50]}...'")
        
        # Шаг 1: Поиск релевантных документов
        documents = await self.retrieve_relevant_documents(query)
        
        # Шаг 2: Подготовка промпта
        if documents:
            enhanced_prompt = self._build_context_prompt(query, documents)
            context_used = True
            logger.info(f"📚 Используем контекст из {len(documents)} документов")
        else:
            enhanced_prompt = unified_llm_service.create_legal_prompt(query)
            context_used = False
            logger.info("📝 Используем базовый промпт без дополнительного контекста")
        
        # Шаг 3: Генерация ответа
        logger.info("🤖 Генерируем ответ с помощью AI модели")
        response_text = ""
        async for chunk in unified_llm_service.generate_response(
            prompt=enhanced_prompt,
            max_tokens=2500,
            stream=True
        ):
            response_text += chunk
        
        if not response_text:
            return {
                "success": False,
                "error": "AI модель не смогла сгенерировать ответ",
                "response": "",
                "sources": [],
                "context_used": context_used
            }
        
        # Шаг 4: Подготовка источников
        sources = []
        for doc in documents:
            metadata = doc.get('metadata', {})
            source = {
                "similarity": doc.get('similarity', 0.0),
                "content_preview": doc.get('content', '')[:200] + "..." if len(doc.get('content', '')) > 200 else doc.get('content', ''),
                "title": metadata.get('title') or metadata.get('filename') or metadata.get('source', 'Правовой документ'),
                "source": metadata.get('source', 'Правовой документ'),
                "article": metadata.get('article', ''),
                "part": metadata.get('part', ''),
                "item": metadata.get('item', ''),
                "edition": metadata.get('edition', '')
            }
            
            if 'file_path' in metadata:
                source['file_path'] = metadata['file_path']
            
            sources.append(source)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Стандартный RAG ответ сгенерирован за {processing_time:.2f} сек")
        
        return {
            "success": True,
            "response": response_text,
            "sources": sources,
            "context_used": context_used,
            "documents_found": len(documents),
            "processing_time": processing_time,
            "query": query,
            "search_type": "standard"
        }
    
    def _prepare_sources_from_search_data(self, search_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Подготовка источников из данных улучшенного поиска"""
        sources = []
        search_results = search_data.get("search_results", [])
        
        for result in search_results:
            if hasattr(result, 'metadata'):
                metadata = result.metadata
                source = {
                    "similarity": result.final_score,
                    "content_preview": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    "title": metadata.get('source', 'Документ'),
                    "article": metadata.get('article', ''),
                    "part": metadata.get('part', ''),
                    "item": metadata.get('item', ''),
                    "edition": metadata.get('edition', ''),
                    "url": metadata.get('url', '')
                }
                sources.append(source)
        
        return sources
    
    async def stream_rag_response(self, query: str):
        """Генерирует ответ с использованием RAG в потоковом режиме"""
        if not self.is_ready():
            yield {
                "type": "error",
                "content": "RAG система не готова"
            }
            return
        
        try:
            # Шаг 1: Поиск релевантных документов
            yield {
                "type": "status",
                "content": "Ищем релевантные документы..."
            }
            
            documents = await self.retrieve_relevant_documents(query)
            
            yield {
                "type": "status", 
                "content": f"Найдено документов: {len(documents)}"
            }
            
            # Шаг 2: Подготовка промпта
            if documents:
                enhanced_prompt = self._build_context_prompt(query, documents)
                context_used = True
            else:
                enhanced_prompt = unified_llm_service.create_legal_prompt(query)
                context_used = False
            
            yield {
                "type": "context_info",
                "context_used": context_used,
                "documents_count": len(documents)
            }
            
            # Шаг 3: Потоковая генерация ответа
            yield {
                "type": "status",
                "content": "Генерируем ответ..."
            }
            
            async for chunk in unified_llm_service.generate_response(enhanced_prompt, max_tokens=2500, stream=True):
                yield {
                    "type": "chunk",
                    "content": chunk
                }
            
            # Шаг 4: Отправляем информацию об источниках
            if documents:
                sources = []
                for doc in documents:
                    metadata = doc.get('metadata', {})
                    source = {
                        "similarity": doc.get('similarity', 0.0),
                        "title": metadata.get('title') or metadata.get('filename') or metadata.get('source', 'Правовой документ'),
                        "content_preview": doc.get('content', '')[:200] + "..." if len(doc.get('content', '')) > 200 else doc.get('content', ''),
                        "source": metadata.get('source', 'Правовой документ'),
                        "article": metadata.get('article', ''),
                        "part": metadata.get('part', ''),
                        "item": metadata.get('item', ''),
                        "edition": metadata.get('edition', '')
                    }
                    sources.append(source)
                
                yield {
                    "type": "sources",
                    "sources": sources
                }
            
            yield {
                "type": "complete"
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка потоковой генерации RAG ответа: {e}")
            yield {
                "type": "error",
                "content": str(e)
            }

# Глобальный экземпляр сервиса
rag_service = RAGService()