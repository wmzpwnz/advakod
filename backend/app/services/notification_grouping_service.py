from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Dict, Any, Optional, Set
import logging
from datetime import datetime, timedelta
import hashlib
import re
from collections import defaultdict

from ..models.notification import (
    Notification, NotificationGroup, NotificationCategory, 
    NotificationPriority, NotificationStatus
)
from ..models.user import User

logger = logging.getLogger(__name__)


class NotificationGroupingService:
    """Service for smart notification grouping and filtering"""
    
    def __init__(self):
        self.grouping_rules = self._load_grouping_rules()
        self.spam_detection_rules = self._load_spam_detection_rules()
        self.auto_dismiss_rules = self._load_auto_dismiss_rules()
    
    # Smart grouping
    async def group_notifications(
        self,
        db: Session,
        user_id: int,
        time_window_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Group similar notifications for a user"""
        try:
            # Get recent notifications
            time_threshold = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            notifications = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.created_at >= time_threshold,
                    Notification.dismissed_at.is_(None),
                    or_(
                        Notification.expires_at.is_(None),
                        Notification.expires_at > datetime.utcnow()
                    )
                )
            ).order_by(desc(Notification.created_at)).all()
            
            if not notifications:
                return []
            
            # Group notifications by similarity
            groups = self._create_notification_groups(notifications)
            
            # Update database groups
            await self._update_database_groups(db, groups, user_id)
            
            return groups
            
        except Exception as e:
            logger.error(f"Error grouping notifications for user {user_id}: {e}")
            raise
    
    def _create_notification_groups(
        self,
        notifications: List[Notification]
    ) -> List[Dict[str, Any]]:
        """Create notification groups based on similarity"""
        
        groups = []
        processed_notifications = set()
        
        for notification in notifications:
            if notification.id in processed_notifications:
                continue
            
            # Find similar notifications
            similar_notifications = [notification]
            processed_notifications.add(notification.id)
            
            for other_notification in notifications:
                if (other_notification.id != notification.id and 
                    other_notification.id not in processed_notifications):
                    
                    if self._are_notifications_similar(notification, other_notification):
                        similar_notifications.append(other_notification)
                        processed_notifications.add(other_notification.id)
            
            # Create group if there are multiple similar notifications
            if len(similar_notifications) > 1:
                group = self._create_group_from_notifications(similar_notifications)
                groups.append(group)
            else:
                # Single notification - add as individual item
                groups.append({
                    'type': 'individual',
                    'notification': self._notification_to_dict(notification),
                    'count': 1
                })
        
        return groups
    
    def _are_notifications_similar(
        self,
        notification1: Notification,
        notification2: Notification
    ) -> bool:
        """Check if two notifications are similar enough to group"""
        
        # Same category and type
        if (notification1.category != notification2.category or
            notification1.type != notification2.type):
            return False
        
        # Apply category-specific grouping rules
        category_rules = self.grouping_rules.get(notification1.category.value, {})
        
        # Check title similarity
        if category_rules.get('group_by_title_pattern'):
            pattern = category_rules['group_by_title_pattern']
            if (re.search(pattern, notification1.title) and 
                re.search(pattern, notification2.title)):
                return True
        
        # Check content similarity
        if category_rules.get('group_by_content_keywords'):
            keywords = category_rules['group_by_content_keywords']
            content1_lower = notification1.content.lower()
            content2_lower = notification2.content.lower()
            
            for keyword in keywords:
                if keyword in content1_lower and keyword in content2_lower:
                    return True
        
        # Check time proximity (within same hour)
        time_diff = abs((notification1.created_at - notification2.created_at).total_seconds())
        if time_diff < 3600:  # 1 hour
            # Check if titles are similar (Levenshtein distance)
            if self._calculate_similarity(notification1.title, notification2.title) > 0.7:
                return True
        
        return False
    
    def _create_group_from_notifications(
        self,
        notifications: List[Notification]
    ) -> Dict[str, Any]:
        """Create a group from similar notifications"""
        
        # Sort by priority and creation time
        notifications.sort(key=lambda n: (
            self._priority_weight(n.priority),
            n.created_at
        ), reverse=True)
        
        primary_notification = notifications[0]
        
        # Generate group key
        group_key = self._generate_group_key(notifications)
        
        # Create group summary
        group = {
            'type': 'group',
            'group_key': group_key,
            'title': self._generate_group_title(notifications),
            'description': self._generate_group_description(notifications),
            'category': primary_notification.category.value,
            'priority': self._determine_group_priority(notifications),
            'count': len(notifications),
            'notifications': [self._notification_to_dict(n) for n in notifications],
            'first_notification_at': min(n.created_at for n in notifications).isoformat(),
            'last_notification_at': max(n.created_at for n in notifications).isoformat(),
            'unread_count': sum(1 for n in notifications if n.read_at is None)
        }
        
        return group
    
    def _generate_group_key(self, notifications: List[Notification]) -> str:
        """Generate a unique key for the group"""
        
        # Use category, type, and content hash
        primary = notifications[0]
        content_hash = hashlib.md5(
            f"{primary.category.value}:{primary.type.value}:{primary.title[:50]}"
            .encode('utf-8')
        ).hexdigest()[:8]
        
        return f"{primary.category.value}_{content_hash}"
    
    def _generate_group_title(self, notifications: List[Notification]) -> str:
        """Generate a title for the group"""
        
        primary = notifications[0]
        count = len(notifications)
        
        # Category-specific titles
        if primary.category.value == 'system':
            return f"Системные уведомления ({count})"
        elif primary.category.value == 'moderation':
            return f"Требуется модерация ({count})"
        elif primary.category.value == 'project':
            return f"Обновления проекта ({count})"
        elif primary.category.value == 'marketing':
            return f"Маркетинговые события ({count})"
        elif primary.category.value == 'analytics':
            return f"Аналитические отчеты ({count})"
        elif primary.category.value == 'security':
            return f"Предупреждения безопасности ({count})"
        else:
            return f"Уведомления ({count})"
    
    def _generate_group_description(self, notifications: List[Notification]) -> str:
        """Generate a description for the group"""
        
        primary = notifications[0]
        count = len(notifications)
        
        if count == 2:
            return f"2 похожих уведомления в категории {primary.category.value}"
        else:
            return f"{count} похожих уведомлений в категории {primary.category.value}"
    
    def _determine_group_priority(self, notifications: List[Notification]) -> str:
        """Determine the priority for the group (highest priority wins)"""
        
        priority_weights = {
            NotificationPriority.CRITICAL: 4,
            NotificationPriority.HIGH: 3,
            NotificationPriority.MEDIUM: 2,
            NotificationPriority.LOW: 1
        }
        
        max_priority = max(notifications, key=lambda n: priority_weights.get(n.priority, 0))
        return max_priority.priority.value
    
    def _priority_weight(self, priority: NotificationPriority) -> int:
        """Get numeric weight for priority"""
        weights = {
            NotificationPriority.CRITICAL: 4,
            NotificationPriority.HIGH: 3,
            NotificationPriority.MEDIUM: 2,
            NotificationPriority.LOW: 1
        }
        return weights.get(priority, 0)
    
    def _notification_to_dict(self, notification: Notification) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return {
            'id': notification.id,
            'title': notification.title,
            'content': notification.content,
            'type': notification.type.value,
            'category': notification.category.value,
            'priority': notification.priority.value,
            'status': notification.status.value,
            'is_read': notification.read_at is not None,
            'is_starred': notification.is_starred,
            'action_url': notification.action_url,
            'action_text': notification.action_text,
            'created_at': notification.created_at.isoformat(),
            'read_at': notification.read_at.isoformat() if notification.read_at else None,
            'data': notification.data
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (simple implementation)"""
        
        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    async def _update_database_groups(
        self,
        db: Session,
        groups: List[Dict[str, Any]],
        user_id: int
    ):
        """Update notification groups in database"""
        try:
            for group_data in groups:
                if group_data['type'] != 'group':
                    continue
                
                group_key = group_data['group_key']
                
                # Check if group already exists
                existing_group = db.query(NotificationGroup).filter(
                    NotificationGroup.group_key == group_key
                ).first()
                
                if existing_group:
                    # Update existing group
                    existing_group.count = group_data['count']
                    existing_group.last_notification_at = datetime.fromisoformat(
                        group_data['last_notification_at']
                    )
                    existing_group.updated_at = datetime.utcnow()
                else:
                    # Create new group
                    new_group = NotificationGroup(
                        name=group_data['title'],
                        description=group_data['description'],
                        group_key=group_key,
                        category=NotificationCategory(group_data['category']),
                        priority=NotificationPriority(group_data['priority']),
                        count=group_data['count'],
                        status='active',
                        first_notification_at=datetime.fromisoformat(
                            group_data['first_notification_at']
                        ),
                        last_notification_at=datetime.fromisoformat(
                            group_data['last_notification_at']
                        ),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(new_group)
                
                # Update notifications with group key
                notification_ids = [n['id'] for n in group_data['notifications']]
                db.query(Notification).filter(
                    Notification.id.in_(notification_ids)
                ).update(
                    {'group_key': group_key},
                    synchronize_session=False
                )
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating database groups: {e}")
            raise
    
    # Spam detection and filtering
    async def detect_spam_notifications(
        self,
        db: Session,
        user_id: int,
        time_window_minutes: int = 60
    ) -> List[int]:
        """Detect spam notifications for a user"""
        try:
            time_threshold = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            
            notifications = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.created_at >= time_threshold,
                    Notification.dismissed_at.is_(None)
                )
            ).all()
            
            spam_notification_ids = []
            
            # Apply spam detection rules
            for rule in self.spam_detection_rules:
                spam_ids = self._apply_spam_rule(notifications, rule)
                spam_notification_ids.extend(spam_ids)
            
            return list(set(spam_notification_ids))
            
        except Exception as e:
            logger.error(f"Error detecting spam notifications: {e}")
            return []
    
    def _apply_spam_rule(
        self,
        notifications: List[Notification],
        rule: Dict[str, Any]
    ) -> List[int]:
        """Apply a spam detection rule"""
        
        spam_ids = []
        
        if rule['type'] == 'frequency':
            # Detect notifications with same title/content appearing too frequently
            content_counts = defaultdict(list)
            
            for notification in notifications:
                key = f"{notification.title}:{notification.content[:100]}"
                content_counts[key].append(notification)
            
            for content, notifs in content_counts.items():
                if len(notifs) > rule['max_count']:
                    # Mark all but the first as spam
                    spam_ids.extend([n.id for n in notifs[1:]])
        
        elif rule['type'] == 'pattern':
            # Detect notifications matching spam patterns
            pattern = rule['pattern']
            
            for notification in notifications:
                if re.search(pattern, notification.content, re.IGNORECASE):
                    spam_ids.append(notification.id)
        
        elif rule['type'] == 'burst':
            # Detect burst of notifications from same source
            category_counts = defaultdict(list)
            
            for notification in notifications:
                category_counts[notification.category].append(notification)
            
            for category, notifs in category_counts.items():
                if len(notifs) > rule['max_burst']:
                    # Sort by creation time and mark excess as spam
                    notifs.sort(key=lambda n: n.created_at)
                    spam_ids.extend([n.id for n in notifs[rule['max_burst']:]])
        
        return spam_ids
    
    # Auto-dismiss expired notifications
    async def auto_dismiss_expired_notifications(
        self,
        db: Session,
        user_id: Optional[int] = None
    ) -> int:
        """Auto-dismiss expired notifications"""
        try:
            query = db.query(Notification).filter(
                and_(
                    Notification.expires_at.isnot(None),
                    Notification.expires_at < datetime.utcnow(),
                    Notification.dismissed_at.is_(None)
                )
            )
            
            if user_id:
                query = query.filter(Notification.user_id == user_id)
            
            # Update expired notifications
            updated_count = query.update(
                {
                    'dismissed_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'status': NotificationStatus.DISMISSED
                },
                synchronize_session=False
            )
            
            db.commit()
            
            if updated_count > 0:
                logger.info(f"Auto-dismissed {updated_count} expired notifications")
            
            return updated_count
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error auto-dismissing expired notifications: {e}")
            return 0
    
    # Auto-dismiss based on rules
    async def auto_dismiss_by_rules(
        self,
        db: Session,
        user_id: int
    ) -> int:
        """Auto-dismiss notifications based on rules"""
        try:
            dismissed_count = 0
            
            for rule in self.auto_dismiss_rules:
                count = await self._apply_auto_dismiss_rule(db, user_id, rule)
                dismissed_count += count
            
            return dismissed_count
            
        except Exception as e:
            logger.error(f"Error auto-dismissing by rules: {e}")
            return 0
    
    async def _apply_auto_dismiss_rule(
        self,
        db: Session,
        user_id: int,
        rule: Dict[str, Any]
    ) -> int:
        """Apply an auto-dismiss rule"""
        
        try:
            query = db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.dismissed_at.is_(None)
                )
            )
            
            # Apply rule conditions
            if rule['type'] == 'age':
                # Dismiss notifications older than specified age
                age_threshold = datetime.utcnow() - timedelta(days=rule['max_age_days'])
                query = query.filter(Notification.created_at < age_threshold)
            
            elif rule['type'] == 'category_limit':
                # Dismiss excess notifications in category (keep only latest N)
                category = NotificationCategory(rule['category'])
                
                # Get notifications in category, ordered by creation time (newest first)
                category_notifications = db.query(Notification).filter(
                    and_(
                        Notification.user_id == user_id,
                        Notification.category == category,
                        Notification.dismissed_at.is_(None)
                    )
                ).order_by(desc(Notification.created_at)).all()
                
                if len(category_notifications) > rule['max_count']:
                    # Dismiss excess notifications
                    excess_notifications = category_notifications[rule['max_count']:]
                    excess_ids = [n.id for n in excess_notifications]
                    
                    updated_count = db.query(Notification).filter(
                        Notification.id.in_(excess_ids)
                    ).update(
                        {
                            'dismissed_at': datetime.utcnow(),
                            'updated_at': datetime.utcnow(),
                            'status': NotificationStatus.DISMISSED
                        },
                        synchronize_session=False
                    )
                    
                    db.commit()
                    return updated_count
            
            elif rule['type'] == 'read_age':
                # Dismiss read notifications older than specified age
                age_threshold = datetime.utcnow() - timedelta(days=rule['max_read_age_days'])
                query = query.filter(
                    and_(
                        Notification.read_at.isnot(None),
                        Notification.read_at < age_threshold
                    )
                )
            
            # Execute update for age and read_age rules
            if rule['type'] in ['age', 'read_age']:
                updated_count = query.update(
                    {
                        'dismissed_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow(),
                        'status': NotificationStatus.DISMISSED
                    },
                    synchronize_session=False
                )
                
                db.commit()
                return updated_count
            
            return 0
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error applying auto-dismiss rule: {e}")
            return 0
    
    # Configuration
    def _load_grouping_rules(self) -> Dict[str, Any]:
        """Load notification grouping rules"""
        return {
            'system': {
                'group_by_title_pattern': r'(ошибка|error|сбой|failure)',
                'group_by_content_keywords': ['система', 'сервис', 'база данных', 'сервер']
            },
            'moderation': {
                'group_by_title_pattern': r'(модерация|moderation|проверка)',
                'group_by_content_keywords': ['требуется', 'проверить', 'модерировать']
            },
            'project': {
                'group_by_title_pattern': r'(задача|task|проект|project)',
                'group_by_content_keywords': ['назначена', 'завершена', 'просрочена']
            },
            'marketing': {
                'group_by_title_pattern': r'(кампания|campaign|реклама)',
                'group_by_content_keywords': ['запущена', 'завершена', 'статистика']
            },
            'analytics': {
                'group_by_title_pattern': r'(отчет|report|аналитика)',
                'group_by_content_keywords': ['готов', 'сформирован', 'данные']
            },
            'security': {
                'group_by_title_pattern': r'(безопасность|security|угроза)',
                'group_by_content_keywords': ['подозрительно', 'заблокирован', 'попытка']
            }
        }
    
    def _load_spam_detection_rules(self) -> List[Dict[str, Any]]:
        """Load spam detection rules"""
        return [
            {
                'type': 'frequency',
                'max_count': 5,  # Max 5 identical notifications per hour
                'description': 'Detect duplicate notifications'
            },
            {
                'type': 'burst',
                'max_burst': 10,  # Max 10 notifications per category per hour
                'description': 'Detect notification bursts'
            },
            {
                'type': 'pattern',
                'pattern': r'(тест|test|debug|отладка)',
                'description': 'Detect test/debug notifications'
            }
        ]
    
    def _load_auto_dismiss_rules(self) -> List[Dict[str, Any]]:
        """Load auto-dismiss rules"""
        return [
            {
                'type': 'age',
                'max_age_days': 30,
                'description': 'Dismiss notifications older than 30 days'
            },
            {
                'type': 'read_age',
                'max_read_age_days': 7,
                'description': 'Dismiss read notifications older than 7 days'
            },
            {
                'type': 'category_limit',
                'category': 'system',
                'max_count': 50,
                'description': 'Keep only latest 50 system notifications'
            },
            {
                'type': 'category_limit',
                'category': 'analytics',
                'max_count': 20,
                'description': 'Keep only latest 20 analytics notifications'
            }
        ]


# Create service instance
notification_grouping_service = NotificationGroupingService()