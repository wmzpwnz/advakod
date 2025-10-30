import smtplib
import ssl
import json
import aiohttp
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import os
from jinja2 import Template

from ..models.notification import NotificationChannel, ChannelType
from ..core.config import settings

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.smtp_configs = {}
        self.templates = {}
        
    async def send_email(
        self,
        channel: NotificationChannel,
        recipient_email: str,
        subject: str,
        content: str,
        html_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send email notification"""
        try:
            config = channel.configuration
            
            # Validate configuration
            required_fields = ['smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required email configuration: {field}")
            
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = f"{config.get('from_name', 'АДВАКОД')} <{config['from_email']}>"
            message['To'] = recipient_email
            message['Subject'] = subject
            
            # Add text content
            text_part = MIMEText(content, 'plain', 'utf-8')
            message.attach(text_part)
            
            # Add HTML content if provided
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                message.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    message.attach(part)
            
            # Send email
            context = ssl.create_default_context()
            
            with smtplib.SMTP(config['smtp_host'], config['smtp_port']) as server:
                if config.get('use_tls', True):
                    server.starttls(context=context)
                
                server.login(config['smtp_username'], config['smtp_password'])
                server.send_message(message)
            
            logger.info(f"Email sent successfully to {recipient_email}")
            
            return {
                'success': True,
                'message': 'Email sent successfully',
                'recipient': recipient_email,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending email to {recipient_email}: {e}")
            return {
                'success': False,
                'error': str(e),
                'recipient': recipient_email,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def render_template(self, template_content: str, variables: Dict[str, Any]) -> str:
        """Render email template with variables"""
        try:
            template = Template(template_content)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"Error rendering email template: {e}")
            return template_content


class SlackNotificationService:
    """Service for sending Slack notifications"""
    
    def __init__(self):
        self.session = None
        
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def send_slack_message(
        self,
        channel: NotificationChannel,
        message: str,
        title: Optional[str] = None,
        color: str = 'good',
        fields: Optional[List[Dict[str, Any]]] = None,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send Slack notification"""
        try:
            config = channel.configuration
            
            # Validate configuration
            if 'webhook_url' not in config and 'bot_token' not in config:
                raise ValueError("Missing Slack webhook URL or bot token")
            
            session = await self.get_session()
            
            if 'webhook_url' in config:
                # Use webhook
                return await self._send_webhook_message(
                    session, config, message, title, color, fields, actions
                )
            else:
                # Use bot token
                return await self._send_bot_message(
                    session, config, message, title, color, fields, actions
                )
                
        except Exception as e:
            logger.error(f"Error sending Slack message: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _send_webhook_message(
        self,
        session: aiohttp.ClientSession,
        config: Dict[str, Any],
        message: str,
        title: Optional[str],
        color: str,
        fields: Optional[List[Dict[str, Any]]],
        actions: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Send message via webhook"""
        
        # Build attachment
        attachment = {
            'color': color,
            'text': message,
            'ts': int(datetime.utcnow().timestamp())
        }
        
        if title:
            attachment['title'] = title
        
        if fields:
            attachment['fields'] = fields
        
        if actions:
            attachment['actions'] = actions
        
        payload = {
            'username': config.get('username', 'АДВАКОД'),
            'icon_emoji': config.get('icon_emoji', ':robot_face:'),
            'channel': config.get('channel', '#general'),
            'attachments': [attachment]
        }
        
        async with session.post(config['webhook_url'], json=payload) as response:
            if response.status == 200:
                logger.info("Slack webhook message sent successfully")
                return {
                    'success': True,
                    'message': 'Slack message sent successfully',
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                error_text = await response.text()
                raise Exception(f"Slack webhook error: {response.status} - {error_text}")
    
    async def _send_bot_message(
        self,
        session: aiohttp.ClientSession,
        config: Dict[str, Any],
        message: str,
        title: Optional[str],
        color: str,
        fields: Optional[List[Dict[str, Any]]],
        actions: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Send message via bot token"""
        
        headers = {
            'Authorization': f"Bearer {config['bot_token']}",
            'Content-Type': 'application/json'
        }
        
        # Build blocks for rich formatting
        blocks = []
        
        if title:
            blocks.append({
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': title
                }
            })
        
        blocks.append({
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': message
            }
        })
        
        if fields:
            field_blocks = []
            for field in fields:
                field_blocks.append({
                    'type': 'mrkdwn',
                    'text': f"*{field.get('title', '')}*\n{field.get('value', '')}"
                })
            
            blocks.append({
                'type': 'section',
                'fields': field_blocks
            })
        
        payload = {
            'channel': config.get('channel', '#general'),
            'blocks': blocks
        }
        
        async with session.post(
            'https://slack.com/api/chat.postMessage',
            headers=headers,
            json=payload
        ) as response:
            result = await response.json()
            
            if result.get('ok'):
                logger.info("Slack bot message sent successfully")
                return {
                    'success': True,
                    'message': 'Slack message sent successfully',
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                raise Exception(f"Slack API error: {result.get('error', 'Unknown error')}")
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None


class TelegramNotificationService:
    """Service for sending Telegram notifications"""
    
    def __init__(self):
        self.session = None
        
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def send_telegram_message(
        self,
        channel: NotificationChannel,
        message: str,
        parse_mode: str = 'HTML',
        disable_web_page_preview: bool = True,
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send Telegram notification"""
        try:
            config = channel.configuration
            
            # Validate configuration
            required_fields = ['bot_token', 'chat_id']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required Telegram configuration: {field}")
            
            session = await self.get_session()
            
            url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
            
            payload = {
                'chat_id': config['chat_id'],
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': disable_web_page_preview
            }
            
            if reply_markup:
                payload['reply_markup'] = json.dumps(reply_markup)
            
            async with session.post(url, json=payload) as response:
                result = await response.json()
                
                if result.get('ok'):
                    logger.info(f"Telegram message sent successfully to chat {config['chat_id']}")
                    return {
                        'success': True,
                        'message': 'Telegram message sent successfully',
                        'message_id': result['result']['message_id'],
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    raise Exception(f"Telegram API error: {result.get('description', 'Unknown error')}")
                    
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def send_telegram_photo(
        self,
        channel: NotificationChannel,
        photo_url: str,
        caption: Optional[str] = None,
        parse_mode: str = 'HTML'
    ) -> Dict[str, Any]:
        """Send Telegram photo notification"""
        try:
            config = channel.configuration
            
            session = await self.get_session()
            
            url = f"https://api.telegram.org/bot{config['bot_token']}/sendPhoto"
            
            payload = {
                'chat_id': config['chat_id'],
                'photo': photo_url,
                'parse_mode': parse_mode
            }
            
            if caption:
                payload['caption'] = caption
            
            async with session.post(url, json=payload) as response:
                result = await response.json()
                
                if result.get('ok'):
                    logger.info(f"Telegram photo sent successfully to chat {config['chat_id']}")
                    return {
                        'success': True,
                        'message': 'Telegram photo sent successfully',
                        'message_id': result['result']['message_id'],
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    raise Exception(f"Telegram API error: {result.get('description', 'Unknown error')}")
                    
        except Exception as e:
            logger.error(f"Error sending Telegram photo: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def format_message(
        self,
        title: str,
        content: str,
        priority: str = 'medium',
        category: str = 'system',
        action_url: Optional[str] = None
    ) -> str:
        """Format message for Telegram"""
        
        # Priority emoji
        priority_emojis = {
            'low': '🔵',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        
        # Category emoji
        category_emojis = {
            'system': '⚙️',
            'marketing': '📈',
            'moderation': '🛡️',
            'project': '📋',
            'analytics': '📊',
            'security': '🔒'
        }
        
        emoji = priority_emojis.get(priority, '🔵')
        cat_emoji = category_emojis.get(category, '⚙️')
        
        message = f"{emoji} <b>{title}</b>\n\n"
        message += f"{cat_emoji} <i>{category.upper()}</i>\n\n"
        message += f"{content}"
        
        if action_url:
            message += f"\n\n🔗 <a href='{action_url}'>Открыть</a>"
        
        return message
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None


class WebhookNotificationService:
    """Service for sending webhook notifications"""
    
    def __init__(self):
        self.session = None
        
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def send_webhook(
        self,
        channel: NotificationChannel,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Send webhook notification"""
        try:
            config = channel.configuration
            
            # Validate configuration
            if 'url' not in config:
                raise ValueError("Missing webhook URL")
            
            session = await self.get_session()
            
            # Prepare headers
            request_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'ADVAKOD-Notification-Service/1.0'
            }
            
            # Add custom headers from configuration
            if 'headers' in config:
                request_headers.update(config['headers'])
            
            # Add headers from parameters
            if headers:
                request_headers.update(headers)
            
            # Add authentication if configured
            auth_config = config.get('authentication', {})
            auth_type = auth_config.get('type', 'none')
            
            if auth_type == 'bearer':
                request_headers['Authorization'] = f"Bearer {auth_config['credentials']['token']}"
            elif auth_type == 'api_key':
                key_name = auth_config['credentials']['key_name']
                key_value = auth_config['credentials']['key_value']
                request_headers[key_name] = key_value
            elif auth_type == 'basic':
                import base64
                username = auth_config['credentials']['username']
                password = auth_config['credentials']['password']
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                request_headers['Authorization'] = f"Basic {credentials}"
            
            # Send webhook
            method = config.get('method', 'POST').upper()
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with session.request(
                method,
                config['url'],
                json=payload,
                headers=request_headers,
                timeout=timeout
            ) as response:
                
                response_text = await response.text()
                
                if 200 <= response.status < 300:
                    logger.info(f"Webhook sent successfully to {config['url']}")
                    return {
                        'success': True,
                        'message': 'Webhook sent successfully',
                        'status_code': response.status,
                        'response': response_text,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    raise Exception(f"Webhook error: {response.status} - {response_text}")
                    
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def create_standard_payload(
        self,
        title: str,
        content: str,
        priority: str = 'medium',
        category: str = 'system',
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create standard webhook payload"""
        
        payload = {
            'title': title,
            'content': content,
            'priority': priority,
            'category': category,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'ADVAKOD'
        }
        
        if action_url:
            payload['action_url'] = action_url
        
        if metadata:
            payload['metadata'] = metadata
        
        return payload
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None


class ExternalNotificationService:
    """Main service for managing external notifications"""
    
    def __init__(self):
        self.email_service = EmailNotificationService()
        self.slack_service = SlackNotificationService()
        self.telegram_service = TelegramNotificationService()
        self.webhook_service = WebhookNotificationService()
        
    async def send_notification(
        self,
        channel: NotificationChannel,
        title: str,
        content: str,
        priority: str = 'medium',
        category: str = 'system',
        action_url: Optional[str] = None,
        recipient: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send notification via external channel with enhanced error handling"""
        
        start_time = datetime.utcnow()
        
        try:
            # Validate inputs
            if not channel:
                raise ValueError("Channel is required")
            if not title or not content:
                raise ValueError("Title and content are required")
            
            logger.info(f"Sending notification via {channel.type.value} channel: {channel.name}")
            
            result = None
            
            if channel.type == ChannelType.EMAIL:
                if not recipient:
                    # Try to get default recipient from channel config
                    recipient = channel.configuration.get('default_recipient', 'admin@advacodex.com')
                    logger.info(f"Using default email recipient: {recipient}")
                
                # Render HTML content if needed
                html_content = self._render_html_email(title, content, priority, category, action_url)
                
                result = await self.email_service.send_email(
                    channel=channel,
                    recipient_email=recipient,
                    subject=title,
                    content=content,
                    html_content=html_content
                )
                
            elif channel.type == ChannelType.SLACK:
                # Format for Slack
                color = self._get_slack_color(priority)
                fields = [
                    {'title': 'Категория', 'value': category.upper(), 'short': True},
                    {'title': 'Приоритет', 'value': priority.upper(), 'short': True}
                ]
                
                actions = []
                if action_url:
                    actions.append({
                        'type': 'button',
                        'text': 'Открыть',
                        'url': action_url
                    })
                
                result = await self.slack_service.send_slack_message(
                    channel=channel,
                    message=content,
                    title=title,
                    color=color,
                    fields=fields,
                    actions=actions
                )
                
            elif channel.type == ChannelType.TELEGRAM:
                # Format for Telegram
                formatted_message = self.telegram_service.format_message(
                    title=title,
                    content=content,
                    priority=priority,
                    category=category,
                    action_url=action_url
                )
                
                result = await self.telegram_service.send_telegram_message(
                    channel=channel,
                    message=formatted_message
                )
                
            elif channel.type == ChannelType.WEBHOOK:
                # Create webhook payload
                payload = self.webhook_service.create_standard_payload(
                    title=title,
                    content=content,
                    priority=priority,
                    category=category,
                    action_url=action_url,
                    metadata=metadata
                )
                
                result = await self.webhook_service.send_webhook(
                    channel=channel,
                    payload=payload
                )
                
            else:
                raise ValueError(f"Unsupported channel type: {channel.type}")
            
            # Add timing information to result
            if result:
                duration = (datetime.utcnow() - start_time).total_seconds()
                result['duration_seconds'] = duration
                result['channel_name'] = channel.name
                result['channel_id'] = channel.id
                
                if result.get('success'):
                    logger.info(f"Notification sent successfully via {channel.type.value} in {duration:.2f}s")
                else:
                    logger.warning(f"Notification failed via {channel.type.value}: {result.get('error', 'Unknown error')}")
            
            return result or {
                'success': False,
                'error': 'No result returned from notification service',
                'channel_type': channel.type.value,
                'timestamp': datetime.utcnow().isoformat()
            }
                
        except ValueError as ve:
            logger.error(f"Validation error sending notification: {ve}")
            return {
                'success': False,
                'error': f"Validation error: {str(ve)}",
                'error_type': 'validation_error',
                'channel_type': channel.type.value if channel else 'unknown',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error sending external notification via {channel.type.value if channel else 'unknown'}: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'channel_type': channel.type.value if channel else 'unknown',
                'duration_seconds': duration,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _render_html_email(
        self,
        title: str,
        content: str,
        priority: str,
        category: str,
        action_url: Optional[str] = None
    ) -> str:
        """Render HTML email template"""
        
        # Priority colors
        priority_colors = {
            'low': '#3B82F6',
            'medium': '#F59E0B',
            'high': '#F97316',
            'critical': '#EF4444'
        }
        
        color = priority_colors.get(priority, '#3B82F6')
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="border-left: 4px solid {color}; padding-left: 20px; margin-bottom: 20px;">
                <h1 style="color: {color}; margin: 0 0 10px 0;">{title}</h1>
                <p style="margin: 0; color: #666; font-size: 14px;">
                    <strong>Категория:</strong> {category.upper()} | 
                    <strong>Приоритет:</strong> {priority.upper()}
                </p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <p style="margin: 0; white-space: pre-line;">{content}</p>
            </div>
            
            {f'<div style="text-align: center; margin: 20px 0;"><a href="{action_url}" style="background: {color}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Открыть</a></div>' if action_url else ''}
            
            <div style="border-top: 1px solid #eee; padding-top: 20px; margin-top: 30px; text-align: center; color: #666; font-size: 12px;">
                <p>Это уведомление отправлено системой АДВАКОД - ИИ-Юрист для РФ</p>
                <p>Если у вас есть вопросы, обратитесь к администратору системы.</p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _get_slack_color(self, priority: str) -> str:
        """Get Slack color for priority"""
        colors = {
            'low': 'good',
            'medium': 'warning',
            'high': 'warning',
            'critical': 'danger'
        }
        return colors.get(priority, 'good')
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on external notification services"""
        health_results = {
            'overall_status': 'healthy',
            'services': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        unhealthy_count = 0
        
        # Check email service
        try:
            health_results['services']['email'] = {
                'status': 'healthy',
                'message': 'Email service available'
            }
        except Exception as e:
            health_results['services']['email'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            unhealthy_count += 1
        
        # Check Slack service
        try:
            if self.slack_service.session:
                health_results['services']['slack'] = {
                    'status': 'healthy',
                    'message': 'Slack service session active'
                }
            else:
                health_results['services']['slack'] = {
                    'status': 'healthy',
                    'message': 'Slack service available (no active session)'
                }
        except Exception as e:
            health_results['services']['slack'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            unhealthy_count += 1
        
        # Check Telegram service
        try:
            if self.telegram_service.session:
                health_results['services']['telegram'] = {
                    'status': 'healthy',
                    'message': 'Telegram service session active'
                }
            else:
                health_results['services']['telegram'] = {
                    'status': 'healthy',
                    'message': 'Telegram service available (no active session)'
                }
        except Exception as e:
            health_results['services']['telegram'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            unhealthy_count += 1
        
        # Check webhook service
        try:
            if self.webhook_service.session:
                health_results['services']['webhook'] = {
                    'status': 'healthy',
                    'message': 'Webhook service session active'
                }
            else:
                health_results['services']['webhook'] = {
                    'status': 'healthy',
                    'message': 'Webhook service available (no active session)'
                }
        except Exception as e:
            health_results['services']['webhook'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            unhealthy_count += 1
        
        # Determine overall status
        total_services = len(health_results['services'])
        if unhealthy_count == 0:
            health_results['overall_status'] = 'healthy'
        elif unhealthy_count == total_services:
            health_results['overall_status'] = 'unhealthy'
        else:
            health_results['overall_status'] = 'degraded'
        
        health_results['healthy_services'] = total_services - unhealthy_count
        health_results['total_services'] = total_services
        
        return health_results
    
    async def close(self):
        """Close all external services"""
        try:
            await self.slack_service.close()
        except Exception as e:
            logger.error(f"Error closing Slack service: {e}")
            
        try:
            await self.telegram_service.close()
        except Exception as e:
            logger.error(f"Error closing Telegram service: {e}")
            
        try:
            await self.webhook_service.close()
        except Exception as e:
            logger.error(f"Error closing Webhook service: {e}")


# Create service instance
external_notification_service = ExternalNotificationService()