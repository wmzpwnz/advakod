from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from jinja2 import Template, Environment, BaseLoader
import json

from ..models.notification import (
    NotificationTemplate, NotificationChannel, ChannelType,
    NotificationType, NotificationCategory, NotificationPriority
)
from ..schemas.notification import (
    NotificationTemplateCreate, NotificationTemplateUpdate
)

logger = logging.getLogger(__name__)


class NotificationTemplateService:
    """Service for managing notification templates"""
    
    def __init__(self):
        self.jinja_env = Environment(loader=BaseLoader())
        self.default_templates = self._load_default_templates()
    
    # Template CRUD operations
    async def create_template(
        self,
        db: Session,
        template_data: NotificationTemplateCreate,
        created_by: int
    ) -> NotificationTemplate:
        """Create a new notification template"""
        try:
            # Validate template syntax
            self._validate_template_syntax(template_data.title_template)
            self._validate_template_syntax(template_data.content_template)
            
            if template_data.subject_template:
                self._validate_template_syntax(template_data.subject_template)
            
            # Create template
            db_template = NotificationTemplate(
                name=template_data.name,
                description=template_data.description,
                type=template_data.type,
                category=template_data.category,
                priority=template_data.priority,
                title_template=template_data.title_template,
                content_template=template_data.content_template,
                subject_template=template_data.subject_template,
                trigger_event=template_data.trigger_event,
                trigger_conditions=template_data.trigger_conditions,
                channels=template_data.channels,
                throttle_minutes=template_data.throttle_minutes,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(db_template)
            db.commit()
            db.refresh(db_template)
            
            logger.info(f"Created notification template {db_template.id}: {db_template.name}")
            return db_template
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating notification template: {e}")
            raise
    
    async def get_templates(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        category: Optional[NotificationCategory] = None,
        is_active: Optional[bool] = None
    ) -> List[NotificationTemplate]:
        """Get notification templates with optional filtering"""
        try:
            query = db.query(NotificationTemplate)
            
            if category:
                query = query.filter(NotificationTemplate.category == category)
            
            if is_active is not None:
                query = query.filter(NotificationTemplate.is_active == is_active)
            
            templates = query.offset(skip).limit(limit).all()
            return templates
            
        except Exception as e:
            logger.error(f"Error getting notification templates: {e}")
            raise
    
    async def get_template(self, db: Session, template_id: int) -> Optional[NotificationTemplate]:
        """Get a specific notification template"""
        try:
            template = db.query(NotificationTemplate).filter(
                NotificationTemplate.id == template_id
            ).first()
            return template
        except Exception as e:
            logger.error(f"Error getting notification template {template_id}: {e}")
            raise
    
    async def update_template(
        self,
        db: Session,
        template_id: int,
        template_data: NotificationTemplateUpdate
    ) -> Optional[NotificationTemplate]:
        """Update a notification template"""
        try:
            template = await self.get_template(db, template_id)
            if not template:
                return None
            
            # Validate template syntax if templates are being updated
            if template_data.title_template:
                self._validate_template_syntax(template_data.title_template)
            
            if template_data.content_template:
                self._validate_template_syntax(template_data.content_template)
            
            if template_data.subject_template:
                self._validate_template_syntax(template_data.subject_template)
            
            # Update fields
            for field, value in template_data.dict(exclude_unset=True).items():
                setattr(template, field, value)
            
            template.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(template)
            
            logger.info(f"Updated notification template {template_id}")
            return template
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating notification template {template_id}: {e}")
            raise
    
    async def delete_template(self, db: Session, template_id: int) -> bool:
        """Delete a notification template"""
        try:
            template = await self.get_template(db, template_id)
            if not template:
                return False
            
            db.delete(template)
            db.commit()
            
            logger.info(f"Deleted notification template {template_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting notification template {template_id}: {e}")
            raise
    
    # Template rendering
    async def render_template(
        self,
        template: NotificationTemplate,
        variables: Dict[str, Any],
        channel_type: Optional[ChannelType] = None
    ) -> Dict[str, str]:
        """Render notification template with variables"""
        try:
            # Render title
            title = self._render_string_template(template.title_template, variables)
            
            # Render content
            content = self._render_string_template(template.content_template, variables)
            
            # Render subject if available
            subject = None
            if template.subject_template:
                subject = self._render_string_template(template.subject_template, variables)
            
            # Apply channel-specific formatting
            if channel_type:
                content = self._format_for_channel(content, channel_type, variables)
            
            result = {
                'title': title,
                'content': content
            }
            
            if subject:
                result['subject'] = subject
            
            return result
            
        except Exception as e:
            logger.error(f"Error rendering template {template.id}: {e}")
            raise
    
    def _render_string_template(self, template_string: str, variables: Dict[str, Any]) -> str:
        """Render a string template with variables"""
        try:
            template = self.jinja_env.from_string(template_string)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Error rendering string template: {e}")
            return template_string
    
    def _validate_template_syntax(self, template_string: str):
        """Validate Jinja2 template syntax"""
        try:
            self.jinja_env.from_string(template_string)
        except Exception as e:
            raise ValueError(f"Invalid template syntax: {e}")
    
    def _format_for_channel(
        self,
        content: str,
        channel_type: ChannelType,
        variables: Dict[str, Any]
    ) -> str:
        """Apply channel-specific formatting"""
        
        if channel_type == ChannelType.SLACK:
            # Convert to Slack markdown
            content = self._convert_to_slack_markdown(content)
        
        elif channel_type == ChannelType.TELEGRAM:
            # Convert to Telegram HTML
            content = self._convert_to_telegram_html(content)
        
        elif channel_type == ChannelType.EMAIL:
            # Keep as plain text or convert to HTML if needed
            pass
        
        return content
    
    def _convert_to_slack_markdown(self, content: str) -> str:
        """Convert content to Slack markdown format"""
        # Basic conversions
        content = content.replace('**', '*')  # Bold
        content = content.replace('__', '_')  # Italic
        return content
    
    def _convert_to_telegram_html(self, content: str) -> str:
        """Convert content to Telegram HTML format"""
        # Basic conversions
        content = content.replace('**', '<b>').replace('**', '</b>')  # Bold
        content = content.replace('__', '<i>').replace('__', '</i>')  # Italic
        return content
    
    # Default templates
    def _load_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load default notification templates"""
        return {
            'user_registered': {
                'name': 'Регистрация пользователя',
                'description': 'Уведомление о регистрации нового пользователя',
                'type': NotificationType.INFO,
                'category': NotificationCategory.SYSTEM,
                'priority': NotificationPriority.LOW,
                'title_template': 'Новый пользователь зарегистрирован',
                'content_template': 'Пользователь {{ user.username }} ({{ user.email }}) зарегистрировался в системе.',
                'subject_template': 'Новая регистрация в АДВАКОД',
                'trigger_event': 'user.registered',
                'channels': [ChannelType.EMAIL, ChannelType.SLACK]
            },
            
            'system_error': {
                'name': 'Системная ошибка',
                'description': 'Уведомление о критической системной ошибке',
                'type': NotificationType.ERROR,
                'category': NotificationCategory.SYSTEM,
                'priority': NotificationPriority.CRITICAL,
                'title_template': 'Критическая ошибка системы',
                'content_template': 'Произошла критическая ошибка: {{ error.message }}\n\nВремя: {{ error.timestamp }}\nМодуль: {{ error.module }}',
                'subject_template': 'КРИТИЧНО: Ошибка в системе АДВАКОД',
                'trigger_event': 'system.error.critical',
                'channels': [ChannelType.EMAIL, ChannelType.SLACK, ChannelType.TELEGRAM]
            },
            
            'moderation_needed': {
                'name': 'Требуется модерация',
                'description': 'Уведомление о необходимости модерации ответа ИИ',
                'type': NotificationType.WARNING,
                'category': NotificationCategory.MODERATION,
                'priority': NotificationPriority.MEDIUM,
                'title_template': 'Требуется модерация ответа',
                'content_template': 'Ответ ИИ требует модерации.\n\nВопрос: {{ message.question }}\nОтвет: {{ message.answer }}\nПользователь: {{ user.username }}',
                'subject_template': 'Требуется модерация - АДВАКОД',
                'trigger_event': 'moderation.needed',
                'channels': [ChannelType.PUSH, ChannelType.SLACK]
            },
            
            'task_assigned': {
                'name': 'Назначена задача',
                'description': 'Уведомление о назначении новой задачи',
                'type': NotificationType.INFO,
                'category': NotificationCategory.PROJECT,
                'priority': NotificationPriority.MEDIUM,
                'title_template': 'Назначена новая задача',
                'content_template': 'Вам назначена задача: {{ task.title }}\n\nОписание: {{ task.description }}\nСрок: {{ task.due_date }}\nПроект: {{ project.name }}',
                'subject_template': 'Новая задача - {{ task.title }}',
                'trigger_event': 'task.assigned',
                'channels': [ChannelType.EMAIL, ChannelType.PUSH]
            },
            
            'marketing_campaign_started': {
                'name': 'Запуск маркетинговой кампании',
                'description': 'Уведомление о запуске новой маркетинговой кампании',
                'type': NotificationType.SUCCESS,
                'category': NotificationCategory.MARKETING,
                'priority': NotificationPriority.LOW,
                'title_template': 'Запущена кампания: {{ campaign.name }}',
                'content_template': 'Маркетинговая кампания "{{ campaign.name }}" успешно запущена.\n\nЦелевая аудитория: {{ campaign.target_audience }}\nБюджет: {{ campaign.budget }}\nДлительность: {{ campaign.duration }}',
                'subject_template': 'Запуск кампании - {{ campaign.name }}',
                'trigger_event': 'marketing.campaign.started',
                'channels': [ChannelType.EMAIL, ChannelType.SLACK]
            },
            
            'security_alert': {
                'name': 'Предупреждение безопасности',
                'description': 'Уведомление о событии безопасности',
                'type': NotificationType.ERROR,
                'category': NotificationCategory.SECURITY,
                'priority': NotificationPriority.HIGH,
                'title_template': 'Предупреждение безопасности',
                'content_template': 'Обнаружено подозрительное действие:\n\nТип: {{ security.event_type }}\nIP: {{ security.ip_address }}\nПользователь: {{ security.user }}\nВремя: {{ security.timestamp }}',
                'subject_template': 'БЕЗОПАСНОСТЬ: Подозрительная активность',
                'trigger_event': 'security.alert',
                'channels': [ChannelType.EMAIL, ChannelType.TELEGRAM, ChannelType.SLACK]
            }
        }
    
    async def create_default_templates(self, db: Session, created_by: int):
        """Create default notification templates"""
        try:
            created_count = 0
            
            for template_key, template_data in self.default_templates.items():
                # Check if template already exists
                existing = db.query(NotificationTemplate).filter(
                    NotificationTemplate.name == template_data['name']
                ).first()
                
                if existing:
                    logger.info(f"Template '{template_data['name']}' already exists, skipping")
                    continue
                
                # Create template
                template_create = NotificationTemplateCreate(**template_data)
                await self.create_template(db, template_create, created_by)
                created_count += 1
            
            logger.info(f"Created {created_count} default notification templates")
            return created_count
            
        except Exception as e:
            logger.error(f"Error creating default templates: {e}")
            raise
    
    # Template matching
    async def find_template_for_event(
        self,
        db: Session,
        event: str,
        category: Optional[NotificationCategory] = None
    ) -> Optional[NotificationTemplate]:
        """Find template for a specific event"""
        try:
            query = db.query(NotificationTemplate).filter(
                NotificationTemplate.trigger_event == event,
                NotificationTemplate.is_active == True
            )
            
            if category:
                query = query.filter(NotificationTemplate.category == category)
            
            template = query.first()
            return template
            
        except Exception as e:
            logger.error(f"Error finding template for event {event}: {e}")
            return None
    
    # Template validation
    async def validate_template_variables(
        self,
        template: NotificationTemplate,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that all required variables are provided"""
        try:
            # Extract variables from templates
            required_vars = set()
            
            # Parse title template
            title_template = self.jinja_env.from_string(template.title_template)
            required_vars.update(title_template.environment.parse(template.title_template).find_all(
                self.jinja_env.variable_start_string
            ))
            
            # Parse content template
            content_template = self.jinja_env.from_string(template.content_template)
            required_vars.update(content_template.environment.parse(template.content_template).find_all(
                self.jinja_env.variable_start_string
            ))
            
            # Check missing variables
            missing_vars = required_vars - set(variables.keys())
            
            return {
                'valid': len(missing_vars) == 0,
                'missing_variables': list(missing_vars),
                'provided_variables': list(variables.keys())
            }
            
        except Exception as e:
            logger.error(f"Error validating template variables: {e}")
            return {
                'valid': False,
                'error': str(e)
            }


# Create service instance
notification_template_service = NotificationTemplateService()