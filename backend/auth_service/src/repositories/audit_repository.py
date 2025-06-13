from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
import logging

from ..models.audit_log import AuditLog

logger = logging.getLogger(__name__)

class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(
        self,
        entity_type: str,
        entity_id: int,
        action: str,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict] = None
    ) -> AuditLog:
        """Log an audit action."""
        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            user_role=user_role,
            ip_address=ip_address,
            details=details
        )
        self.session.add(audit_log)
        await self.session.commit()
        await self.session.refresh(audit_log)
        
        logger.debug(f"Logged audit action: {action} for {entity_type}:{entity_id}")
        return audit_log

    async def get_logs_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs for a specific entity."""
        result = await self.session.execute(
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_logs_by_user(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs for a specific user."""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_logs_by_action(
        self,
        action: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs for a specific action type."""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_logs_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000,
        offset: int = 0
    ) -> List[AuditLog]:
        """Get audit logs within a date range."""
        result = await self.session.execute(
            select(AuditLog)
            .where(
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_recent_logs(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get recent audit logs within specified hours."""
        since = datetime.utcnow() - timedelta(hours=hours)
        return await self.get_logs_by_date_range(since, datetime.utcnow(), limit)

    async def get_failed_login_attempts(
        self,
        hours: int = 1,
        ip_address: Optional[str] = None
    ) -> List[AuditLog]:
        """Get failed login attempts for monitoring."""
        since = datetime.utcnow() - timedelta(hours=hours)
        query = select(AuditLog).where(
            AuditLog.action == "login_failed",
            AuditLog.created_at >= since
        )
        
        if ip_address:
            query = query.where(AuditLog.ip_address == ip_address)
        
        result = await self.session.execute(
            query.order_by(AuditLog.created_at.desc())
        )
        return result.scalars().all()

    async def get_audit_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get audit log statistics."""
        query = select(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        )
        
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
        
        result = await self.session.execute(
            query.group_by(AuditLog.action)
            .order_by(func.count(AuditLog.id).desc())
        )
        
        action_counts = {row.action: row.count for row in result}
        
        # Get total count
        total_query = select(func.count(AuditLog.id))
        if start_date:
            total_query = total_query.where(AuditLog.created_at >= start_date)
        if end_date:
            total_query = total_query.where(AuditLog.created_at <= end_date)
        
        total_result = await self.session.execute(total_query)
        total_count = total_result.scalar()
        
        return {
            "total_logs": total_count,
            "action_counts": action_counts,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }

    async def cleanup_old_logs(self, days: int = 90) -> int:
        """Clean up audit logs older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.session.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff_date)
        )
        await self.session.commit()
        
        count = result.rowcount
        logger.info(f"Cleaned up {count} audit logs older than {days} days")
        return count

    async def search_logs(
        self,
        search_term: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """Search audit logs by details or action."""
        # Note: This is a simple text search. For production, consider using full-text search
        result = await self.session.execute(
            select(AuditLog)
            .where(
                AuditLog.action.ilike(f"%{search_term}%")
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_user_activity_summary(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get activity summary for a user."""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get action counts
        result = await self.session.execute(
            select(
                AuditLog.action,
                func.count(AuditLog.id).label('count')
            )
            .where(
                AuditLog.user_id == user_id,
                AuditLog.created_at >= since
            )
            .group_by(AuditLog.action)
            .order_by(func.count(AuditLog.id).desc())
        )
        
        action_counts = {row.action: row.count for row in result}
        
        # Get last activity
        last_activity_result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(1)
        )
        last_activity = last_activity_result.scalar_one_or_none()
        
        return {
            "user_id": user_id,
            "period_days": days,
            "action_counts": action_counts,
            "total_actions": sum(action_counts.values()),
            "last_activity": {
                "action": last_activity.action if last_activity else None,
                "timestamp": last_activity.created_at.isoformat() if last_activity else None
            }
        } 