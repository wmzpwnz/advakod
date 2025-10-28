# API документация админ-панели АДВАКОД

## Обзор

Данная документация описывает REST API endpoints для интегрированной админ-панели АДВАКОД. API предоставляет доступ ко всем функциям администрирования через HTTP запросы.

## Базовая информация

- **Базовый URL**: `https://api.advakod.ru/api/v1/admin`
- **Аутентификация**: JWT Bearer Token
- **Формат данных**: JSON
- **Кодировка**: UTF-8

## Аутентификация

Все API запросы требуют JWT токен в заголовке Authorization:

```http
Authorization: Bearer <jwt_token>
```

### Получение токена

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "admin@advakod.ru",
  "password": "password"
}
```

**Ответ:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "admin@advakod.ru",
    "is_admin": true,
    "role": "super_admin"
  }
}
```

## Дашборд

### Получение данных дашборда

```http
GET /api/v1/admin/dashboard
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "users": {
    "total": 1250,
    "active": 890,
    "new_today": 15,
    "new_week": 87
  },
  "chats": {
    "total_messages": 45230,
    "total_sessions": 12450,
    "avg_session_length": 8.5,
    "today_messages": 234
  },
  "system": {
    "rag_status": {
      "embeddings_ready": true,
      "vector_store_ready": true,
      "ai_model_ready": true,
      "documents_count": 1500
    },
    "vector_store_status": {
      "initialized": true,
      "size_mb": 2048,
      "last_update": "2024-10-26T10:30:00Z"
    }
  },
  "performance": {
    "avg_response_time": 1.2,
    "uptime_percentage": 99.8,
    "error_rate": 0.02
  }
}
```

## Управление пользователями

### Получение списка пользователей

```http
GET /api/v1/admin/users?page=1&limit=50&search=email&status=active&role=user
Authorization: Bearer <token>
```

**Параметры запроса:**
- `page` (int): Номер страницы (по умолчанию 1)
- `limit` (int): Количество записей на странице (по умолчанию 50, максимум 100)
- `search` (string): Поиск по email, имени или ID
- `status` (string): Фильтр по статусу (`active`, `inactive`, `blocked`)
- `role` (string): Фильтр по роли (`user`, `moderator`, `admin`)
- `created_from` (date): Дата регистрации от (YYYY-MM-DD)
- `created_to` (date): Дата регистрации до (YYYY-MM-DD)

**Ответ:**
```json
{
  "users": [
    {
      "id": 123,
      "email": "user@example.com",
      "first_name": "Иван",
      "last_name": "Петров",
      "is_active": true,
      "is_admin": false,
      "role": "user",
      "created_at": "2024-10-15T14:30:00Z",
      "last_login": "2024-10-26T09:15:00Z",
      "subscription_type": "premium",
      "total_messages": 45,
      "total_sessions": 12
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1250,
    "pages": 25,
    "has_next": true,
    "has_prev": false
  }
}
```

### Получение детальной информации о пользователе

```http
GET /api/v1/admin/users/{user_id}
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "id": 123,
  "email": "user@example.com",
  "first_name": "Иван",
  "last_name": "Петров",
  "is_active": true,
  "is_admin": false,
  "role": "user",
  "created_at": "2024-10-15T14:30:00Z",
  "last_login": "2024-10-26T09:15:00Z",
  "subscription": {
    "type": "premium",
    "expires_at": "2024-11-15T14:30:00Z",
    "auto_renew": true
  },
  "statistics": {
    "total_messages": 45,
    "total_sessions": 12,
    "avg_session_length": 7.5,
    "favorite_topics": ["трудовое право", "налоги"]
  },
  "activity": [
    {
      "date": "2024-10-26",
      "messages": 5,
      "sessions": 2,
      "duration": 15.5
    }
  ]
}
```

### Создание пользователя

```http
POST /api/v1/admin/users
Authorization: Bearer <token>
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "temporary_password",
  "first_name": "Новый",
  "last_name": "Пользователь",
  "role": "user",
  "is_active": true,
  "subscription_type": "free"
}
```

**Ответ:**
```json
{
  "id": 124,
  "email": "newuser@example.com",
  "first_name": "Новый",
  "last_name": "Пользователь",
  "is_active": true,
  "role": "user",
  "created_at": "2024-10-26T12:00:00Z",
  "message": "Пользователь создан успешно. Email с инструкциями отправлен."
}
```

