# WebSocket Services

Этот каталог содержит реализацию устойчивых WebSocket соединений для ADVAKOD системы.

## ResilientWebSocket

Основной класс для работы с WebSocket соединениями, который обеспечивает:

### Основные возможности

- ✅ **Автоматическое переподключение** с exponential backoff
- ✅ **Ping/Pong механизм** для поддержания соединения
- ✅ **Очередь сообщений** для отправки при переподключении
- ✅ **Детальная статистика** соединения
- ✅ **Пользовательские статусы** для UI
- ✅ **Обработка ошибок** с понятными кодами
- ✅ **Event-driven архитектура** для интеграции

### Использование

```javascript
import ResilientWebSocket from '../services/ResilientWebSocket';

// Создание экземпляра
const ws = new ResilientWebSocket('wss://example.com/ws', {
  maxReconnectAttempts: 10,
  reconnectDelay: 1000,
  maxReconnectDelay: 30000,
  pingInterval: 30000,
  pongTimeout: 10000
});

// Подписка на события
ws.on('open', () => console.log('Подключено'));
ws.on('message', (data) => console.log('Сообщение:', data));
ws.on('stateChange', (state) => console.log('Состояние:', state));
ws.on('error', (error) => console.error('Ошибка:', error));

// Подключение
await ws.connect();

// Отправка сообщений
ws.send({ type: 'chat', message: 'Привет!' });

// Получение статуса
const status = ws.getStatus();
const userStatus = ws.getUserFriendlyStatus();
```

### Состояния соединения

- `connecting` - Устанавливается соединение
- `connected` - Соединение активно
- `reconnecting` - Переподключение после разрыва
- `disconnected` - Нормальное отключение
- `failed` - Ошибка соединения

### События

- `open` - Соединение установлено
- `close` - Соединение закрыто
- `message` - Получено сообщение
- `error` - Произошла ошибка
- `stateChange` - Изменилось состояние
- `maxReconnectAttemptsReached` - Исчерпаны попытки переподключения

## WebSocketStatus Component

React компонент для отображения статуса WebSocket соединения.

### Возможности

- 📊 **Компактный индикатор** для встраивания в интерфейс
- 🔄 **Кнопка переподключения** при ошибках
- 📈 **Детальная статистика** соединения
- 🎨 **Цветовые индикаторы** состояния
- ⏰ **Автоматическое скрытие** после восстановления

### Использование

```jsx
import WebSocketStatus from '../components/WebSocketStatus';

// Компактный индикатор
<WebSocketStatus websocket={websocket} />

// С деталями и кнопкой переподключения
<WebSocketStatus 
  websocket={websocket}
  showDetails={true}
  onReconnect={() => websocket.reconnect()}
/>

// Плавающий индикатор
<div className="fixed top-4 right-4 z-50">
  <WebSocketStatus websocket={websocket} />
</div>
```

## useChatWebSocket Hook

React хук для интеграции WebSocket в чат компоненты.

### Возможности

- 🔌 **Автоматическое подключение** при монтировании
- 💬 **Обработка сообщений** чата
- ⌨️ **Индикатор печати** с debounce
- 🔄 **Управление сессиями** чата
- 🛑 **Остановка генерации** ответов

### Использование

```javascript
import { useChatWebSocket } from '../hooks/useChatWebSocket';

const ChatComponent = () => {
  const {
    isConnected,
    connectionState,
    websocket,
    sendChatMessage,
    sendTyping,
    stopGeneration,
    forceReconnect
  } = useChatWebSocket(sessionId, handleNewMessage);

  return (
    <div>
      <WebSocketStatus websocket={websocket} onReconnect={forceReconnect} />
      {/* Остальной UI чата */}
    </div>
  );
};
```

## Конфигурация

### Переменные окружения

```env
# WebSocket URL для подключения
REACT_APP_WS_URL=wss://advacodex.com

# Для разработки
REACT_APP_WS_URL=ws://localhost:8000
```

### Настройки по умолчанию

```javascript
const defaultOptions = {
  maxReconnectAttempts: 10,     // Максимум попыток переподключения
  reconnectDelay: 1000,         // Начальная задержка (мс)
  maxReconnectDelay: 30000,     // Максимальная задержка (мс)
  pingInterval: 30000,          // Интервал ping (мс)
  pongTimeout: 10000,           // Таймаут pong (мс)
  connectionTimeout: 10000,     // Таймаут подключения (мс)
  maxQueueSize: 100             // Размер очереди сообщений
};
```

## Обработка ошибок

### Коды закрытия WebSocket

- `1000` - Нормальное закрытие (не переподключаемся)
- `1003` - Отказ в доступе (не переподключаемся)
- `1006` - Потеря соединения (переподключаемся)
- `1008` - Ошибка аутентификации (не переподключаемся)
- `1011` - Ошибка сервера (переподключаемся)

### Стратегия переподключения

1. **Exponential backoff**: Задержка удваивается с каждой попыткой
2. **Максимальная задержка**: Не более 30 секунд
3. **Ограничение попыток**: По умолчанию 10 попыток
4. **Очередь сообщений**: Сохраняем до 100 сообщений

## Тестирование

```bash
# Запуск тестов WebSocket
npm test -- --testPathPattern="ResilientWebSocket|WebSocketStatus"

# Демонстрация функциональности
import { demonstrateResilientWebSocket } from './demo/websocket-demo';
demonstrateResilientWebSocket();
```

## Мониторинг

### Метрики соединения

```javascript
const status = websocket.getStatus();
console.log({
  connected: status.connected,
  state: status.connectionState,
  attempts: status.reconnectAttempts,
  totalConnections: status.stats.totalConnections,
  totalMessages: status.stats.totalMessages,
  lastPong: status.lastPong
});
```

### Логирование

Все события WebSocket логируются в консоль с префиксом `ResilientWebSocket:` для удобной фильтрации.

## Требования спецификации

Эта реализация выполняет следующие требования из `.kiro/specs/websocket-ai-errors-fix/`:

- ✅ **2.2**: Автоматическое переподключение WebSocket при разрыве
- ✅ **2.3**: Ping/pong механизм для поддержания соединения  
- ✅ **6.3**: Индикаторы статуса соединения для пользователя

## Производительность

- **Минимальная нагрузка**: Ping каждые 30 секунд
- **Эффективная очередь**: Максимум 100 сообщений в памяти
- **Умное переподключение**: Только при необходимости
- **Оптимизированные таймауты**: Быстрое обнаружение проблем