from typing import Optional, Dict, Any
from uuid import UUID
import json

from common.src.vector_store import VectorStore
from ..repositories.iep_repository import IEPRepository
from ..repositories.pl_repository import PLRepository
from ..rag.iep_generator import IEPGenerator

class IEPService:
    def __init__(
        self,
        repository: IEPRepository,
        pl_repository: PLRepository,
        vector_store: VectorStore,
        iep_generator: IEPGenerator,
        workflow_client,
        audit_client
    ):
        self.repository = repository
        self.pl_repository = pl_repository
        self.vector_store = vector_store
        self.iep_generator = iep_generator
        self.workflow_client = workflow_client
        self.audit_client = audit_client
    
    async def create_iep_with_rag(
        self,
        student_id: UUID,
        template_id: UUID,
        academic_year: str,
        initial_data: Dict[str, Any],
        user_id: UUID,
        user_role: str
    ) -> Dict[str, Any]:
        """Create new IEP using template and RAG generation"""
        
        # 1. Load template
        template = await self.repository.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # 2. Get student history for context
        previous_ieps = await self.repository.get_student_ieps(
            student_id, 
            limit=3
        )
        previous_pls = await self.pl_repository.get_student_present_levels(
            student_id,
            limit=3
        )
        
        # 3. Generate IEP content using RAG
        iep_content = await self.iep_generator.generate_iep(
            template=template,
            student_data=initial_data,
            previous_ieps=previous_ieps,
            previous_assessments=previous_pls
        )
        
        # 4. Create IEP record
        iep = await self.repository.create_iep({
            "student_id": student_id,
            "template_id": template_id,
            "academic_year": academic_year,
            "status": "draft",
            "content": iep_content,
            "created_by": user_id
        })
        
        # 5. Create goals if provided
        if initial_data.get("goals"):
            for goal_data in initial_data["goals"]:
                await self.repository.create_iep_goal({
                    "iep_id": iep["id"],
                    **goal_data
                })
        
        # 6. Create audit log
        await self.audit_client.log_action(
            entity_type="iep",
            entity_id=iep["id"],
            action="create",
            user_id=user_id,
            user_role=user_role,
            changes={"initial_creation": True}
        )
        
        # 7. Index in vector store for future retrieval
        await self._index_iep_content(iep)
        
        return iep
    
    async def update_iep_with_versioning(
        self,
        iep_id: UUID,
        updates: Dict[str, Any],
        user_id: UUID,
        user_role: str
    ) -> Dict[str, Any]:
        """Update IEP with automatic versioning"""
        
        # 1. Get current IEP
        current_iep = await self.repository.get_iep(iep_id)
        if not current_iep:
            raise ValueError(f"IEP {iep_id} not found")
        
        # 2. Check if IEP can be edited
        if current_iep["status"] not in ["draft", "returned"]:
            raise ValueError(f"Cannot edit IEP in {current_iep['status']} status")
        
        # 3. Create new version
        new_version = current_iep["version"] + 1
        new_iep = await self.repository.create_iep({
            "student_id": current_iep["student_id"],
            "template_id": current_iep["template_id"],
            "academic_year": current_iep["academic_year"],
            "status": current_iep["status"],
            "content": {**current_iep["content"], **updates},
            "version": new_version,
            "parent_version_id": iep_id,
            "created_by": user_id
        })
        
        # 4. Log changes
        await self.audit_client.log_action(
            entity_type="iep",
            entity_id=new_iep["id"],
            action="update",
            user_id=user_id,
            user_role=user_role,
            changes=updates
        )
        
        # 5. Re-index
        await self._index_iep_content(new_iep)
        
        return new_iep
    
    async def submit_iep_for_approval(
        self,
        iep_id: UUID,
        user_id: UUID,
        user_role: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit IEP for approval workflow"""
        
        # 1. Validate IEP is in draft status
        iep = await self.repository.get_iep(iep_id)
        if not iep:
            raise ValueError(f"IEP {iep_id} not found")
        
        if iep['status'] != 'draft':
            raise ValueError("IEP must be in draft status to submit for approval")
        
        # 2. Update IEP status to under_review
        await self.repository.update_iep_status(iep_id, 'under_review')
        
        # 3. Initiate approval workflow
        workflow = await self.workflow_client.initiate_workflow(
            document_type="iep",
            document_id=iep_id,
            document_version_id=iep_id,
            initiated_by=user_id
        )
        
        # 4. Log audit trail
        await self.audit_client.log_action(
            entity_type="iep",
            entity_id=iep_id,
            action="submitted_for_approval",
            user_id=user_id,
            user_role=user_role,
            changes={"workflow_id": str(workflow['id']), "comments": comments}
        )
        
        return {
            "iep_id": iep_id,
            "workflow": workflow,
            "message": "IEP submitted for approval successfully"
        }
    
    async def generate_section(
        self,
        iep_id: UUID,
        section_name: str,
        additional_context: Optional[Dict[str, Any]] = None,
        user_id: UUID = None
    ) -> Dict[str, Any]:
        """Generate specific IEP section using RAG"""
        # Get IEP and template
        iep = await self.repository.get_iep(iep_id)
        if not iep:
            raise ValueError(f"IEP {iep_id} not found")
        
        template = await self.repository.get_template(iep["template_id"])
        section_template = template["sections"].get(section_name)
        
        if not section_template:
            raise ValueError(f"Section {section_name} not found in template")
        
        # Generate section
        context = {
            "student_id": iep["student_id"],
            "current_iep": iep["content"],
            **(additional_context or {})
        }
        
        section_content = await self.iep_generator._generate_section(
            section_name,
            section_template,
            context
        )
        
        # Log generation
        if user_id:
            await self.audit_client.log_action(
                entity_type="iep",
                entity_id=iep_id,
                action="section_generated",
                user_id=user_id,
                user_role="system",
                changes={"section": section_name}
            )
        
        return section_content
    
    async def get_iep_with_details(
        self,
        iep_id: UUID,
        include_history: bool = False,
        include_goals: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get IEP with optional related data"""
        iep = await self.repository.get_iep(iep_id)
        if not iep:
            return None
        
        # Add goals if requested
        if include_goals:
            goals = await self.repository.get_iep_goals(iep_id)
            iep["goals"] = goals
        
        # Add history if requested
        if include_history:
            history = await self.repository.get_iep_version_history(
                iep["student_id"],
                iep["academic_year"]
            )
            iep["version_history"] = history
        
        return iep
    
    async def _index_iep_content(self, iep: Dict[str, Any]):
        """Index IEP content for RAG retrieval"""
        # Extract text content from IEP
        text_content = self._extract_text_from_iep(iep)
        
        # Create embedding
        embedding = await self.iep_generator.create_embedding(text_content)
        
        # Store in vector store
        self.vector_store.add_documents([{
            "id": f"iep_{iep['id']}",
            "content": text_content,
            "embedding": embedding,
            "metadata": {
                "type": "iep",
                "student_id": str(iep["student_id"]),
                "academic_year": iep["academic_year"],
                "version": iep["version"],
                "created_at": iep["created_at"].isoformat()
            }
        }])
    
    def _extract_text_from_iep(self, iep: Dict[str, Any]) -> str:
        """Extract searchable text from IEP structure"""
        text_parts = []
        
        # Add basic info
        text_parts.append(f"IEP for academic year {iep['academic_year']}")
        
        # Add content sections
        content = iep.get("content", {})
        for section_name, section_content in content.items():
            if isinstance(section_content, dict):
                text_parts.append(f"{section_name}: {json.dumps(section_content)}")
            else:
                text_parts.append(f"{section_name}: {section_content}")
        
        return "\n\n".join(text_parts)
