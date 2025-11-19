# Design Document: Система обратной связи и модерации

## Overview

Система обратной связи и модерации для улучшения качества ответов ИИ-юриста через оценку модераторов и пользователей, с последующим автоматическим обучением модели.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
├─────────────────────────────────────────────────────────────┤
│  User Interface          │  Moderator Panel  │  Admin Panel │
│  - Feedback buttons      │  - Review queue   │  - Analytics │
│  - Rating (👍 👎)        │  - Star rating    │  - Statistics│
│  - Comment form          │  - Comments       │  - Training  │
└─────────────────────────────────────────────────────────────┘
                              ↓ REST API
┌─────────────────────────────────────────────────────────────┐
│                        Backend API                           │
├─────────────────────────────────────────────────────────────┤
│  /api/v1/feedback/       │  /api/v1/moderation/             │
│  - submit                │  - queue                          │
│  - rate                  │  - review                         │
│  - comment               │  - stats                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Services Layer                          │
├─────────────────────────────────────────────────────────────┤
│  FeedbackService    │  ModerationService  │  TrainingService│
│  - collect feedback │  - prioritize       │  - create dataset│
│  - aggregate        │  - assign           │  - fine-tune     │
│  - analyze          │  - track            │  - deploy        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Database Layer                          │
├─────────────────────────────────────────────────────────────┤
│  Feedback  │  ModerationReview  │  TrainingDataset          │
│  Rating    │  ProblemCategory   │  ModelVersion             │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Database Models

#### ResponseFeedback
```python
class ResponseFeedback(Base):
    id: int
    message_id: int  # FK to ChatMessage
    user_id: int  # FK to User
    rating: str  # 'positive', 'negative', 'neutral'
    reason: str  # optional
    comment: str  # optional
    created_at: datetime
```

#### ModerationReview
```python
class ModerationReview(Base):
    id: int
    message_id: int  # FK to ChatMessage
    moderator_id: int  # FK to User
    star_rating: int  # 1-10
    problem_categories: List[str]  # JSON array
    comment: str
    suggested_fix: str  # optional
    status: str  # 'pending', 'reviewed', 'approved'
    priority: str  # 'high', 'medium', 'low'
    created_at: datetime
    updated_at: datetime
```

#### ProblemCategory
```python
class ProblemCategory(Base):
    id: int
    name: str  # 'inaccurate_info', 'outdated_data', etc.
    display_name: str
    description: str
    severity: int  # 1-5
    is_active: bool
```

#### TrainingDataset
```python
class TrainingDataset(Base):
    id: int
    version: str  # 'v1.0', 'v1.1', etc.
    question: str
    bad_answer: str
    good_answer: str
    review_id: int  # FK to ModerationReview
    metadata: dict  # JSON
    created_at: datetime
```

#### ModeratorStats
```python
class ModeratorStats(Base):
    id: int
    moderator_id: int  # FK to User
    total_reviews: int
    points: int
    badges: List[str]  # JSON array
    rank: str  # 'novice', 'expert', 'master', 'legend'
    created_at: datetime
    updated_at: datetime
```

### 2. API Endpoints

#### User Feedback API
```
POST   /api/v1/feedback/rate
POST   /api/v1/feedback/comment
GET    /api/v1/feedback/stats/{message_id}
```

#### Moderation API
```
GET    /api/v1/moderation/queue
GET    /api/v1/moderation/review/{message_id}
POST   /api/v1/moderation/review
PUT    /api/v1/moderation/review/{review_id}
GET    /api/v1/moderation/stats
GET    /api/v1/moderation/categories
```

#### Admin API
```
GET    /api/v1/admin/moderation/analytics
GET    /api/v1/admin/moderation/moderators
POST   /api/v1/admin/moderation/training/create-dataset
POST   /api/v1/admin/moderation/training/start
GET    /api/v1/admin/moderation/training/status
```

### 3. Services

#### FeedbackService
```python
class FeedbackService:
    async def submit_rating(user_id, message_id, rating, reason)
    async def submit_comment(user_id, message_id, comment)
    async def get_message_feedback(message_id)
    async def get_user_feedback_history(user_id)
    async def aggregate_feedback_stats()
```

#### ModerationService
```python
class ModerationService:
    async def get_moderation_queue(moderator_id, filters)
    async def submit_review(moderator_id, message_id, review_data)
    async def update_review(review_id, updates)
    async def get_review_stats(moderator_id)
    async def prioritize_messages()
    async def assign_to_moderator(message_id, moderator_id)
```

