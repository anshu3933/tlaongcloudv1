from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime

from ..repositories.audit_repository import AuditRepository

class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository
    
    async def log_action(
        self,
        entity_type: str,
        entity_id: UUID,
        action: str,
        user_id: UUID,
        user_role: str,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict:
        """Log an action in the audit trail"""
        audit_entry = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "user_id": user_id,
            "user_role": user_role,
            "changes": changes or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow()
        }
        
        return await self.repository.create_audit_log(audit_entry)
    
    async def get_entity_audit_trail(
        self,
        entity_type: str,
        entity_id: UUID,
        limit: int = 100
    ) -> List[Dict]:
        """Get audit trail for specific entity"""
        return await self.repository.get_audit_logs_for_entity(
            entity_type, entity_id, limit
        )
    
    async def get_user_actions(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get all actions performed by a user"""
        return await self.repository.get_audit_logs_by_user(
            user_id, start_date, end_date, limit
        )
