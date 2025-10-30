/**
 * Демонстрация функциональности ResilientWebSocket
 * Этот файл показывает, как использовать ResilientWebSocket с автоматическим переподключением
 */

import ResilientWebSocket from '../services/ResilientWebSocket';

// Пример использования ResilientWebSocket
export const demonstrateResilientWebSocket = () => {
  console.log('🚀 Демонстрация ResilientWebSocket');
  
  // Создаем экземпляр с настройками
  const ws = new ResilientWebSocket('wss://echo.websocket.org', {
    maxReconnectAttempts: 5,
    reconnectDelay: 1000,
    maxReconnectDelay: 10000,
    pingInterval: 30000,
    pongTimeout: 5000
  });

  // Подписываемся на события
  ws.on('open', () => {
    console.log('✅ WebSocket подключен');
    
    // Отправляем тестовое сообщение
    ws.send({
      type: 'test',
      message: 'Привет от ResilientWebSocket!',
      timestamp: Date.now()
    });
  });

  ws.on('message', (data) => {
    console.log('📨 Получено сообщение:', data);
  });

  ws.on('close', ({ code, reason, shouldReconnect }) => {
    console.log(`❌ Соединение закрыто: ${code} - ${reason}`);
    console.log(`🔄 Будет переподключение: ${shouldReconnect}`);
  });

  ws.on('stateChange', (state) => {
    console.log(`🔄 Состояние изменилось: ${state}`);
    
    // Получаем пользовательский статус
    const userStatus = ws.getUserFriendlyStatus();
    console.log(`👤 Статус для пользователя: ${userStatus.text} (${userStatus.color})`);
  });

  ws.on('error', (error) => {
    console.error('❌ Ошибка WebSocket:', error);
  });

  ws.on('maxReconnectAttemptsReached', () => {
    console.log('🚫 Достигнуто максимальное количество попыток переподключения');
  });

  // Подключаемся
  ws.connect().then(() => {
    console.log('🎉 Подключение установлено');
    
    // Демонстрируем получение статуса
    setTimeout(() => {
      const status = ws.getStatus();
      console.log('📊 Статус соединения:', {
        connected: status.connected,
        state: status.connectionState,
        attempts: status.reconnectAttempts,
        queuedMessages: status.queuedMessages,
        stats: status.stats
      });
    }, 1000);
    
    // Демонстрируем отправку нескольких сообщений
    setTimeout(() => {
      for (let i = 1; i <= 3; i++) {
        ws.send({
          type: 'demo',
          message: `Сообщение ${i}`,
          timestamp: Date.now()
        });
      }
    }, 2000);
    
    // Демонстрируем принудительное переподключение
    setTimeout(() => {
      console.log('🔄 Принудительное переподключение...');
      ws.reconnect();
    }, 5000);
    
    // Отключаемся через 10 секунд
    setTimeout(() => {
      console.log('👋 Отключение...');
      ws.disconnect();
    }, 10000);
    
  }).catch((error) => {
    console.error('❌ Не удалось подключиться:', error);
  });

  return ws;
};

// Пример интеграции с React компонентом
export const WebSocketDemo = () => {
  const [ws, setWs] = React.useState(null);
  const [messages, setMessages] = React.useState([]);
  const [status, setStatus] = React.useState('disconnected');

  React.useEffect(() => {
    const websocket = new ResilientWebSocket('wss://echo.websocket.org');
    
    websocket.on('open', () => {
      console.log('Demo WebSocket connected');
    });
    
    websocket.on('message', (data) => {
      setMessages(prev => [...prev, data]);
    });
    
    websocket.on('stateChange', (state) => {
      setStatus(state);
    });
    
    websocket.connect();
    setWs(websocket);
    
    return () => {
      websocket.disconnect();
    };
  }, []);

  const sendMessage = () => {
    if (ws) {
      ws.send({
        type: 'demo',
        message: 'Тестовое сообщение',
        timestamp: Date.now()
      });
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">WebSocket Demo</h2>
      
      <div className="mb-4">
        <span className="font-medium">Статус: </span>
        <span className={`px-2 py-1 rounded text-sm ${
          status === 'connected' ? 'bg-green-100 text-green-800' :
          status === 'connecting' ? 'bg-yellow-100 text-yellow-800' :
          status === 'reconnecting' ? 'bg-orange-100 text-orange-800' :
          'bg-red-100 text-red-800'
        }`}>
          {status}
        </span>
      </div>
      
      <button
        onClick={sendMessage}
        disabled={status !== 'connected'}
        className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50 mb-4"
      >
        Отправить сообщение
      </button>
      
      <div className="border rounded p-4 h-64 overflow-y-auto">
        <h3 className="font-medium mb-2">Сообщения:</h3>
        {messages.map((msg, index) => (
          <div key={index} className="text-sm mb-1">
            {JSON.stringify(msg)}
          </div>
        ))}
      </div>
    </div>
  );
};

export default demonstrateResilientWebSocket;