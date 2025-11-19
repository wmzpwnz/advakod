/**
 * ИИ-Юрист JavaScript SDK
 * SDK для интеграции с ИИ-Юрист API
 */

class AILawyerSDK {
    /**
     * Инициализация SDK
     * @param {string} apiKey - API ключ для аутентификации
     * @param {string} baseUrl - Базовый URL API
     */
    constructor(apiKey, baseUrl = 'https://api.ai-lawyer.com/v1') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Lawyer-JavaScript-SDK/1.0.0'
        };
    }

    /**
     * Выполнение HTTP запроса
     * @param {string} method - HTTP метод
     * @param {string} endpoint - Endpoint API
     * @param {Object} options - Опции запроса
     * @returns {Promise<Object>} Ответ API
     */
    async _makeRequest(method, endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        const config = {
            method,
            headers: this.headers,
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Request failed:', error);
            throw error;
        }
    }

    /**
     * Отправка сообщения в чат с ИИ
     * @param {string} message - Текст сообщения
     * @param {string} sessionId - ID сессии (опционально)
     * @param {Object} context - Дополнительный контекст
     * @param {Object} options - Опции обработки
     * @returns {Promise<Object>} Ответ от ИИ
     */
    async chat(message, sessionId = null, context = {}, options = {}) {
        const data = {
            message,
            session_id: sessionId,
            context,
            options
        };

        return await this._makeRequest('POST', '/external/chat', {
            body: JSON.stringify(data)
        });
    }

    /**
     * Создание новой сессии чата
     * @param {string} title - Название сессии
     * @returns {Promise<Object>} Информация о созданной сессии
     */
    async createSession(title = null) {
        const data = {
            title: title || `Session ${Date.now()}`
        };

        return await this._makeRequest('POST', '/chat/sessions', {
            body: JSON.stringify(data)
        });
    }

    /**
     * Получение истории сессии
     * @param {string} sessionId - ID сессии
     * @param {number} limit - Количество сообщений
     * @returns {Promise<Object>} История сообщений
     */
    async getSessionHistory(sessionId, limit = 50) {
        const params = new URLSearchParams({ limit: limit.toString() });
        
        return await this._makeRequest('GET', `/chat/sessions/${sessionId}/messages?${params}`);
    }

    /**
     * Анализ документа
     * @param {File} file - Файл для анализа
     * @param {string} analysisType - Тип анализа
     * @returns {Promise<Object>} Результат анализа
     */
    async analyzeDocument(file, analysisType = 'general') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('analysis_type', analysisType);

        return await this._makeRequest('POST', '/files/analyze', {
            headers: {
                ...this.headers,
                'Content-Type': undefined // Убираем Content-Type для FormData
            },
            body: formData
        });
    }

    /**
     * Получение юридической консультации
     * @param {string} question - Вопрос
     * @param {string} category - Категория права
     * @returns {Promise<Object>} Юридическая консультация
     */
    async getLegalAdvice(question, category = null) {
        const data = {
            question,
            category
        };

        return await this._makeRequest('POST', '/legal/advice', {
            body: JSON.stringify(data)
        });
    }

    /**
     * Поиск в юридической базе данных
     * @param {string} query - Поисковый запрос
     * @param {Object} filters - Фильтры поиска
     * @returns {Promise<Object>} Результаты поиска
     */
    async searchLegalDatabase(query, filters = {}) {
        const data = {
            query,
            filters
        };

        return await this._makeRequest('POST', '/legal/search', {
            body: JSON.stringify(data)
        });
    }

    /**
     * Создание webhook подписки
     * @param {string} url - URL для webhook
     * @param {Array<string>} events - Список событий
     * @param {string} secret - Секрет для подписи
     * @returns {Promise<Object>} Информация о подписке
     */
    async createWebhookSubscription(url, events, secret = null) {
        const data = {
            url,
            events,
            secret
        };

        return await this._makeRequest('POST', '/external/webhooks', {
            body: JSON.stringify(data)
        });
    }

    /**
     * Получение статистики использования API
     * @returns {Promise<Object>} Статистика API
     */
    async getApiStats() {
        return await this._makeRequest('GET', '/external/stats');
    }

    /**
     * Проверка здоровья API
     * @returns {Promise<Object>} Статус API
     */
    async healthCheck() {
        return await this._makeRequest('GET', '/external/health');
    }
}

