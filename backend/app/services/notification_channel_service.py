from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ..models.notification import NotificationChannel, ChannelType
from ..schemas.notification import (
    NotificationChannelCreate, NotificationChannelUpdate
)
from .external_notification_service import external_notification_service

logger = logging.getLogger(__name__)


class NotificationChannelService:
    """Service for managing notification channels"""
    
    def __init__(self):
        self.external_service = external_notification_service
    
    # Channel CRUD operations
    async def create_channel(
        self,
        db: Session,
        channel_data: NotificationChannelCreate
    ) -> NotificationChannel:
        """Create a new notification channel"""
        try:
            # Validate channel configuration
            await self._validate_channel_config(channel_data.type, channel_data.configuration)
            
            # Create channel
            db_channel = NotificationChannel(
                name=channel_data.name,
                type=channel_data.type,
                is_active=True,
                configuration=channel_data.configuration,
                rate_limit_per_minute=channel_data.rate_limit_per_minute,
                rate_limit_per_hour=channel_data.rate_limit_per_hour,
                rate_limit_per_day=channel_data.rate_limit_per_day,
                max_retries=channel_data.max_retries,
                retry_delay_seconds=channel_data.retry_delay_seconds,
                total_sent=0,
                total_failed=0,
                success_rate=0.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(db_channel)
            db.commit()
            db.refresh(db_channel)
            
            logger.info(f"Created notification channel {db_channel.id}: {db_channel.name}")
            return db_channel
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating notification channel: {e}")
            raise
    
    async def get_channels(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        channel_type: Optional[List[ChannelType]] = None,
        is_active: Optional[bool] = None
    ) -> List[NotificationChannel]:
        """Get notification channels with optional filtering"""
        try:
            query = db.query(NotificationChannel)
            
            if channel_type:
                query = query.filter(NotificationChannel.type.in_(channel_type))
            
            if is_active is not None:
                query = query.filter(NotificationChannel.is_active == is_active)
            
            channels = query.offset(skip).limit(limit).all()
            return channels
            
        except Exception as e:
            logger.error(f"Error getting notification channels: {e}")
            raise
    
    async def get_channel(self, db: Session, channel_id: int) -> Optional[NotificationChannel]:
        """Get a specific notification channel"""
        try:
            channel = db.query(NotificationChannel).filter(
                NotificationChannel.id == channel_id
            ).first()
            return channel
        except Exception as e:
            logger.error(f"Error getting notification channel {channel_id}: {e}")
            raise
    
    async def update_channel(
        self,
        db: Session,
        channel_id: int,
        channel_data: NotificationChannelUpdate
    ) -> Optional[NotificationChannel]:
        """Update a notification channel"""
        try:
            channel = await self.get_channel(db, channel_id)
            if not channel:
                return None
            
            # Validate configuration if being updated
            if channel_data.configuration:
                await self._validate_channel_config(channel.type, channel_data.configuration)
            
            # Update fields
            for field, value in channel_data.dict(exclude_unset=True).items():
                setattr(channel, field, value)
            
            channel.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(channel)
            
            logger.info(f"Updated notification channel {channel_id}")
            return channel
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating notification channel {channel_id}: {e}")
            raise
    
    async def delete_channel(self, db: Session, channel_id: int) -> bool:
        """Delete a notification channel"""
        try:
            channel = await self.get_channel(db, channel_id)
            if not channel:
                return False
            
            db.delete(channel)
            db.commit()
            
            logger.info(f"Deleted notification channel {channel_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting notification channel {channel_id}: {e}")
            raise
    
    # Channel validation
    async def _validate_channel_config(
        self,
        channel_type: ChannelType,
        configuration: Dict[str, Any]
    ):
        """Validate channel configuration"""
        
        if channel_type == ChannelType.EMAIL:
            required_fields = ['smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email']
            for field in required_fields:
                if field not in configuration:
                    raise ValueError(f"Missing required email configuration: {field}")
        
        elif channel_type == ChannelType.SLACK:
            if 'webhook_url' not in configuration and 'bot_token' not in configuration:
                raise ValueError("Slack channel requires either webhook_url or bot_token")
        
        elif channel_type == ChannelType.TELEGRAM:
            required_fields = ['bot_token', 'chat_id']
            for field in required_fields:
                if field not in configuration:
                    raise ValueError(f"Missing required Telegram configuration: {field}")
        
        elif channel_type == ChannelType.WEBHOOK:
            if 'url' not in configuration:
                raise ValueError("Webhook channel requires url")
        
        elif channel_type == ChannelType.SMS:
            required_fields = ['api_key', 'api_secret', 'sender_id']
            for field in required_fields:
                if field not in configuration:
                    raise ValueError(f"Missing required SMS configuration: {field}")
    
    # Channel testing
    async def test_channel(
        self,
        db: Session,
        channel_id: int,
        test_message: str = "Тестовое сообщение от системы АДВАКОД"
    ) -> Dict[str, Any]:
        """Test notification channel"""
        try:
            channel = await self.get_channel(db, channel_id)
            if not channel:
                raise ValueError("Channel not found")
            
            if not channel.is_active:
                raise ValueError("Channel is not active")
            
            # Send test notification
            result = await self.external_service.send_notification(
                channel=channel,
                title="Тест уведомления",
                content=test_message,
                priority="low",
                category="system",
                recipient="test@example.com" if channel.type == ChannelType.EMAIL else None
            )
            
            # Update channel statistics
            if result.get('success'):
                channel.total_sent += 1
                channel.last_used_at = datetime.utcnow()
            else:
                channel.total_failed += 1
            
            # Recalculate success rate
            total_attempts = channel.total_sent + channel.total_failed
            if total_attempts > 0:
                channel.success_rate = (channel.total_sent / total_attempts) * 100
            
            channel.updated_at = datetime.utcnow()
            db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing notification channel {channel_id}: {e}")
            raise
    
    # Channel statistics
    async def get_channel_stats(
        self,
        db: Session,
        channel_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get channel statistics"""
        try:
            channel = await self.get_channel(db, channel_id)
            if not channel:
                raise ValueError("Channel not found")
            
            # Get basic stats from channel
            stats = {
                'channel_id': channel.id,
                'channel_name': channel.name,
                'channel_type': channel.type.value,
                'is_active': channel.is_active,
                'total_sent': channel.total_sent,
                'total_failed': channel.total_failed,
                'success_rate': channel.success_rate,
                'last_used_at': channel.last_used_at.isoformat() if channel.last_used_at else None,
                'created_at': channel.created_at.isoformat(),
                'updated_at': channel.updated_at.isoformat() if channel.updated_at else None
            }
            
            # TODO: Add more detailed statistics from notification_history table
            # This would require querying the notification_history table for this channel
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting channel stats for {channel_id}: {e}")
            raise
    
    # Bulk operations
    async def bulk_update_channels(
        self,
        db: Session,
        channel_ids: List[int],
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bulk update channels"""
        try:
            updated_count = 0
            errors = []
            
            for channel_id in channel_ids:
                try:
                    channel = await self.get_channel(db, channel_id)
                    if not channel:
                        errors.append({"channel_id": channel_id, "error": "Channel not found"})
                        continue
                    
                    # Apply updates
                    for field, value in updates.items():
                        if hasattr(channel, field):
                            setattr(channel, field, value)
                    
                    channel.updated_at = datetime.utcnow()
                    updated_count += 1
                    
                except Exception as e:
                    errors.append({"channel_id": channel_id, "error": str(e)})
            
            if updated_count > 0:
                db.commit()
            
            return {
                "updated_count": updated_count,
                "errors": errors,
                "success": updated_count > 0
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in bulk channel update: {e}")
            raise
    
    # Channel health check
    async def health_check_all_channels(self, db: Session) -> Dict[str, Any]:
        """Perform health check on all active channels"""
        try:
            channels = await self.get_channels(db, is_active=True)
            
            results = {
                'total_channels': len(channels),
                'healthy_channels': 0,
                'unhealthy_channels': 0,
                'channel_results': []
            }
            
            for channel in channels:
                try:
                    # Simple health check - just validate configuration
                    await self._validate_channel_config(channel.type, channel.configuration)
                    
                    results['healthy_channels'] += 1
                    results['channel_results'].append({
                        'channel_id': channel.id,
                        'channel_name': channel.name,
                        'channel_type': channel.type.value,
                        'status': 'healthy',
                        'last_check': datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    results['unhealthy_channels'] += 1
                    results['channel_results'].append({
                        'channel_id': channel.id,
                        'channel_name': channel.name,
                        'channel_type': channel.type.value,
                        'status': 'unhealthy',
                        'error': str(e),
                        'last_check': datetime.utcnow().isoformat()
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in channel health check: {e}")
            raise


# Create service instance
notification_channel_service = NotificationChannelService()