### Обновление пользователя

```http
PUT /api/v1/admin/users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "Обновленное Имя",
  "is_active": false,
  "role": "moderator"
}
```

### Удаление пользователя

```http
DELETE /api/v1/admin/users/{user_id}
Authorization: Bearer <token>
```

### Массовые операции с пользователями

```http
POST /api/v1/admin/users/bulk
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_ids": [123, 124, 125],
  "action": "update_status",
  "data": {
    "is_active": false
  }
}
```

**Доступные действия:**
- `update_status`: Изменение статуса активности
- `update_role`: Изменение роли
- `delete`: Удаление пользователей
- `send_notification`: Отправка уведомления

## Система модерации

### Получение очереди модерации

```http
GET /api/v1/admin/moderation/queue?priority=high&category=legal&limit=20
Authorization: Bearer <token>
```

**Параметры:**
- `priority` (string): Приоритет (`critical`, `high`, `medium`, `low`)
- `category` (string): Категория проблемы
- `assigned_to` (int): ID модератора
- `status` (string): Статус (`pending`, `in_progress`, `completed`)

**Ответ:**
```json
{
  "messages": [
    {
      "id": 456,
      "user_question": "Какие права у работника при увольнении?",
      "ai_response": "При увольнении работник имеет право...",
      "priority": "high",
      "category": "labor_law",
      "created_at": "2024-10-26T10:00:00Z",
      "assigned_to": null,
      "confidence_score": 0.75,
      "user_feedback": null
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "pages": 3
  }
}
```

### Отправка модерации

```http
POST /api/v1/admin/moderation/review
Authorization: Bearer <token>
Content-Type: application/json

{
  "message_id": 456,
  "rating": 8,
  "comment": "Ответ правильный и полный, но можно добавить ссылку на статью ТК РФ",
  "categories": ["accuracy", "completeness"],
  "suggested_improvements": "Добавить ссылку на ст. 80 ТК РФ"
}
```

### Статистика модерации

```http
GET /api/v1/admin/moderation/stats?period=week&moderator_id=5
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "moderator_stats": {
    "total_reviews": 45,
    "avg_rating": 7.2,
    "consistency_score": 0.89,
    "avg_time_per_review": 3.5,
    "points_earned": 1250,
    "rank": "senior_moderator",
    "badges": ["critical_eye", "detail_oriented"]
  },
  "system_stats": {
    "avg_ai_quality": 7.8,
    "total_reviews": 2340,
    "quality_trend": "improving",
    "top_issues": ["incomplete_answer", "outdated_info"]
  }
}
```

## Маркетинговые инструменты

### Воронка продаж

```http
GET /api/v1/admin/marketing/funnel?period=month
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "funnel_stages": [
    {
      "stage": "visitors",
      "count": 10000,
      "conversion_rate": 1.0
    },
    {
      "stage": "registrations",
      "count": 1200,
      "conversion_rate": 0.12
    },
    {
      "stage": "trial_users",
      "count": 800,
      "conversion_rate": 0.67
    },
    {
      "stage": "paid_users",
      "count": 240,
      "conversion_rate": 0.30
    }
  ],
  "period": "2024-10",
  "total_revenue": 120000
}
```

### Управление промокодами

```http
GET /api/v1/admin/marketing/promo-codes
Authorization: Bearer <token>
```

```http
POST /api/v1/admin/marketing/promo-codes
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "WELCOME2024",
  "discount_type": "percentage",
  "discount_value": 20,
  "usage_limit": 100,
  "valid_from": "2024-10-26T00:00:00Z",
  "valid_to": "2024-12-31T23:59:59Z",
  "description": "Скидка для новых пользователей"
}
```

### Аналитика трафика

```http
GET /api/v1/admin/marketing/traffic?period=week
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "sources": [
    {
      "source": "google",
      "medium": "organic",
      "users": 2500,
      "sessions": 3200,
      "conversion_rate": 0.15,
      "revenue": 45000
    },
    {
      "source": "yandex",
      "medium": "cpc",
      "users": 1200,
      "sessions": 1800,
      "conversion_rate": 0.22,
      "revenue": 28000
    }
  ],
  "utm_campaigns": [
    {
      "campaign": "autumn_promo",
      "users": 800,
      "conversion_rate": 0.25,
      "cost": 15000,
      "revenue": 35000,
      "roi": 2.33
    }
  ]
}
```

