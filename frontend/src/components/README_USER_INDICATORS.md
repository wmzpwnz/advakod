# User Indicators and Error Messages Components

This document describes the new user interface components implemented for task 7 of the WebSocket AI errors fix specification.

## Components Overview

### 1. ErrorMessage Component

**Purpose**: Displays informative error messages with appropriate actions for users.

**Features**:
- Automatically detects error types (WebSocket, HTTP, network, etc.)
- Provides user-friendly messages instead of technical errors
- Shows appropriate action buttons (retry, reconnect, login, etc.)
- Supports multiple display variants (default, inline, toast)

**Usage**:
```jsx
import ErrorMessage from '../components/ErrorMessage';

// Basic usage
<ErrorMessage error="Something went wrong" onRetry={handleRetry} />

// With WebSocket error
<ErrorMessage 
  error={{ code: 1008, message: 'Auth failed' }} 
  onReconnect={handleReconnect}
/>

// Toast variant
<ErrorMessage 
  error={error} 
  variant="toast" 
  onRetry={handleRetry}
/>
```

### 2. AIThinkingIndicator Component

**Purpose**: Shows "AI is thinking..." indicator with ability to stop generation.

**Features**:
- Animated thinking phases that change over time
- Elapsed time display
- Progress bar (when estimated time is provided)
- Stop generation button
- Multiple display variants (default, compact, detailed)

**Usage**:
```jsx
import AIThinkingIndicator from '../components/AIThinkingIndicator';

// Basic usage
<AIThinkingIndicator 
  isGenerating={true}
  startTime={Date.now()}
  onStop={handleStop}
/>

// Detailed variant with progress
<AIThinkingIndicator 
  isGenerating={true}
  startTime={startTime}
  estimatedTime={120} // 2 minutes
  onStop={handleStop}
  variant="detailed"
/>

// Compact variant
<AIThinkingIndicator 
  isGenerating={true}
  variant="compact"
  onStop={handleStop}
/>
```

### 3. EnhancedConnectionStatus Component

**Purpose**: Enhanced WebSocket connection status with better reconnection capabilities.

**Features**:
- Real-time connection status updates
- Reconnection countdown timer
- Detailed connection statistics
- Manual reconnection buttons
- Auto-hide functionality

**Usage**:
```jsx
import EnhancedConnectionStatus from '../components/EnhancedConnectionStatus';

<EnhancedConnectionStatus
  websocket={websocketInstance}
  onReconnect={handleReconnect}
  onForceReconnect={handleForceReconnect}
  showDetails={true}
  autoHide={false}
/>
```

### 4. StatusNotificationSystem Component

**Purpose**: Centralized notification system for the entire application.

**Features**:
- Manages all status notifications
- Automatic WebSocket monitoring
- Global notification API
- Different notification types (success, error, info, warning)
- Auto-hide and manual dismiss options

**Usage**:
```jsx
import StatusNotificationSystem from '../components/StatusNotificationSystem';

// In main app component
<StatusNotificationSystem
  websocket={websocket}
  isGenerating={isGenerating}
  generationStartTime={generationStartTime}
  onStopGeneration={stopGeneration}
  onReconnect={reconnect}
  onForceReconnect={forceReconnect}
/>

// Using the global API anywhere in the app
window.statusNotifications.showError('Something went wrong');
window.statusNotifications.showSuccess('Operation completed');
window.statusNotifications.showInfo('Information message');
```

### 5. useStatusNotifications Hook

**Purpose**: Convenient hook for using the status notification system.

**Usage**:
```jsx
import { useStatusNotifications } from '../hooks/useStatusNotifications';

function MyComponent() {
  const { 
    showError, 
    showSuccess, 
    showInfo,
    showConnectionError,
    showAuthError 
  } = useStatusNotifications();

  const handleError = (error) => {
    showError(error, {
      autoHide: false,
      actions: [
        {
          label: 'Retry',
          action: () => retryOperation(),
          primary: true
        }
      ]
    });
  };

  return (
    // Your component JSX
  );
}
```

## Error Types and Messages

The ErrorMessage component automatically handles these error types:

### WebSocket Errors
- **1008**: Authentication failed → "Ваша сессия истекла. Пожалуйста, войдите в систему заново."
- **1006**: Connection lost → "Связь с сервером прервана. Попробуем переподключиться автоматически."
- **1011**: Server error → "На сервере произошла ошибка. Попробуйте позже или обратитесь в поддержку."

### HTTP Errors
- **401**: Unauthorized → "Пожалуйста, войдите в систему для продолжения работы."
- **408**: Timeout → "Генерация ответа превысила максимальное время ожидания"
- **429**: Rate limit → "Вы отправили слишком много запросов. Подождите немного перед следующим запросом."
- **503**: Service unavailable → "Сервер временно перегружен. Подождите немного и попробуйте снова."
- **5xx**: Server errors → "На сервере произошла ошибка. Мы уже работаем над её устранением."

### Network Errors
- No response → "Не удалось соединиться с сервером. Проверьте подключение к интернету."

### AI Model Errors
- Model unavailable → "Модель искусственного интеллекта временно недоступна. Попробуйте позже."

## Integration with Chat Component

The Chat component has been updated to use all these new components:

1. **Error handling**: All errors now show user-friendly messages with appropriate actions
2. **AI thinking indicator**: Replaces the old simple spinner with an enhanced indicator
3. **Status notifications**: Global notification system monitors WebSocket and shows relevant notifications
4. **Stop generation**: Users can stop AI generation at any time

## Testing

Basic tests are included for the main components:

```bash
npm test -- --testPathPattern="ErrorMessage|AIThinkingIndicator"
```

## Requirements Fulfilled

This implementation fulfills the following requirements from the specification:

- **6.1**: Informative error messages for users ✅
- **6.2**: WebSocket connection status with reconnection ✅  
- **6.3**: Manual reconnection button for errors ✅
- **6.4**: "AI thinking..." indicator during generation ✅
- **6.5**: Ability to stop generation on user demand ✅

## Future Enhancements

Potential improvements for future versions:

1. **Accessibility**: Add ARIA labels and keyboard navigation
2. **Internationalization**: Support for multiple languages
3. **Customization**: Theme support and custom styling options
4. **Analytics**: Track error rates and user interactions
5. **Offline support**: Better handling of offline scenarios