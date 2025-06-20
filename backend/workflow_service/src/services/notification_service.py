from typing import Dict, Optional
from uuid import UUID
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from ..repositories.notification_repository import NotificationRepository
from common.src.config import get_settings

class NotificationService:
    def __init__(self, repository: NotificationRepository):
        self.repository = repository
        self.settings = get_settings()
    
    async def send_approval_notification(
        self,
        workflow_id: UUID,
        recipient_id: UUID,
        notification_type: str,
        document_type: str,
        document_id: UUID,
        step_id: Optional[UUID] = None
    ) -> Dict:
        """Send approval notification to user"""
        # Create notification record
        notification = await self.repository.create_notification({
            "workflow_id": workflow_id,
            "step_id": step_id,
            "recipient_id": recipient_id,
            "notification_type": notification_type,
            "metadata": {
                "document_type": document_type,
                "document_id": str(document_id)
            }
        })
        
        # Get recipient details
        recipient = await self.repository.get_user(recipient_id)
        
        # Send email notification
        if recipient.get('email') and self.settings.smtp_enabled:
            await self._send_email(
                to_email=recipient['email'],
                subject=f"Action Required: {document_type.upper()} Approval",
                body=self._format_approval_email(
                    recipient['full_name'],
                    document_type,
                    notification_type
                )
            )
        
        return notification
    
    async def send_reminder_notification(
        self,
        workflow_id: UUID,
        step_id: UUID,
        recipient_id: UUID
    ) -> Dict:
        """Send reminder for pending approval"""
        # Check last reminder
        last_reminder = await self.repository.get_last_reminder(step_id, recipient_id)
        
        if last_reminder and (datetime.utcnow() - last_reminder['sent_at']).total_seconds() < 43200:  # 12 hours
            return {"status": "skipped", "reason": "Reminder sent recently"}
        
        # Create reminder notification
        notification = await self.repository.create_notification({
            "workflow_id": workflow_id,
            "step_id": step_id,
            "recipient_id": recipient_id,
            "notification_type": "reminder",
            "reminder_count": (last_reminder['reminder_count'] + 1) if last_reminder else 1
        })
        
        # Send reminder email
        recipient = await self.repository.get_user(recipient_id)
        if recipient.get('email') and self.settings.smtp_enabled:
            await self._send_email(
                to_email=recipient['email'],
                subject="Reminder: Pending Approval Required",
                body=self._format_reminder_email(recipient['full_name'])
            )
        
        return notification
    
    async def _send_email(self, to_email: str, subject: str, body: str):
        """Send email using SMTP"""
        message = MIMEMultipart()
        message['From'] = self.settings.smtp_from_email
        message['To'] = to_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        
        try:
            async with aiosmtplib.SMTP(
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                use_tls=True
            ) as smtp:
                await smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                await smtp.send_message(message)
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
    
    def _format_approval_email(self, recipient_name: str, document_type: str, notification_type: str) -> str:
        """Format approval email body"""
        return f"""
Dear {recipient_name},

You have a new {document_type.upper()} document awaiting your approval.

Please log in to the system to review and approve the document.

Action Required: {notification_type.replace('_', ' ').title()}

Thank you,
Special Education Management System
"""
    
    def _format_reminder_email(self, recipient_name: str) -> str:
        """Format reminder email body"""
        return f"""
Dear {recipient_name},

This is a reminder that you have a document pending your approval.

Please log in to the system at your earliest convenience to review the document.

Thank you,
Special Education Management System
"""