## Управление проектом

### Дашборд проекта

```http
GET /api/v1/admin/project/dashboard
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "kpis": {
    "active_tasks": 23,
    "completed_tasks": 156,
    "team_utilization": 0.85,
    "sprint_progress": 0.67,
    "bug_count": 5,
    "code_coverage": 0.89
  },
  "milestones": [
    {
      "id": 1,
      "name": "MVP Release",
      "due_date": "2024-11-15",
      "progress": 0.78,
      "status": "on_track"
    }
  ],
  "team_workload": [
    {
      "user_id": 10,
      "name": "Иван Разработчик",
      "utilization": 0.90,
      "active_tasks": 3,
      "capacity": "full"
    }
  ]
}
```

### Управление задачами

```http
GET /api/v1/admin/project/tasks?status=active&assignee=10
Authorization: Bearer <token>
```

```http
POST /api/v1/admin/project/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Исправить баг в системе уведомлений",
  "description": "Пользователи не получают push-уведомления в Firefox",
  "priority": "high",
  "assignee_id": 10,
  "due_date": "2024-11-01",
  "estimated_hours": 4,
  "tags": ["bug", "notifications", "firefox"]
}
```

## Система уведомлений

### Получение уведомлений

```http
GET /api/v1/admin/notifications?unread_only=true&limit=20
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "notifications": [
    {
      "id": 789,
      "type": "system_alert",
      "title": "Высокая нагрузка на сервер",
      "message": "CPU использование превысило 80%",
      "priority": "high",
      "created_at": "2024-10-26T11:30:00Z",
      "read_at": null,
      "action_url": "/admin/system/monitoring"
    }
  ],
  "unread_count": 5,
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45
  }
}
```

### Отправка уведомления

```http
POST /api/v1/admin/notifications/send
Authorization: Bearer <token>
Content-Type: application/json

{
  "recipients": [10, 11, 12],
  "type": "announcement",
  "title": "Обновление системы",
  "message": "Запланировано техническое обслуживание на 27.10.2024",
  "channels": ["push", "email"],
  "scheduled_at": "2024-10-26T15:00:00Z"
}
```

### Настройки уведомлений

```http
GET /api/v1/admin/notifications/settings
Authorization: Bearer <token>
```

```http
PUT /api/v1/admin/notifications/settings
Authorization: Bearer <token>
Content-Type: application/json

{
  "push_enabled": true,
  "email_enabled": true,
  "slack_webhook": "https://hooks.slack.com/...",
  "telegram_bot_token": "123456:ABC-DEF...",
  "notification_types": {
    "system_alerts": true,
    "moderation_queue": true,
    "user_activity": false
  }
}
```

## Продвинутая аналитика

### Конструктор дашбордов

```http
GET /api/v1/admin/analytics/dashboards
Authorization: Bearer <token>
```

```http
POST /api/v1/admin/analytics/dashboards
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Маркетинговый дашборд",
  "description": "Основные маркетинговые метрики",
  "widgets": [
    {
      "type": "metric",
      "title": "Конверсия",
      "data_source": "marketing.conversion_rate",
      "position": {"x": 0, "y": 0, "w": 2, "h": 1}
    }
  ],
  "is_public": false
}
```

### Когортный анализ

```http
GET /api/v1/admin/analytics/cohorts?period=month&metric=retention
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "cohorts": [
    {
      "cohort": "2024-09",
      "size": 120,
      "periods": [
        {"period": 0, "users": 120, "retention": 1.0},
        {"period": 1, "users": 89, "retention": 0.74},
        {"period": 2, "users": 67, "retention": 0.56}
      ]
    }
  ],
  "metric": "retention",
  "period_type": "month"
}
```

### Пользовательские метрики

```http
GET /api/v1/admin/analytics/metrics
Authorization: Bearer <token>
```

```http
POST /api/v1/admin/analytics/metrics
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Активные пользователи за неделю",
  "description": "Количество пользователей с активностью за последние 7 дней",
  "query": "SELECT COUNT(DISTINCT user_id) FROM user_activity WHERE created_at >= NOW() - INTERVAL 7 DAY",
  "alert_threshold": 1000,
  "alert_condition": "less_than"
}
```

