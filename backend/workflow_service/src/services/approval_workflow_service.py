from typing import Dict, List, Optional, Any
from uuid import UUID
from enum import Enum

from ..repositories.approval_repository import ApprovalRepository
from .notification_service import NotificationService

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"

class StepStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"

class ApprovalWorkflowService:
    def __init__(
        self,
        repository: ApprovalRepository,
        notification_service: NotificationService,
        auth_service_client
    ):
        self.repository = repository
        self.notification_service = notification_service
        self.auth_client = auth_service_client
    
    async def initiate_workflow(
        self,
        document_type: str,
        document_id: UUID,
        document_version_id: UUID,
        initiated_by: UUID
    ) -> Dict[str, Any]:
        """Initiate approval workflow for a document"""
        
        # 1. Get approval hierarchy for document type
        hierarchy = await self.repository.get_approval_hierarchy(document_type)
        if not hierarchy:
            raise ValueError(f"No approval hierarchy defined for {document_type}")
        
        # 2. Create workflow
        workflow = await self.repository.create_workflow({
            "document_type": document_type,
            "document_id": document_id,
            "current_step": 1,
            "status": WorkflowStatus.PENDING,
            "initiated_by": initiated_by
        })
        
        # 3. Create approval steps based on hierarchy
        for step in hierarchy:
            # Find users with the required role
            approvers = await self.auth_client.get_users_by_role(step['approver_role'])
            
            # For now, assign to first available approver
            # In production, implement round-robin or workload balancing
            assigned_to = approvers[0]['id'] if approvers else None
            
            await self.repository.create_approval_step({
                "workflow_id": workflow['id'],
                "step_order": step['step_order'],
                "approver_role": step['approver_role'],
                "assigned_to": assigned_to,
                "status": StepStatus.PENDING,
                "version_reviewed": document_version_id
            })
            
            # Send notification only for first step
            if step['step_order'] == 1 and assigned_to:
                await self.notification_service.send_approval_notification(
                    workflow_id=workflow['id'],
                    recipient_id=assigned_to,
                    notification_type="pending_approval",
                    document_type=document_type,
                    document_id=document_id
                )
        
        # 4. Update workflow status to in_review
        await self.repository.update_workflow_status(
            workflow['id'], 
            WorkflowStatus.IN_REVIEW
        )
        
        return workflow
    
    async def process_approval_decision(
        self,
        workflow_id: UUID,
        step_id: UUID,
        decision: StepStatus,
        comments: Optional[str],
        user_id: UUID,
        user_role: str,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Process approval decision for a step"""
        
        # 1. Validate user can approve this step
        step = await self.repository.get_approval_step(step_id)
        if not step or step['workflow_id'] != workflow_id:
            raise ValueError("Invalid step for workflow")
        
        if not self.auth_client.can_perform_action(user_role, step['approver_role']):
            raise PermissionError("User cannot approve this step")
        
        # 2. Update step status
        await self.repository.update_step_status(
            step_id,
            decision,
            comments,
            attachments
        )
        
        # 3. Handle workflow progression based on decision
        workflow = await self.repository.get_workflow(workflow_id)
        
        if decision == StepStatus.APPROVED:
            # Check if there are more steps
            next_step = await self.repository.get_next_pending_step(workflow_id)
            
            if next_step:
                # Move to next step
                await self.repository.update_workflow_current_step(
                    workflow_id,
                    next_step['step_order']
                )
                
                # Notify next approver
                if next_step['assigned_to']:
                    await self.notification_service.send_approval_notification(
                        workflow_id=workflow_id,
                        recipient_id=next_step['assigned_to'],
                        notification_type="pending_approval",
                        document_type=workflow['document_type'],
                        document_id=workflow['document_id']
                    )
            else:
                # All steps approved - complete workflow
                await self.repository.update_workflow_status(
                    workflow_id,
                    WorkflowStatus.APPROVED
                )
                
                # Notify initiator
                await self.notification_service.send_completion_notification(
                    workflow_id=workflow_id,
                    recipient_id=workflow['initiated_by'],
                    status="approved"
                )
        
        elif decision == StepStatus.REJECTED:
            # Workflow rejected
            await self.repository.update_workflow_status(
                workflow_id,
                WorkflowStatus.REJECTED
            )
            
            # Notify initiator with rejection reason
            await self.notification_service.send_rejection_notification(
                workflow_id=workflow_id,
                recipient_id=workflow['initiated_by'],
                rejected_by=user_id,
                reason=comments
            )
        
        elif decision == StepStatus.RETURNED:
            # Return for revision
            await self.repository.update_workflow_status(
                workflow_id,
                WorkflowStatus.RETURNED
            )
            
            # Notify initiator to make changes
            await self.notification_service.send_return_notification(
                workflow_id=workflow_id,
                recipient_id=workflow['initiated_by'],
                returned_by=user_id,
                comments=comments
            )
        
        return {
            "workflow": workflow,
            "step": step,
            "decision": decision,
            "next_step": next_step if decision == StepStatus.APPROVED else None
        }
    
    async def get_pending_approvals(
        self,
        user_id: UUID,
        user_role: str,
        document_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all pending approvals for a user"""
        # Get pending steps assigned to user or their role
        pending_steps = await self.repository.get_pending_approvals_for_user(
            user_id,
            user_role,
            document_type
        )
        
        # Enrich with document information
        approvals = []
        for step in pending_steps:
            workflow = await self.repository.get_workflow(step['workflow_id'])
            
            approvals.append({
                "workflow_id": workflow['id'],
                "step_id": step['id'],
                "document_type": workflow['document_type'],
                "document_id": workflow['document_id'],
                "initiated_at": workflow['initiated_at'],
                "current_step": step['step_order'],
                "total_steps": await self.repository.get_total_steps(workflow['id'])
            })
        
        return approvals
