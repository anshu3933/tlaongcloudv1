from typing import Optional, Dict, Any
from uuid import UUID
import json

from ..vector_store import VectorStore
from ..repositories.iep_repository import IEPRepository
from ..repositories.pl_repository import PLRepository
from ..rag.iep_generator import IEPGenerator
from ..utils.retry import retry_iep_operation, ConflictDetector

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
        
        import logging
        import time
        logger = logging.getLogger(__name__)
        start_time = time.time()
        
        logger.info(f"🚀 [BACKEND-SERVICE] Starting RAG IEP creation for student {student_id}, academic year {academic_year}")
        logger.info(f"📋 [BACKEND-SERVICE] Input validation: template_id={template_id}, user_id={user_id}, user_role={user_role}")
        logger.info(f"📊 [BACKEND-SERVICE] Initial data keys: {list(initial_data.keys())}, content_keys: {list(initial_data.get('content', {}).keys())}")
        
        # STEP 1: Collect all needed data from database FIRST (before any external calls)
        logger.info(f"🗃️ [BACKEND-SERVICE] STEP 1: Collecting database data...")
        template = None
        if template_id:
            try:
                logger.info(f"📋 [BACKEND-SERVICE] Fetching template: {template_id}")
                template = await self.repository.get_template(template_id)
                if not template:
                    logger.warning(f"⚠️ [BACKEND-SERVICE] Template {template_id} not found, using default template")
                else:
                    logger.info(f"✅ [BACKEND-SERVICE] Template fetched successfully: {template.get('name', 'Unknown')}")
            except Exception as e:
                logger.warning(f"❌ [BACKEND-SERVICE] Error fetching template {template_id}, using default template: {e}")
        
        # Create default template if none provided or not found
        if not template:
            logger.info("Using default template as no template was provided or found")
            template = {
                "id": "default-template",
                "name": "Default IEP Template",
                "sections": {
                    "student_info": "Name, DOB, Class, Date of IEP",
                    "long_term_goal": "Long-Term Goal",
                    "short_term_goals": "Short Term Goals: June – December 2025",
                    "oral_language": "Oral Language – Receptive and Expressive Goals and Recommendations",
                    "reading_familiar": "Reading Familiar Goals",
                    "reading_unfamiliar": "Reading - Unfamiliar",
                    "reading_comprehension": "Reading Comprehension Recommendations",
                    "spelling": "Spelling Goals",
                    "writing": "Writing Recommendations",
                    "concept": "Concept Recommendations",
                    "math": "Math Goals and Recommendations"
                },
                "default_goals": [
                    {
                        "domain": "Reading",
                        "template": "Student will improve reading skills with 80% accuracy"
                    },
                    {
                        "domain": "Writing", 
                        "template": "Student will improve writing skills with measurable progress"
                    },
                    {
                        "domain": "Math",
                        "template": "Student will demonstrate improved math skills"
                    }
                ]
            }
        
        logger.info(f"📚 [BACKEND-SERVICE] Fetching student history...")
        previous_ieps = await self.repository.get_student_ieps(
            student_id, 
            limit=3
        )
        previous_pls = await self.pl_repository.get_student_present_levels(
            student_id,
            limit=3
        )
        
        logger.info(f"📊 [BACKEND-SERVICE] Historical data collected: {len(previous_ieps)} previous IEPs, {len(previous_pls)} assessments")
        
        # STEP 2: Disconnect from database session and generate content with RAG
        # This ensures no active DB session during external API calls
        step1_time = time.time()
        logger.info(f"🤖 [BACKEND-SERVICE] STEP 2: Starting RAG generation (external API calls) after {step1_time - start_time:.2f}s")
        
        # Prepare data for RAG (convert to serializable format)
        template_data = {
            "id": str(template["id"]),
            "name": template.get("name", ""),
            "sections": template.get("sections", {}),
            "default_goals": template.get("default_goals", [])
        }
        
        previous_ieps_data = [
            {
                "id": str(iep["id"]),
                "content": iep.get("content", {}),
                "academic_year": iep.get("academic_year", ""),
                "status": iep.get("status", "")
            }
            for iep in previous_ieps
        ]
        
        previous_pls_data = [
            {
                "id": str(pl["id"]),
                "present_levels": pl.get("present_levels", ""),
                "strengths": pl.get("strengths", []),
                "needs": pl.get("needs", [])
            }
            for pl in previous_pls
        ]
        
        # ACTUAL RAG GENERATION: Call the IEP generator with real AI
        logger.info("Starting RAG-powered IEP generation using Gemini")
        
        # Extract student data from the content field (where frontend sends it)
        content_data = initial_data.get("content", {})
        assessment_data = content_data.get("assessment_summary", {})
        
        # Handle assessment_data being either string or dict
        if isinstance(assessment_data, str):
            # If it's a string, treat it as a summary
            assessment_dict = {"summary": assessment_data}
        elif isinstance(assessment_data, dict):
            assessment_dict = assessment_data
        else:
            assessment_dict = {}
        
        # Prepare student data for RAG generation using content field
        student_data = {
            "student_id": str(student_id),
            "disability_type": content_data.get("disability_types", []),
            "grade_level": content_data.get("grade_level", ""),
            "student_name": content_data.get("student_name", ""),
            "case_manager_name": content_data.get("case_manager_name", ""),
            "placement_setting": content_data.get("placement_setting", ""),
            "service_hours_per_week": content_data.get("service_hours_per_week", 0),
            # Extract assessment summary details with defensive checks
            "current_achievement": assessment_dict.get("current_achievement", assessment_dict.get("summary", "")),
            "strengths": assessment_dict.get("strengths", ""),
            "areas_for_growth": assessment_dict.get("areas_for_growth", ""),
            "learning_profile": assessment_dict.get("learning_profile", ""),
            "interests": assessment_dict.get("interests", ""),
            # Extract educational planning if available
            "annual_goals": content_data.get("educational_planning", {}).get("annual_goals", ""),
            "teaching_strategies": content_data.get("educational_planning", {}).get("teaching_strategies", ""),
            "assessment_methods": content_data.get("educational_planning", {}).get("assessment_methods", ""),
            # Fallback to root level if content is empty (for backwards compatibility)
            "needs": initial_data.get("needs", []) if not content_data else [],
            "assessment_summary": initial_data.get("assessment_summary", "") if not content_data else ""
        }
        
        logger.info(f"📄 [BACKEND-SERVICE] Extracted student data for RAG: {student_data}")
        logger.info(f"📋 [BACKEND-SERVICE] Content data received keys: {list(content_data.keys()) if content_data else []}")
        
        # Generate IEP content using RAG and Gemini
        try:
            rag_start = time.time()
            logger.info(f"🧠 [BACKEND-SERVICE] Calling RAG generator...")
            iep_content = await self.iep_generator.generate_iep(
                template=template_data,
                student_data=student_data,
                previous_ieps=previous_ieps_data,
                previous_assessments=previous_pls_data
            )
            rag_end = time.time()
            logger.info(f"✅ [BACKEND-SERVICE] RAG generation completed successfully in {rag_end - rag_start:.2f}s with Gemini AI")
            logger.info(f"📄 [BACKEND-SERVICE] Generated content sections: {list(iep_content.keys()) if isinstance(iep_content, dict) else 'non-dict response'}")
            
            # Add metadata about generation method
            iep_content.update({
                "template_used": template_data.get("name", "Default IEP Template"),
                "generation_method": "rag_powered_ai",
                "ai_model": "gemini-2.5-flash",
                "generated_at": str(initial_data.get("meeting_date", ""))
            })
            
        except Exception as e:
            rag_end = time.time()
            logger.error(f"❌ [BACKEND-SERVICE] RAG generation failed after {rag_end - rag_start:.2f}s: {e}")
            # Fallback to basic template structure if RAG fails
            iep_content = {
                "error": f"AI generation failed: {str(e)}",
                "fallback_content": template_data.get("sections", {}),
                "template_used": template_data.get("name", "Default IEP Template"),
                "generation_method": "fallback_template",
                "requires_manual_review": True
            }
            logger.info(f"🔄 [BACKEND-SERVICE] Using fallback template content")
        
        # JSON serialization helper function
        def ensure_json_serializable(obj):
            """Recursively ensure all objects are JSON serializable"""
            if hasattr(obj, 'strftime'):  # datetime/date objects
                return obj.strftime("%Y-%m-%d") if hasattr(obj, 'date') else str(obj)
            elif isinstance(obj, dict):
                return {k: ensure_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [ensure_json_serializable(item) for item in obj]
            elif hasattr(obj, '__dict__'):  # Custom objects
                return str(obj)
            else:
                return obj
        
        # Ensure the generated content is JSON serializable
        iep_content = ensure_json_serializable(iep_content)
        
        step2_time = time.time()
        logger.info(f"🗃️ [BACKEND-SERVICE] STEP 3: RAG generation completed in {step2_time - step1_time:.2f}s, proceeding with database operations")
        
        # 4. Create IEP directly without retry mechanism to avoid greenlet issues
        try:
            # Get next version number atomically
            version_number = await self.repository.get_next_version_number(
                student_id, academic_year
            )
            logger.info(f"Atomic version number assigned: {version_number} for student {student_id} in {academic_year}")
            
            # Get parent version if this is not the first version
            parent_version_id = None
            if version_number > 1:
                latest_iep = await self.repository.get_latest_iep_version(
                    student_id, academic_year
                )
                if latest_iep:
                    # Convert string UUID back to UUID object for database
                    from uuid import UUID
                    parent_version_id = UUID(latest_iep["id"])
                    logger.info(f"Parent version ID: {parent_version_id}")
            else:
                logger.info(f"First IEP version for student {student_id} in {academic_year}")
            
            # Create IEP record with proper versioning
            iep_data = {
                "student_id": student_id,
                "template_id": template_id,
                "academic_year": academic_year,
                "status": "draft",
                "content": iep_content,
                "version": version_number,
                "created_by": user_id
            }
            
            # Handle date fields safely - convert strings to date objects for SQLite
            from datetime import date, datetime
            
            if initial_data.get("meeting_date"):
                meeting_date = initial_data["meeting_date"]
                if isinstance(meeting_date, str):
                    try:
                        # Parse string date to date object
                        iep_data["meeting_date"] = datetime.strptime(meeting_date, "%Y-%m-%d").date()
                    except ValueError:
                        logger.warning(f"Invalid meeting_date format: {meeting_date}")
                        iep_data["meeting_date"] = None
                elif hasattr(meeting_date, 'date'):
                    # It's a datetime, extract date part
                    iep_data["meeting_date"] = meeting_date.date()
                else:
                    # It's already a date object
                    iep_data["meeting_date"] = meeting_date
            
            if initial_data.get("effective_date"):
                effective_date = initial_data["effective_date"]
                if isinstance(effective_date, str):
                    try:
                        # Parse string date to date object
                        iep_data["effective_date"] = datetime.strptime(effective_date, "%Y-%m-%d").date()
                    except ValueError:
                        logger.warning(f"Invalid effective_date format: {effective_date}")
                        iep_data["effective_date"] = None
                elif hasattr(effective_date, 'date'):
                    # It's a datetime, extract date part
                    iep_data["effective_date"] = effective_date.date()
                else:
                    # It's already a date object
                    iep_data["effective_date"] = effective_date
            
            if initial_data.get("review_date"):
                review_date = initial_data["review_date"]
                if isinstance(review_date, str):
                    try:
                        # Parse string date to date object
                        iep_data["review_date"] = datetime.strptime(review_date, "%Y-%m-%d").date()
                    except ValueError:
                        logger.warning(f"Invalid review_date format: {review_date}")
                        iep_data["review_date"] = None
                elif hasattr(review_date, 'date'):
                    # It's a datetime, extract date part
                    iep_data["review_date"] = review_date.date()
                else:
                    # It's already a date object
                    iep_data["review_date"] = review_date
            
            # Add parent version if this is not the first version
            if parent_version_id:
                # Ensure parent_version_id is a UUID object, not string
                if isinstance(parent_version_id, str):
                    from uuid import UUID
                    iep_data["parent_version_id"] = UUID(parent_version_id)
                else:
                    iep_data["parent_version_id"] = parent_version_id
            
            logger.info(f"About to create IEP with version: {version_number}")
            # Create the IEP
            iep = await self.repository.create_iep(iep_data)
            logger.info(f"IEP created successfully with ID: {iep['id']}, version: {version_number}")
            
        except Exception as e:
            logger.error(f"Failed to create IEP: {e}")
            raise ValueError(f"Failed to create IEP: {str(e)}")
        
        logger.info(f"IEP created successfully: {iep['id']}")
        
        # SAFETY: Test JSON serialization of IEP before proceeding  
        try:
            import json
            test_json = json.dumps(iep, default=str)
            logger.info(f"IEP data JSON serialization test passed, length: {len(test_json)}")
        except Exception as json_error:
            logger.error(f"IEP data JSON serialization failed: {json_error}")
            logger.error(f"IEP keys: {list(iep.keys())}")
            logger.error(f"Content keys: {list(iep.get('content', {}).keys())}")
        
        # CRITICAL FIX: Enable IEP indexing for RAG functionality
        logger.info("Performing post-creation operations...")
        
        # Enable vector store indexing for RAG retrieval
        try:
            logger.info("Indexing IEP content for RAG retrieval...")
            await self._index_iep_content(iep)
            logger.info("IEP content indexed successfully")
        except Exception as indexing_error:
            logger.error(f"Failed to index IEP content: {indexing_error}")
            # Don't fail the entire operation if indexing fails
        
        # Create goals if provided
        if initial_data.get("goals"):
            try:
                for goal_data in initial_data["goals"]:
                    await self.repository.create_iep_goal({
                        "iep_id": iep["id"],
                        **goal_data
                    })
                logger.info("Goals created successfully")
            except Exception as goal_error:
                logger.error(f"Failed to create goals: {goal_error}")
        
        # Create audit log if available
        if self.audit_client:
            try:
                await self.audit_client.log_action(
                    entity_type="iep",
                    entity_id=iep["id"],
                    action="create",
                    user_id=user_id,
                    user_role="system",
                    changes={"initial_creation": True, "version": iep.get("version", 1)}
                )
                logger.info("Audit log created successfully")
            except Exception as audit_error:
                logger.error(f"Failed to create audit log: {audit_error}")
        
        logger.info("Post-creation operations completed")
        return iep
    
    async def create_iep(
        self,
        student_id: UUID,
        academic_year: str,
        initial_data: Dict[str, Any],
        user_id: UUID,
        template_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Create new IEP without RAG generation (simple version) with retry mechanism"""
        
        async def _create_iep_operation():
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Creating simple IEP for student {student_id}, academic year {academic_year}")
            
            try:
                # Get next version number atomically
                version_number = await self.repository.get_next_version_number(
                    student_id, academic_year
                )
                logger.info(f"Atomic version number assigned: {version_number} for student {student_id} in {academic_year}")
                
                # Get parent version if this is not the first version
                parent_version_id = None
                if version_number > 1:
                    latest_iep = await self.repository.get_latest_iep_version(
                        student_id, academic_year
                    )
                    if latest_iep:
                        parent_version_id = latest_iep["id"]
                        logger.info(f"Parent version ID: {parent_version_id}")
                else:
                    logger.info(f"First IEP version for student {student_id} in {academic_year}")
                
                # Create IEP record with proper versioning
                iep_data = {
                    "student_id": student_id,
                    "template_id": template_id,
                    "academic_year": academic_year,
                    "status": "draft",
                    "content": initial_data.get("content", {}),
                    "version": version_number,
                    "created_by": user_id
                }
                
                # Handle date fields safely - convert strings to date objects for SQLite
                from datetime import date, datetime
                
                if initial_data.get("meeting_date"):
                    meeting_date = initial_data["meeting_date"]
                    if isinstance(meeting_date, str):
                        try:
                            # Parse string date to date object
                            iep_data["meeting_date"] = datetime.strptime(meeting_date, "%Y-%m-%d").date()
                        except ValueError:
                            logger.warning(f"Invalid meeting_date format: {meeting_date}")
                            iep_data["meeting_date"] = None
                    elif hasattr(meeting_date, 'date'):
                        # It's a datetime, extract date part
                        iep_data["meeting_date"] = meeting_date.date()
                    else:
                        # It's already a date object
                        iep_data["meeting_date"] = meeting_date
                
                if initial_data.get("effective_date"):
                    effective_date = initial_data["effective_date"]
                    if isinstance(effective_date, str):
                        try:
                            # Parse string date to date object
                            iep_data["effective_date"] = datetime.strptime(effective_date, "%Y-%m-%d").date()
                        except ValueError:
                            logger.warning(f"Invalid effective_date format: {effective_date}")
                            iep_data["effective_date"] = None
                    elif hasattr(effective_date, 'date'):
                        # It's a datetime, extract date part
                        iep_data["effective_date"] = effective_date.date()
                    else:
                        # It's already a date object
                        iep_data["effective_date"] = effective_date
                
                if initial_data.get("review_date"):
                    review_date = initial_data["review_date"]
                    if isinstance(review_date, str):
                        try:
                            # Parse string date to date object
                            iep_data["review_date"] = datetime.strptime(review_date, "%Y-%m-%d").date()
                        except ValueError:
                            logger.warning(f"Invalid review_date format: {review_date}")
                            iep_data["review_date"] = None
                    elif hasattr(review_date, 'date'):
                        # It's a datetime, extract date part
                        iep_data["review_date"] = review_date.date()
                    else:
                        # It's already a date object
                        iep_data["review_date"] = review_date
                
                # Add parent version if this is not the first version
                if parent_version_id:
                    # Ensure parent_version_id is a UUID object, not string
                    if isinstance(parent_version_id, str):
                        from uuid import UUID
                        iep_data["parent_version_id"] = UUID(parent_version_id)
                    else:
                        iep_data["parent_version_id"] = parent_version_id
                
                logger.info(f"About to create IEP with version: {version_number}")
                # Create the IEP
                iep = await self.repository.create_iep(iep_data)
                logger.info(f"IEP created successfully with ID: {iep['id']}, version: {version_number}")
                
                # Create goals if provided
                if initial_data.get("goals"):
                    for goal_data in initial_data["goals"]:
                        await self.repository.create_iep_goal({
                            "iep_id": iep["id"],
                            **goal_data
                        })
                
                # Create audit log
                if self.audit_client:
                    await self.audit_client.log_action(
                        entity_type="iep",
                        entity_id=iep["id"],
                        action="create",
                        user_id=user_id,
                        user_role="system",
                        changes={"initial_creation": True, "version": version_number}
                    )
                
                return iep
                
            except Exception as e:
                # Convert database exceptions to retryable errors when appropriate
                converted_exception = ConflictDetector.convert_to_retryable_error(e)
                raise converted_exception
        
        # Use retry mechanism for the entire operation
        return await retry_iep_operation(_create_iep_operation)
    
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
                "created_at": iep["created_at"].isoformat() if hasattr(iep["created_at"], 'isoformat') else str(iep["created_at"])
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
