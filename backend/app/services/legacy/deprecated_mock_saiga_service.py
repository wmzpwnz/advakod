"""
Mock Saiga Service для тестирования
"""

import logging
import asyncio
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

class MockSaigaService:
    def __init__(self):
        self.model_name = "mock-saiga"
        logger.info("Mock Saiga Service инициализирован")

    def create_legal_prompt_with_history(self, question: str, chat_history: str = None, context: str = None) -> str:
        """Создает промпт с историей"""
        return f"Mock prompt for: {question}"

    def create_legal_prompt(self, message: str) -> str:
        """Создает простой промпт"""
        return f"Mock prompt for: {message}"

    async def generate_response_async(self, prompt: str, max_tokens: int = 1000) -> str:
        """Генерирует ответ асинхронно"""
        return f"Mock response for: {prompt[:50]}..."

    def generate_response(self, message: str, max_tokens: int = 1000) -> str:
        """Генерирует ответ синхронно"""
        return f"Mock response for: {message[:50]}..."

    async def stream_response(self, prompt: str, max_tokens: int = 1000) -> AsyncGenerator[str, None]:
        """Потоковая генерация ответа"""
        response = f"Mock streaming response for: {prompt[:50]}..."
        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.1)

# Создаем экземпляр сервиса
mock_saiga_service = MockSaigaService()


