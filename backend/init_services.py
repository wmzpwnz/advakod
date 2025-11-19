#!/usr/bin/env python3
"""
Скрипт для инициализации всех сервисов АДВАКОД
"""
import sys
import os
import asyncio
import logging

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.embeddings_service import embeddings_service
from app.services.vector_store_service import vector_store_service
from app.services.unified_llm_service import unified_llm_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

async def initialize_all_services():
    """Инициализирует все сервисы системы"""
    print("🚀 Инициализация сервисов АДВАКОД...")
    
    try:
        # 1. Инициализируем embeddings
        print("📚 Инициализация embeddings service...")
        embeddings_service.load_model()
        print("✅ Embeddings service готов")
        
        # 2. Инициализируем vector store
        print("🗄️ Инициализация vector store service...")
        vector_store_service.initialize()
        print("✅ Vector store service готов")
        
        # 3. Инициализируем unified LLM (Vistral)
        print("🤖 Инициализация unified LLM service (Vistral)...")
        await unified_llm_service.ensure_model_loaded_async()
        print("✅ Unified LLM service готов")
        
        # 4. Проверяем RAG
        print("🔍 Проверка RAG service...")
        rag_ready = rag_service.is_ready()
        print(f"✅ RAG service готов: {rag_ready}")
        
        print("\n🎉 Все сервисы успешно инициализированы!")
        
        # Выводим статус
        print("\n📊 Статус сервисов:")
        print(f"  - Embeddings: {embeddings_service.is_ready()}")
        print(f"  - Vector Store: {vector_store_service.is_ready()}")
        print(f"  - Unified LLM: {unified_llm_service.is_model_loaded()}")
        print(f"  - RAG System: {rag_service.is_ready()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        logger.exception("Ошибка инициализации сервисов")
        return False

if __name__ == "__main__":
    success = asyncio.run(initialize_all_services())
    sys.exit(0 if success else 1)
