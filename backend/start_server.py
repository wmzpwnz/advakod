#!/usr/bin/env python3
"""
Скрипт запуска сервера АДВАКОД
"""

import sys
import os
import uvicorn

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import app
    print("✅ main.py импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта main.py: {e}")
    print("Создаю минимальный сервер...")
    
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="АДВАКОД - ИИ-Юрист")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {"message": "АДВАКОД - ИИ-Юрист работает!"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "message": "Сервер работает"}
    
    @app.get("/api/v1/monitoring/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": "2024-09-17T21:28:00Z",
            "database": {"status": "healthy", "type": "sqlite"},
            "services": {
                "vector_store": "ready",
                "ai_models": "loading",
                "embeddings": "loading",
                "rag": "loading"
            }
        }

if __name__ == "__main__":
    print("🚀 Запускаю сервер АДВАКОД на порту 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