#### TrainingService
```python
class TrainingService:
    async def create_dataset(min_reviews=100)
    async def export_dataset(version)
    async def start_training(dataset_version)
    async def get_training_status(job_id)
    async def deploy_model(model_version, canary_percentage)
```

#### GamificationService
```python
class GamificationService:
    async def award_points(moderator_id, points, reason)
    async def check_badges(moderator_id)
    async def update_rank(moderator_id)
    async def get_leaderboard(period='month')
```

## Data Models

### ResponseFeedback Schema
```json
{
  "id": 1,
  "message_id": 123,
  "user_id": 456,
  "rating": "negative",
  "reason": "not_answered",
  "comment": "Не ответил на мой вопрос о сроках",
  "created_at": "2024-10-21T10:30:00Z"
}
```

### ModerationReview Schema
```json
{
  "id": 1,
  "message_id": 123,
  "moderator_id": 789,
  "star_rating": 6,
  "problem_categories": ["outdated_data", "poor_structure"],
  "comment": "Информация устарела, нужно обновить данные о сроках регистрации ИП",
  "suggested_fix": "Срок регистрации ИП - 3 рабочих дня, а не 7",
  "status": "reviewed",
  "priority": "medium",
  "created_at": "2024-10-21T11:00:00Z",
  "updated_at": "2024-10-21T11:15:00Z"
}
```

### ProblemCategory Schema
```json
{
  "id": 1,
  "name": "inaccurate_info",
  "display_name": "Неточная информация",
  "description": "Ответ содержит фактические ошибки",
  "severity": 5,
  "is_active": true
}
```

## Error Handling

### Error Codes
- `400` - Invalid input (неверные данные)
- `401` - Unauthorized (не авторизован)
- `403` - Forbidden (нет прав модератора)
- `404` - Not found (сообщение не найдено)
- `409` - Conflict (уже оценено)
- `500` - Internal server error

### Error Response Format
```json
{
  "error": "validation_error",
  "message": "Star rating must be between 1 and 10",
  "details": {
    "field": "star_rating",
    "value": 15
  }
}
```

## Testing Strategy

### Unit Tests
- Models validation
- Service methods
- Business logic

### Integration Tests
- API endpoints
- Database operations
- RBAC permissions

### E2E Tests
- User feedback flow
- Moderator review flow
- Admin analytics flow

## Security Considerations

### Authentication & Authorization
- JWT tokens for API access
- RBAC check for moderator role
- Permission check: `chats.moderate`

### Data Privacy
- Anonymize user data in training datasets
- Encrypt sensitive comments
- Audit log for all moderation actions

### Rate Limiting
- User feedback: 10 per minute
- Moderator reviews: 100 per hour
- Admin operations: 50 per hour

## Performance Optimization

### Caching
- Cache moderation queue (5 minutes)
- Cache statistics (15 minutes)
- Cache problem categories (1 hour)

### Database Indexes
```sql
CREATE INDEX idx_feedback_message ON response_feedback(message_id);
CREATE INDEX idx_feedback_user ON response_feedback(user_id);
CREATE INDEX idx_review_moderator ON moderation_review(moderator_id);
CREATE INDEX idx_review_status ON moderation_review(status);
CREATE INDEX idx_review_priority ON moderation_review(priority);
```

### Pagination
- Moderation queue: 20 items per page
- Review history: 50 items per page
- Analytics: 100 items per page

## Deployment Strategy

### Phase 1: Core Functionality (Week 1)
1. Database models and migrations
2. Basic API endpoints
3. User feedback (👍 👎)
4. Moderator review panel

### Phase 2: Advanced Features (Week 2)
1. Gamification system
2. Analytics dashboard
3. Auto-prioritization
4. Training dataset creation

### Phase 3: ML Integration (Week 3)
1. LoRA fine-tuning integration
2. Canary deployment
3. A/B testing framework
4. Automated retraining

## Monitoring & Metrics

### Key Metrics
- Feedback rate (% of responses rated)
- Average star rating
- Moderation queue size
- Time to review
- Training dataset size
- Model improvement (before/after)

### Alerts
- Queue size > 100 (notify moderators)
- Average rating < 6.0 (notify admins)
- Training dataset ready (notify admins)
- Model degradation detected (notify admins)

## Integration Points

### Existing Systems
- **RBAC**: Use existing roles (moderator, admin, super_admin)
- **Chat**: Link to ChatMessage model
- **User**: Link to User model
- **LoRA**: Integrate with existing training service
- **Canary**: Use existing canary deployment system

### External Services
- **Notification Service**: Send alerts to moderators/admins
- **Analytics Service**: Track metrics
- **Audit Service**: Log all moderation actions