## Резервное копирование

### Список бэкапов

```http
GET /api/v1/admin/backup/list
Authorization: Bearer <token>
```

**Ответ:**
```json
{
  "backups": [
    {
      "id": "backup_20241026_120000",
      "type": "full",
      "size_mb": 2048,
      "created_at": "2024-10-26T12:00:00Z",
      "status": "completed",
      "integrity_check": "passed",
      "components": ["database", "files", "configs"]
    }
  ]
}
```

### Создание бэкапа

```http
POST /api/v1/admin/backup/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "full",
  "components": ["database", "files"],
  "description": "Бэкап перед обновлением системы"
}
```

### Восстановление из бэкапа

```http
POST /api/v1/admin/backup/restore
Authorization: Bearer <token>
Content-Type: application/json

{
  "backup_id": "backup_20241026_120000",
  "components": ["database"],
  "confirm": true
}
```

## WebSocket API

### Подключение

```javascript
const ws = new WebSocket('wss://api.advakod.ru/ws/admin?token=jwt_token');
```

### Подписки

```javascript
// Подписка на обновления дашборда
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'admin_dashboard'
}));

// Подписка на уведомления
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'notifications'
}));

// Подписка на очередь модерации
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'moderation_queue'
}));
```

### Получение сообщений

```javascript
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'dashboard_update':
      // Обновление метрик дашборда
      updateDashboard(data.payload);
      break;
      
    case 'notification':
      // Новое уведомление
      showNotification(data.payload);
      break;
      
    case 'moderation_queue_update':
      // Обновление очереди модерации
      updateModerationQueue(data.payload);
      break;
  }
};
```

## Коды ошибок

### HTTP статус коды

- `200` - OK
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Too Many Requests
- `500` - Internal Server Error

### Формат ошибок

```json
{
  "error": "validation_error",
  "message": "Ошибка валидации данных",
  "details": {
    "email": ["Поле email обязательно для заполнения"],
    "password": ["Пароль должен содержать минимум 8 символов"]
  },
  "timestamp": "2024-10-26T12:00:00Z",
  "request_id": "req_123456"
}
```

### Специфичные коды ошибок

- `invalid_token` - Недействительный JWT токен
- `insufficient_permissions` - Недостаточно прав доступа
- `user_not_found` - Пользователь не найден
- `validation_error` - Ошибка валидации данных
- `rate_limit_exceeded` - Превышен лимит запросов
- `backup_in_progress` - Операция резервного копирования уже выполняется

## Лимиты запросов

### Ограничения по ролям

- **super_admin**: 1000 запросов/час
- **admin**: 500 запросов/час
- **moderator**: 300 запросов/час
- **analyst**: 200 запросов/час

### Заголовки лимитов

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1698336000
```

## Примеры использования

### JavaScript/Fetch

```javascript
const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('admin_token');
  
  const response = await fetch(`https://api.advakod.ru/api/v1/admin${endpoint}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  
  return response.json();
};

// Получение списка пользователей
const users = await apiCall('/users?page=1&limit=50');

// Создание пользователя
const newUser = await apiCall('/users', {
  method: 'POST',
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'password123',
    role: 'user'
  })
});
```

### Python/Requests

```python
import requests

class AdminAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def get_users(self, page=1, limit=50):
        response = requests.get(
            f'{self.base_url}/users',
            headers=self.headers,
            params={'page': page, 'limit': limit}
        )
        response.raise_for_status()
        return response.json()
    
    def create_user(self, user_data):
        response = requests.post(
            f'{self.base_url}/users',
            headers=self.headers,
            json=user_data
        )
        response.raise_for_status()
        return response.json()

# Использование
api = AdminAPI('https://api.advakod.ru/api/v1/admin', 'your_jwt_token')
users = api.get_users(page=1, limit=10)
```

## Changelog

### v1.0.0 (2024-10-26)
- Первая версия API
- Базовые endpoints для всех модулей
- WebSocket поддержка
- Система аутентификации и авторизации

---

**Версия API:** 1.0  
**Последнее обновление:** 26 октября 2024  
**Поддержка:** api-support@advakod.ru