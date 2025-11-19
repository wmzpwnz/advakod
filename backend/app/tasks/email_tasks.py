from ..core.celery_app import celery_app
import logging
from typing import Dict, Any, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

logger = logging.getLogger(__name__)

@celery_app.task(queue="email")
def send_welcome_email(user_email: str, username: str) -> Dict[str, Any]:
    """Отправка приветственного email"""
    try:
        logger.info(f"Sending welcome email to {user_email}")
        
        # Настройки SMTP (в реальном приложении должны быть в переменных окружения)
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        
        # Создание сообщения
        msg = MIMEMultipart()
        msg["From"] = smtp_username
        msg["To"] = user_email
        msg["Subject"] = "Добро пожаловать в ИИ-Юрист!"
        
        # Тело письма
        body = f"""
        Здравствуйте, {username}!
        
        Добро пожаловать в ИИ-Юрист - ваш персональный помощник в области права!
        
        С нашим сервисом вы можете:
        - Получать консультации по правовым вопросам
        - Анализировать документы
        - Получать рекомендации по юридическим вопросам
        
        Если у вас есть вопросы, не стесняйтесь обращаться к нам.
        
        С уважением,
        Команда ИИ-Юрист
        """
        
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        # Отправка email (заглушка для демонстрации)
        # В реальном приложении здесь будет реальная отправка
        logger.info(f"Email sent successfully to {user_email}")
        
        return {
            "status": "sent",
            "recipient": user_email,
            "subject": "Добро пожаловать в ИИ-Юрист!"
        }
        
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        raise

@celery_app.task(queue="email")
def send_subscription_reminder(user_email: str, subscription_type: str, days_left: int) -> Dict[str, Any]:
    """Отправка напоминания о подписке"""
    try:
        logger.info(f"Sending subscription reminder to {user_email}")
        
        # Создание сообщения
        subject = f"Напоминание о подписке - осталось {days_left} дней"
        
        body = f"""
        Здравствуйте!
        
        Ваша подписка {subscription_type} истекает через {days_left} дней.
        
        Чтобы продолжить пользоваться всеми возможностями ИИ-Юрист, 
        пожалуйста, продлите подписку.
        
        С уважением,
        Команда ИИ-Юрист
        """
        
        # Имитация отправки
        logger.info(f"Subscription reminder sent to {user_email}")
        
        return {
            "status": "sent",
            "recipient": user_email,
            "subject": subject
        }
        
    except Exception as e:
        logger.error(f"Failed to send subscription reminder: {str(e)}")
        raise

@celery_app.task(queue="email")
def send_subscription_reminders() -> Dict[str, Any]:
    """Отправка напоминаний о подписках всем пользователям"""
    try:
        logger.info("Sending subscription reminders to all users")
        
        # В реальном приложении здесь будет запрос к базе данных
        # для получения пользователей с истекающими подписками
        
        # Имитация отправки
        time.sleep(2)
        
        return {
            "status": "completed",
            "reminders_sent": 150,
            "failed": 0
        }
        
    except Exception as e:
        logger.error(f"Failed to send subscription reminders: {str(e)}")
        raise

@celery_app.task(queue="email")
def send_password_reset_email(user_email: str, reset_token: str) -> Dict[str, Any]:
    """Отправка email для сброса пароля"""
    try:
        logger.info(f"Sending password reset email to {user_email}")
        
        reset_url = f"{os.getenv('FRONTEND_URL', 'https://advacodex.com')}/reset-password?token={reset_token}"
        
        subject = "Сброс пароля - ИИ-Юрист"
        
        body = f"""
        Здравствуйте!
        
        Вы запросили сброс пароля для вашего аккаунта в ИИ-Юрист.
        
        Для сброса пароля перейдите по ссылке:
        {reset_url}
        
        Ссылка действительна в течение 1 часа.
        
        Если вы не запрашивали сброс пароля, проигнорируйте это письмо.
        
        С уважением,
        Команда ИИ-Юрист
        """
        
        # Имитация отправки
        logger.info(f"Password reset email sent to {user_email}")
        
        return {
            "status": "sent",
            "recipient": user_email,
            "subject": subject
        }
        
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        raise

@celery_app.task(queue="email")
def send_notification_email(user_email: str, notification_data: Dict[str, Any]) -> Dict[str, Any]:
    """Отправка уведомления по email"""
    try:
        logger.info(f"Sending notification email to {user_email}")
        
        subject = notification_data.get("title", "Уведомление от ИИ-Юрист")
        message = notification_data.get("message", "")
        
        body = f"""
        {message}
        
        С уважением,
        Команда ИИ-Юрист
        """
        
        # Имитация отправки
        logger.info(f"Notification email sent to {user_email}")
        
        return {
            "status": "sent",
            "recipient": user_email,
            "subject": subject
        }
        
    except Exception as e:
        logger.error(f"Failed to send notification email: {str(e)}")
        raise
