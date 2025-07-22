from typing import Optional, Dict, Any, Union, List
from uuid import UUID
import json
import logging

# Global logger
logger = logging.getLogger(__name__)

from ..vector_store_enhanced import EnhancedVectorStore
from ..repositories.iep_repository import IEPRepository
from ..repositories.pl_repository import PLRepository
from ..repositories.student_repository import StudentRepository
from ..rag.metadata_aware_iep_generator import MetadataAwareIEPGenerator
from ..utils.retry import retry_iep_operation, ConflictDetector

# Legacy import for backward compatibility
from ..vector_store import VectorStore
from ..rag.iep_generator import IEPGenerator

class IEPService:
    def __init__(
        self,
        repository: IEPRepository,
        pl_repository: PLRepository,
        student_repository: StudentRepository,
        vector_store: Union[EnhancedVectorStore, VectorStore],
        iep_generator: Union[MetadataAwareIEPGenerator, IEPGenerator],
        workflow_client,
        audit_client
    ):
        self.repository = repository
        self.pl_repository = pl_repository
        self.student_repository = student_repository
        self.vector_store = vector_store
        self.iep_generator = iep_generator
        self.workflow_client = workflow_client
        self.audit_client = audit_client
        
        # Determine if using enhanced or legacy system
        self.using_enhanced_rag = isinstance(iep_generator, MetadataAwareIEPGenerator)
        
        if self.using_enhanced_rag:
            logger.info("✅ IEP Service initialized with Enhanced RAG System (metadata-aware)")
        else:
            logger.warning("⚠️ IEP Service initialized with Legacy RAG System (deprecated)")
    
    async def create_iep_with_rag(
        self,
        student_id: UUID,
        template_id: UUID,
        academic_year: str,
        initial_data: Dict[str, Any],
        user_id: UUID,
        user_role: str,
        enable_google_search_grounding: bool = False
    ) -> Dict[str, Any]:
        """Create new IEP using template and RAG generation"""
        
        import time
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
        
        # Fetch student record from database
        logger.info(f"👤 [BACKEND-SERVICE] Fetching student record...")
        student_record = await self.student_repository.get_student(student_id)
        if not student_record:
            raise ValueError(f"Student {student_id} not found in database")
        
        logger.info(f"📊 [BACKEND-SERVICE] Historical data collected: {len(previous_ieps)} previous IEPs, {len(previous_pls)} assessments")
        logger.info(f"👤 [BACKEND-SERVICE] Student record: {student_record.get('first_name', '')} {student_record.get('last_name', '')}, Grade: {student_record.get('grade_level', '')}")
        
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
        document_id = content_data.get("document_id")
        
        # 🔗 NEW: ASSESSMENT DATA BRIDGE - Fetch real assessment data if document_id provided
        real_assessment_data = {}
        if document_id:
            logger.info(f"🔗 [ASSESSMENT-BRIDGE] Fetching real assessment data for document_id: {document_id}")
            real_assessment_data = await self._fetch_assessment_data(document_id, student_id)
        else:
            logger.warning(f"⚠️ [ASSESSMENT-BRIDGE] No document_id provided, using fallback data")
        
        # Handle legacy assessment_data format (for backwards compatibility)
        assessment_data = content_data.get("assessment_summary", {})
        if isinstance(assessment_data, str):
            assessment_dict = {"summary": assessment_data}
        elif isinstance(assessment_data, dict):
            assessment_dict = assessment_data
        else:
            assessment_dict = {}
        
        # Prepare student data with DATABASE record taking priority, then assessment data
        student_data = {
            "student_id": str(student_id),
            # Use database record for core student info (CRITICAL for validation)
            "disability_type": student_record.get("disability_codes", []),
            # 🚨 GRADE LEVEL REMOVED: Must come ONLY from assessment data per user requirements
            # "grade_level": student_record.get("grade_level", ""),  # REMOVED - causes hardcoded grades
            "student_name": f"{student_record.get('first_name', '')} {student_record.get('last_name', '')}".strip(),
            "case_manager_name": content_data.get("case_manager_name", ""),
            "placement_setting": content_data.get("placement_setting", ""),
            "service_hours_per_week": content_data.get("service_hours_per_week", 0),
            
            # 🎯 ENHANCED: Use REAL assessment data when available, fallback to generic
            "current_achievement": (
                real_assessment_data.get("present_levels_summary", "") or 
                assessment_dict.get("current_achievement", assessment_dict.get("summary", ""))
            ),
            "strengths": (
                real_assessment_data.get("strengths_formatted", "") or 
                assessment_dict.get("strengths", "")
            ),
            "areas_for_growth": (
                real_assessment_data.get("areas_of_concern_formatted", "") or 
                assessment_dict.get("areas_for_growth", "")
            ),
            "learning_profile": (
                real_assessment_data.get("learning_profile_summary", "") or 
                assessment_dict.get("learning_profile", "")
            ),
            "interests": assessment_dict.get("interests", ""),
            
            # 📊 NEW: Add detailed test scores and assessment findings
            "test_scores": real_assessment_data.get("test_scores", []),
            "composite_scores": real_assessment_data.get("composite_scores", {}),
            "educational_objectives": real_assessment_data.get("educational_objectives", []),
            "recommendations": real_assessment_data.get("recommendations", []),
            "assessment_confidence": real_assessment_data.get("extraction_confidence", 0.0),
            
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
        
        # Generate IEP content using Enhanced RAG system or legacy fallback
        try:
            rag_start = time.time()
            
            if self.using_enhanced_rag:
                logger.info(f"🧠 [BACKEND-SERVICE] Calling Enhanced Metadata-Aware RAG generator...")
                logger.info(f"🎯 [BACKEND-SERVICE] Using evidence-based generation with quality filtering and source attribution")
                
                # Use enhanced generation with metadata awareness
                iep_response, evidence_metadata = await self.iep_generator.generate_enhanced_iep(
                    student_data=student_data,
                    template_data=template_data,
                    generation_context={
                        "previous_ieps": previous_ieps_data,
                        "previous_assessments": previous_pls_data,
                        "academic_year": academic_year,
                        "user_context": {"user_id": user_id, "user_role": user_role}
                    },
                    enable_google_search_grounding=enable_google_search_grounding
                )
                
                # Convert enhanced response to legacy format
                iep_content = iep_response.model_dump()
                
                # 🎯 DEBUG: Log PLOP grounding metadata handling
                template_name = template_data.get("name", "")
                is_plop = template_name.startswith("PLOP and Goals")
                if is_plop:
                    logger.info(f"🎯 PLOP TEMPLATE DETECTED: {template_name}")
                    logger.info(f"🎯 PLOP content keys before metadata update: {list(iep_content.keys())}")
                    if 'grounding_metadata' in iep_content:
                        logger.info(f"🎯 PLOP grounding_metadata found in iep_content: {iep_content['grounding_metadata']}")
                    if 'plop_sections' in iep_content:
                        logger.info(f"🎯 PLOP sections preserved in content")
                
                # Add enhanced metadata
                iep_content.update({
                    "template_used": template_data.get("name", "Default IEP Template"),
                    "generation_method": "enhanced_rag_metadata_aware",
                    "ai_model": "gemini-2.5-flash",
                    "generated_at": str(initial_data.get("meeting_date", "")),
                    "evidence_metadata": evidence_metadata,
                    "quality_score": evidence_metadata.get('quality_assessment', {}).get('overall_score', 0.0),
                    "evidence_sources": evidence_metadata.get('total_evidence_chunks', 0),
                    "confidence_scores": evidence_metadata.get('confidence_scores', {}),
                    # 🌐 CRITICAL: Add grounding metadata if present
                    "google_search_grounding": evidence_metadata.get('google_search_grounding', None)
                })
                
                logger.info(f"📊 [BACKEND-SERVICE] Enhanced generation quality score: {evidence_metadata.get('quality_assessment', {}).get('overall_score', 0.0):.3f}")
                logger.info(f"📚 [BACKEND-SERVICE] Evidence sources used: {evidence_metadata.get('total_evidence_chunks', 0)}")
                
                # 🌐 Log grounding status
                if evidence_metadata.get('google_search_grounding'):
                    grounding_data = evidence_metadata['google_search_grounding']
                    logger.info(f"🌐 [BACKEND-SERVICE] Google Search grounding ACTIVE: {len(grounding_data.get('web_search_queries', []))} queries performed")
                else:
                    logger.warning(f"⚠️ [BACKEND-SERVICE] Google Search grounding NOT ACTIVE (requested: {enable_google_search_grounding})")
                
                # 🎯 DEBUG: Final PLOP content check
                if is_plop:
                    logger.info(f"🎯 PLOP FINAL content keys after metadata update: {list(iep_content.keys())}")
                    if 'google_search_grounding' in iep_content:
                        logger.info(f"🎯 PLOP google_search_grounding in final content: {bool(iep_content['google_search_grounding'])}")
                        if iep_content['google_search_grounding']:
                            logger.info(f"🎯 PLOP grounding keys: {list(iep_content['google_search_grounding'].keys())}")
                
            else:
                logger.warning(f"⚠️ [BACKEND-SERVICE] Using deprecated legacy RAG generator...")
                
                # Legacy generation method (deprecated)
                iep_content = await self.iep_generator.generate_iep(
                    template=template_data,
                    student_data=student_data,
                    previous_ieps=previous_ieps_data,
                    previous_assessments=previous_pls_data,
                    enable_google_search_grounding=enable_google_search_grounding
                )
                
                # Add basic metadata
                iep_content.update({
                    "template_used": template_data.get("name", "Default IEP Template"),
                    "generation_method": "legacy_rag_basic",
                    "ai_model": "gemini-2.5-flash",
                    "generated_at": str(initial_data.get("meeting_date", ""))
                })
            
            rag_end = time.time()
            logger.info(f"✅ [BACKEND-SERVICE] RAG generation completed successfully in {rag_end - rag_start:.2f}s")
            logger.info(f"📄 [BACKEND-SERVICE] Generated content sections: {list(iep_content.keys()) if isinstance(iep_content, dict) else 'non-dict response'}")
            
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
        
        # 🌐 CRITICAL FIX: Include grounding metadata in API response
        # The generated iep_content contains grounding metadata, but it's stored in the database
        # We need to return it separately so the frontend can access it
        response = dict(iep)  # Create a copy of the IEP record
        
        # Extract grounding metadata from the generated content
        if iep_content and isinstance(iep_content, dict):
            grounding_metadata = iep_content.get('google_search_grounding')
            if grounding_metadata:
                response['grounding_metadata'] = grounding_metadata
                logger.info(f"🌐 [BACKEND-SERVICE] Grounding metadata added to API response: {len(grounding_metadata.get('web_search_queries', []))} queries")
            else:
                logger.warning(f"⚠️ [BACKEND-SERVICE] No grounding metadata found in generated content")
        
        return response
    
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
        user_id: UUID = None,
        enable_google_search_grounding: bool = False
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
            context,
            enable_google_search_grounding
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
    
    async def _fetch_assessment_data(self, document_id: str, student_id: UUID) -> Dict[str, Any]:
        """
        🔗 ASSESSMENT DATA BRIDGE: Fetch real assessment data from Document AI pipeline
        
        This method retrieves:
        1. Extracted structured data from Document AI
        2. Individual test scores (WISC-V, WIAT-IV, etc.)
        3. Quantified composite scores
        4. Educational recommendations
        
        Returns formatted data ready for LLM consumption
        """
        logger.info(f"🔗 [ASSESSMENT-BRIDGE] Starting data retrieval for document {document_id}")
        
        assessment_data = {
            "present_levels_summary": "",
            "strengths_formatted": "",
            "areas_of_concern_formatted": "",
            "learning_profile_summary": "",
            "test_scores": [],
            "composite_scores": {},
            "educational_objectives": [],
            "recommendations": [],
            "extraction_confidence": 0.0
        }
        
        try:
            # Import assessment repository and use the SAME session as IEP repository
            from ..repositories.assessment_repository import AssessmentRepository
            assessment_repo = AssessmentRepository(self.repository.session)
            
            # 1. Fetch structured data from Document AI extraction
            logger.info(f"📄 [ASSESSMENT-BRIDGE] Fetching structured data...")
            try:
                from uuid import UUID as ConvertUUID
                doc_uuid = ConvertUUID(document_id)
                extracted_data = await assessment_repo.get_document_extracted_data(doc_uuid)
                
                if extracted_data and extracted_data.get("structured_data"):
                    structured = extracted_data["structured_data"]
                    
                    # Extract educational objectives
                    if "educational_objectives" in structured:
                        assessment_data["educational_objectives"] = structured["educational_objectives"]
                        logger.info(f"✅ Found {len(structured['educational_objectives'])} educational objectives")
                    
                    # Extract performance levels
                    if "performance_levels" in structured:
                        perf_levels = structured["performance_levels"]
                        assessment_data["present_levels_summary"] = self._format_performance_levels(perf_levels)
                        logger.info(f"✅ Formatted performance levels from {len(perf_levels)} areas")
                    
                    # Extract strengths
                    if "strengths" in structured:
                        assessment_data["strengths_formatted"] = self._format_list_items(structured["strengths"], "Strengths")
                        logger.info(f"✅ Formatted {len(structured['strengths'])} strengths")
                    
                    # Extract areas of concern
                    if "areas_of_concern" in structured:
                        assessment_data["areas_of_concern_formatted"] = self._format_list_items(structured["areas_of_concern"], "Areas of Concern")
                        logger.info(f"✅ Formatted {len(structured['areas_of_concern'])} areas of concern")
                    
                    # Extract recommendations
                    if "recommendations" in structured:
                        assessment_data["recommendations"] = structured["recommendations"]
                        logger.info(f"✅ Found {len(structured['recommendations'])} recommendations")
                    
                    # Set extraction confidence
                    assessment_data["extraction_confidence"] = extracted_data.get("extraction_confidence", 0.0)
                    
            except Exception as e:
                logger.error(f"❌ [ASSESSMENT-BRIDGE] Error fetching structured data: {e}")
            
            # 2. Fetch individual test scores
            logger.info(f"📊 [ASSESSMENT-BRIDGE] Fetching test scores...")
            try:
                scores = await assessment_repo.get_document_scores(doc_uuid)
                if scores:
                    assessment_data["test_scores"] = self._format_test_scores(scores)
                    logger.info(f"✅ Formatted {len(scores)} test scores")
            except Exception as e:
                logger.error(f"❌ [ASSESSMENT-BRIDGE] Error fetching test scores: {e}")
            
            # 3. Fetch quantified data (composite scores)
            logger.info(f"🧮 [ASSESSMENT-BRIDGE] Fetching quantified data...")
            try:
                quantified_data = await assessment_repo.get_student_quantified_data(student_id)
                if quantified_data:
                    # Get the most recent quantified data
                    latest_data = max(quantified_data, key=lambda x: x.get("created_at", ""))
                    assessment_data["composite_scores"] = self._format_composite_scores(latest_data)
                    logger.info(f"✅ Formatted composite scores from latest assessment")
            except Exception as e:
                logger.error(f"❌ [ASSESSMENT-BRIDGE] Error fetching quantified data: {e}")
            
            # Log summary of retrieved data
            data_summary = {
                "objectives_count": len(assessment_data["educational_objectives"]),
                "test_scores_count": len(assessment_data["test_scores"]),
                "has_present_levels": bool(assessment_data["present_levels_summary"]),
                "has_strengths": bool(assessment_data["strengths_formatted"]),
                "has_concerns": bool(assessment_data["areas_of_concern_formatted"]),
                "confidence": assessment_data["extraction_confidence"]
            }
            logger.info(f"📋 [ASSESSMENT-BRIDGE] Data retrieval complete: {data_summary}")
            
        except Exception as e:
            logger.error(f"❌ [ASSESSMENT-BRIDGE] Critical error in assessment data retrieval: {e}")
            # Return empty structure on error - IEP generation will use fallback
        
        return assessment_data
    
    def _format_performance_levels(self, performance_levels: Dict[str, Any]) -> str:
        """Format performance levels into readable summary"""
        if not performance_levels:
            return ""
        
        formatted_parts = []
        for area, data in performance_levels.items():
            if isinstance(data, dict) and "current_level" in data:
                formatted_parts.append(f"{area.title()}: {data['current_level']}")
            elif isinstance(data, str):
                formatted_parts.append(f"{area.title()}: {data}")
        
        return "; ".join(formatted_parts)
    
    def _format_list_items(self, items: List[str], category: str) -> str:
        """Format list of items into readable text"""
        if not items:
            return ""
        
        if len(items) == 1:
            return items[0]
        elif len(items) <= 3:
            return f"{', '.join(items[:-1])}, and {items[-1]}"
        else:
            return f"{', '.join(items[:3])}, and {len(items)-3} additional {category.lower()}"
    
    def _format_test_scores(self, scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format test scores for LLM consumption"""
        formatted_scores = []
        
        for score in scores:
            formatted_score = {
                "test_name": score.get("test_name", ""),
                "subtest_name": score.get("subtest_name", ""),
                "standard_score": score.get("standard_score"),
                "percentile_rank": score.get("percentile_rank"),
                "score_interpretation": self._interpret_standard_score(score.get("standard_score")),
                "confidence": score.get("extraction_confidence", 0.0)
            }
            formatted_scores.append(formatted_score)
        
        return formatted_scores
    
    def _format_composite_scores(self, quantified_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format composite scores for LLM consumption"""
        composite_mapping = {
            "cognitive_composite": "Cognitive Ability",
            "academic_composite": "Academic Achievement", 
            "behavioral_composite": "Behavioral Functioning",
            "reading_composite": "Reading Skills",
            "math_composite": "Mathematics",
            "writing_composite": "Written Expression",
            "language_composite": "Language Skills"
        }
        
        formatted_composites = {}
        for key, label in composite_mapping.items():
            if quantified_data.get(key) is not None:
                score = quantified_data[key]
                formatted_composites[label] = {
                    "score": score,
                    "interpretation": self._interpret_composite_score(score),
                    "percentile_equivalent": self._score_to_percentile(score)
                }
        
        return formatted_composites
    
    def _interpret_standard_score(self, standard_score: Optional[int]) -> str:
        """Interpret standard score into performance level"""
        if standard_score is None:
            return "Not available"
        
        if standard_score >= 130:
            return "Very Superior"
        elif standard_score >= 120:
            return "Superior" 
        elif standard_score >= 110:
            return "High Average"
        elif standard_score >= 90:
            return "Average"
        elif standard_score >= 80:
            return "Low Average"
        elif standard_score >= 70:
            return "Borderline"
        else:
            return "Significantly Below Average"
    
    def _interpret_composite_score(self, composite_score: float) -> str:
        """Interpret 0-100 composite score into performance level"""
        if composite_score >= 85:
            return "Above Average"
        elif composite_score >= 70:
            return "Average"
        elif composite_score >= 55:
            return "Below Average"
        elif composite_score >= 40:
            return "Low"
        else:
            return "Significantly Below Average"
    
    def _score_to_percentile(self, composite_score: float) -> int:
        """Convert 0-100 composite score to approximate percentile"""
        # Simple linear mapping for demonstration
        # In practice, you'd use actual standardization tables
        return min(99, max(1, int(composite_score)))
