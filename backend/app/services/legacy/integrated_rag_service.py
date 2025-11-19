"""
Упрощенный интегрированный RAG сервис
Использует только simple_expert_rag как fallback
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import asyncio

from .simple_expert_rag import SimpleExpertRAG, LegalMetadata

logger = logging.getLogger(__name__)

class IntegratedRAGService:
    """Упрощенный интегрированный RAG сервис"""
    
    def __init__(self):
        self.simple_rag = SimpleExpertRAG()  # Используем только простую систему
        self.initialized = False
        
    async def initialize(self):
        """Инициализация интегрированного сервиса"""
        try:
            logger.info("🚀 Инициализация интегрированного RAG сервиса...")
            
            # Инициализируем простую RAG систему
            await self.simple_rag.initialize()
            
            self.initialized = True
            logger.info("🎉 Интегрированный RAG сервис инициализирован!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            self.initialized = False
            raise
    
    async def search_with_enhancements(
        self,
        query: str,
        situation_date: Optional[date] = None,
        use_enhanced: bool = True,
        top_k: int = 20,
        rerank_top_k: int = 5
    ) -> Dict[str, Any]:
        """Поиск с использованием простой RAG системы"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Используем простую RAG систему
            search_results = await self.simple_rag.search_documents(
                query=query,
                situation_date=situation_date,
                top_k=top_k
            )
            
            # Подготовка контекста
            context_documents = [
                {
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "final_score": result.get("final_score", 0.0)
                }
                for result in search_results
            ]
            
            return {
                "success": True,
                "context_documents": context_documents,
                "search_results": search_results,
                "total_found": len(search_results),
                "system_used": "simple_expert_rag"
            }
                
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return {
                "success": False,
                "error": str(e),
                "context_documents": [],
                "search_results": [],
                "total_found": 0,
                "system_used": "simple_expert_rag"
            }
    
    async def generate_enhanced_response(
        self,
        query: str,
        search_data: Dict[str, Any],
        response_text: str,
        enable_fact_checking: bool = False,
        enable_explainability: bool = False
    ) -> Dict[str, Any]:
        """Генерация ответа (упрощенная версия)"""
        try:
            # В упрощенной версии просто возвращаем базовый ответ
            return {
                "success": True,
                "response": response_text,
                "fact_checking_enabled": enable_fact_checking,
                "explainability_enabled": enable_explainability,
                "enhancements_applied": False  # Упрощенная версия не применяет улучшения
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка генерации ответа: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": response_text,
                "fact_checking_enabled": False,
                "explainability_enabled": False,
                "enhancements_applied": False
            }
    
    async def add_document_with_text_enhanced(
        self,
        text_content: str,
        metadata: LegalMetadata
    ) -> Dict[str, Any]:
        """Добавление документа (упрощенная версия)"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Используем простую RAG систему
            result = await self.simple_rag.add_document_with_text(text_content, metadata)
            
            return {
                "success": result.get("success", False),
                "chunks_created": result.get("chunks_created", 0),
                "document_id": result.get("document_id", ""),
                "status": result.get("status", "error"),
                "system_used": "simple_expert_rag"
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления документа: {e}")
            return {
                "success": False,
                "error": str(e),
                "chunks_created": 0,
                "document_id": "",
                "status": "error",
                "system_used": "simple_expert_rag"
            }
    
    async def get_enhanced_search_stats(self) -> Dict[str, Any]:
        """Получение статистики поиска"""
        try:
            simple_status = self.simple_rag.get_status()
            
            return {
                "simple_rag_status": simple_status,
                "total_documents": simple_status.get("documents_indexed", 0),
                "total_chunks": simple_status.get("chunks_indexed", 0),
                "system_type": "integrated_simple",
                "features_available": simple_status.get("features", [])
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {
                "simple_rag_status": {"status": "error"},
                "total_documents": 0,
                "total_chunks": 0,
                "system_type": "integrated_simple",
                "features_available": [],
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Получение статуса системы"""
        return {
            "status": "integrated_rag_operational",
            "system_type": "integrated_simple",
            "features": [
                "simple_search",
                "document_processing",
                "basic_rag"
            ],
            "simple_rag_initialized": self.simple_rag.initialized,
            "initialized": self.initialized
        }

# Глобальный экземпляр сервиса
integrated_rag_service = IntegratedRAGService()