/**
 * Утилиты для работы с SDK
 */
class AILawyerUtils {
    /**
     * Форматирование ответа для вывода
     * @param {Object} response - Ответ API
     * @returns {string} Отформатированный ответ
     */
    static formatResponse(response) {
        if (response.response) {
            return response.response;
        }
        return JSON.stringify(response, null, 2);
    }

    /**
     * Извлечение предложений из ответа
     * @param {Object} response - Ответ API
     * @returns {Array<string>} Список предложений
     */
    static extractSuggestions(response) {
        return response.suggestions || [];
    }

    /**
     * Получение уровня уверенности ответа
     * @param {Object} response - Ответ API
     * @returns {number} Уровень уверенности
     */
    static getConfidence(response) {
        return response.confidence || 0.0;
    }

    /**
     * Валидация API ключа
     * @param {string} apiKey - API ключ
     * @returns {boolean} Валидность ключа
     */
    static validateApiKey(apiKey) {
        return apiKey.startsWith('ak_') && apiKey.length === 35;
    }

    /**
     * Создание WebSocket соединения для real-time чата
     * @param {string} apiKey - API ключ
     * @param {string} sessionId - ID сессии
     * @returns {WebSocket} WebSocket соединение
     */
    static createWebSocketConnection(apiKey, sessionId) {
        const wsUrl = `wss://api.ai-lawyer.com/ws/chat/${sessionId}?token=${apiKey}`;
        return new WebSocket(wsUrl);
    }
}

/**
 * React Hook для использования SDK
 */
function useAILawyer(apiKey) {
    const [sdk] = useState(() => new AILawyerSDK(apiKey));
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const chat = useCallback(async (message, sessionId, context, options) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await sdk.chat(message, sessionId, context, options);
            return response;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [sdk]);

    const getLegalAdvice = useCallback(async (question, category) => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await sdk.getLegalAdvice(question, category);
            return response;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [sdk]);

    return {
        sdk,
        chat,
        getLegalAdvice,
        loading,
        error
    };
}

// Экспорт для различных модульных систем
if (typeof module !== 'undefined' && module.exports) {
    // Node.js
    module.exports = {
        AILawyerSDK,
        AILawyerUtils,
        useAILawyer
    };
} else if (typeof define === 'function' && define.amd) {
    // AMD
    define([], function() {
        return {
            AILawyerSDK,
            AILawyerUtils,
            useAILawyer
        };
    });
} else {
    // Браузер
    window.AILawyerSDK = AILawyerSDK;
    window.AILawyerUtils = AILawyerUtils;
    window.useAILawyer = useAILawyer;
}

// Пример использования
/*
// Создание экземпляра SDK
const sdk = new AILawyerSDK('your_api_key_here');

// Отправка сообщения
sdk.chat('Как оформить трудовой договор?')
    .then(response => {
        console.log('Ответ ИИ:', response.response);
        console.log('Предложения:', response.suggestions);
    })
    .catch(error => {
        console.error('Ошибка:', error);
    });

// Получение юридической консультации
sdk.getLegalAdvice('Какие документы нужны для регистрации ООО?')
    .then(advice => {
        console.log('Консультация:', advice);
    });

// Использование в React
function ChatComponent() {
    const { chat, loading, error } = useAILawyer('your_api_key_here');
    
    const handleSendMessage = async (message) => {
        try {
            const response = await chat(message);
            console.log('Ответ:', response.response);
        } catch (err) {
            console.error('Ошибка:', err);
        }
    };
    
    return (
        <div>
            {loading && <p>Загрузка...</p>}
            {error && <p>Ошибка: {error}</p>}
            <button onClick={() => handleSendMessage('Привет!')}>
                Отправить сообщение
            </button>
        </div>
    );
}
*/
