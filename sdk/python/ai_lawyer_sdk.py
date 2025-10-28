"""
ИИ-Юрист Python SDK
SDK для интеграции с ИИ-Юрист API
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AILawyerSDK:
    """Основной класс SDK для ИИ-Юрист"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.ai-lawyer.com/v1"):
        """
        Инициализация SDK
        
        Args:
            api_key: API ключ для аутентификации
            base_url: Базовый URL API
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Lawyer-Python-SDK/1.0.0'
        })
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнение HTTP запроса"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def chat(self, message: str, session_id: Optional[str] = None, 
             context: Optional[Dict[str, Any]] = None, 
             options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Отправка сообщения в чат с ИИ
        
        Args:
            message: Текст сообщения
            session_id: ID сессии (опционально)
            context: Дополнительный контекст
            options: Опции обработки
            
        Returns:
            Ответ от ИИ
        """
        data = {
            "message": message,
            "session_id": session_id,
            "context": context or {},
            "options": options or {}
        }
        
        return self._make_request('POST', '/external/chat', json=data)
    
    def create_session(self, title: str = None) -> Dict[str, Any]:
        """
        Создание новой сессии чата
        
        Args:
            title: Название сессии
            
        Returns:
            Информация о созданной сессии
        """
        data = {"title": title or f"Session {int(time.time())}"}
        return self._make_request('POST', '/chat/sessions', json=data)
    
    def get_session_history(self, session_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        Получение истории сессии
        
        Args:
            session_id: ID сессии
            limit: Количество сообщений
            
        Returns:
            История сообщений
        """
        params = {"limit": limit}
        return self._make_request('GET', f'/chat/sessions/{session_id}/messages', params=params)
    
    def analyze_document(self, document_path: str, analysis_type: str = "general") -> Dict[str, Any]:
        """
        Анализ документа
        
        Args:
            document_path: Путь к документу
            analysis_type: Тип анализа
            
        Returns:
            Результат анализа
        """
        with open(document_path, 'rb') as file:
            files = {'file': file}
            data = {'analysis_type': analysis_type}
            return self._make_request('POST', '/files/analyze', files=files, data=data)
    
    def get_legal_advice(self, question: str, category: str = None) -> Dict[str, Any]:
        """
        Получение юридической консультации
        
        Args:
            question: Вопрос
            category: Категория права
            
        Returns:
            Юридическая консультация
        """
        data = {
            "question": question,
            "category": category
        }
        return self._make_request('POST', '/legal/advice', json=data)
    
    def search_legal_database(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Поиск в юридической базе данных
        
        Args:
            query: Поисковый запрос
            filters: Фильтры поиска
            
        Returns:
            Результаты поиска
        """
        data = {
            "query": query,
            "filters": filters or {}
        }
        return self._make_request('POST', '/legal/search', json=data)
    
    def create_webhook_subscription(self, url: str, events: List[str], secret: str = None) -> Dict[str, Any]:
        """
        Создание webhook подписки
        
        Args:
            url: URL для webhook
            events: Список событий
            secret: Секрет для подписи
            
        Returns:
            Информация о подписке
        """
        data = {
            "url": url,
            "events": events,
            "secret": secret
        }
        return self._make_request('POST', '/external/webhooks', json=data)
    
    def get_api_stats(self) -> Dict[str, Any]:
        """
        Получение статистики использования API
        
        Returns:
            Статистика API
        """
        return self._make_request('GET', '/external/stats')
    
    def health_check(self) -> Dict[str, Any]:
        """
        Проверка здоровья API
        
        Returns:
            Статус API
        """
        return self._make_request('GET', '/external/health')

class AILawyerAsyncSDK:
    """Асинхронная версия SDK"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.ai-lawyer.com/v1"):
        """
        Инициализация асинхронного SDK
        
        Args:
            api_key: API ключ для аутентификации
            base_url: Базовый URL API
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Lawyer-Python-Async-SDK/1.0.0'
        }
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнение асинхронного HTTP запроса"""
        import aiohttp
        
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.request(method, url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"Async request failed: {e}")
                raise
    
    async def chat(self, message: str, session_id: Optional[str] = None, 
                   context: Optional[Dict[str, Any]] = None, 
                   options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Асинхронная отправка сообщения в чат"""
        data = {
            "message": message,
            "session_id": session_id,
            "context": context or {},
            "options": options or {}
        }
        
        return await self._make_request('POST', '/external/chat', json=data)
    
    async def get_legal_advice(self, question: str, category: str = None) -> Dict[str, Any]:
        """Асинхронное получение юридической консультации"""
        data = {
            "question": question,
            "category": category
        }
        return await self._make_request('POST', '/legal/advice', json=data)

# Утилиты
class AILawyerUtils:
    """Утилиты для работы с SDK"""
    
    @staticmethod
    def format_response(response: Dict[str, Any]) -> str:
        """Форматирование ответа для вывода"""
        if 'response' in response:
            return response['response']
        return json.dumps(response, indent=2, ensure_ascii=False)
    
    @staticmethod
    def extract_suggestions(response: Dict[str, Any]) -> List[str]:
        """Извлечение предложений из ответа"""
        return response.get('suggestions', [])
    
    @staticmethod
    def calculate_confidence(response: Dict[str, Any]) -> float:
        """Получение уровня уверенности ответа"""
        return response.get('confidence', 0.0)
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Валидация API ключа"""
        return api_key.startswith('ak_') and len(api_key) == 35

# Пример использования
if __name__ == "__main__":
    # Синхронное использование
    sdk = AILawyerSDK("your_api_key_here")
    
    # Отправка сообщения
    response = sdk.chat("Как оформить трудовой договор?")
    print("Ответ ИИ:", response['response'])
    
    # Получение юридической консультации
    advice = sdk.get_legal_advice("Какие документы нужны для регистрации ООО?")
    print("Консультация:", advice)
    
    # Асинхронное использование
    import asyncio
    
    async def async_example():
        async_sdk = AILawyerAsyncSDK("your_api_key_here")
        
        response = await async_sdk.chat("Расскажите о налоговых льготах для ИП")
        print("Асинхронный ответ:", response['response'])
    
    # asyncio.run(async_example())
