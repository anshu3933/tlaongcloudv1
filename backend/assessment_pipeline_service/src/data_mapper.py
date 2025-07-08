"""
Data mapping layer between frontend and backend structures
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
import json

from assessment_pipeline_service.schemas.assessment_schemas import (
    AssessmentUploadDTO, PsychoedScoreDTO, ExtractedDataDTO,
    QuantifiedMetricsDTO, CognitiveProfileDTO, AcademicProfileDTO,
    BehavioralProfileDTO, AssessmentSummaryDTO
)
from assessment_pipeline_service.schemas.pipeline_schemas import (
    PipelineStatusResponseDTO, AssessmentPipelineResponseDTO,
    IntakeResultDTO, QuantificationResultDTO, GenerationResultDTO,
    IEPSectionDTO, GeneratedIEPDTO
)
from assessment_pipeline_service.models.assessment_models import (
    AssessmentDocument, PsychoedScore, ExtractedAssessmentData,
    CognitiveProfile, AcademicProfile, BehavioralProfile,
    QuantifiedAssessmentData, AssessmentPipeline
)

class DataMapper:
    """Maps between frontend DTOs and backend database models"""
    
    @staticmethod
    def upload_dto_to_document(dto: AssessmentUploadDTO) -> AssessmentDocument:
        """Convert upload DTO to database model"""
        
        return AssessmentDocument(
            student_id=dto.student_id,
            document_type=dto.document_type,
            file_name=dto.file_name,
            file_path=dto.file_path or f"/tmp/{dto.file_name}",  # Temporary path
            assessment_date=dto.assessment_date,
            assessor_name=dto.assessor_name,
            assessor_title=dto.assessor_title,
            referral_reason=dto.referral_reason
        )
    
    @staticmethod
    def score_dto_to_model(dto: PsychoedScoreDTO, document_id: UUID, student_id: UUID) -> PsychoedScore:
        """Convert score DTO to database model"""
        
        model = PsychoedScore(
            document_id=document_id,
            student_id=student_id,
            test_name=dto.test_name,
            test_version=dto.test_version,
            subtest_name=dto.subtest_name,
            raw_score=dto.raw_score,
            standard_score=dto.standard_score,
            scaled_score=dto.scaled_score,
            t_score=dto.t_score,
            percentile_rank=dto.percentile_rank,
            age_equivalent_years=dto.age_equivalent_years,
            age_equivalent_months=dto.age_equivalent_months,
            grade_equivalent=dto.grade_equivalent,
            qualitative_descriptor=dto.qualitative_descriptor,
            score_classification=dto.score_classification,
            extraction_confidence=dto.extraction_confidence
        )
        
        # Handle confidence interval
        if dto.confidence_interval:
            model.confidence_interval_lower = dto.confidence_interval[0]
            model.confidence_interval_upper = dto.confidence_interval[1]
            model.confidence_level = dto.confidence_level or 95
        
        return model
    
    @staticmethod
    def model_to_score_dto(model: PsychoedScore) -> PsychoedScoreDTO:
        """Convert database model to score DTO"""
        
        confidence_interval = None
        if model.confidence_interval_lower and model.confidence_interval_upper:
            confidence_interval = (model.confidence_interval_lower, model.confidence_interval_upper)
        
        return PsychoedScoreDTO(
            test_name=model.test_name,
            test_version=model.test_version,
            subtest_name=model.subtest_name,
            raw_score=model.raw_score,
            standard_score=model.standard_score,
            scaled_score=model.scaled_score,
            t_score=model.t_score,
            percentile_rank=model.percentile_rank,
            age_equivalent_years=model.age_equivalent_years,
            age_equivalent_months=model.age_equivalent_months,
            grade_equivalent=model.grade_equivalent,
            confidence_interval=confidence_interval,
            confidence_level=model.confidence_level,
            qualitative_descriptor=model.qualitative_descriptor,
            score_classification=model.score_classification,
            extraction_confidence=model.extraction_confidence
        )
    
    @staticmethod
    def extracted_data_to_model(
        dto: ExtractedDataDTO,
        document_id: UUID
    ) -> ExtractedAssessmentData:
        """Convert extracted data DTO to model"""
        
        # Prepare cognitive data
        cognitive_data = {
            "indices": dto.cognitive_indices,
            "scores": [score.model_dump() for score in dto.cognitive_scores]
        }
        
        # Prepare academic data
        academic_data = {
            "composites": dto.academic_composites,
            "scores": [score.model_dump() for score in dto.academic_scores]
        }
        
        # Prepare behavioral data
        behavioral_data = {
            "ratings": dto.behavioral_ratings,
            "observations": dto.behavioral_observations
        }
        
        return ExtractedAssessmentData(
            document_id=document_id,
            extraction_date=dto.extraction_date,
            cognitive_data=cognitive_data,
            academic_data=academic_data,
            behavioral_data=behavioral_data,
            present_levels=dto.present_levels,
            strengths=dto.strengths,
            needs=dto.needs,
            recommendations=dto.recommendations,
            accommodations=dto.accommodations,
            extraction_confidence=dto.extraction_confidence,
            completeness_score=dto.completeness_score,
            manual_review_required=dto.manual_review_required
        )
    
    @staticmethod
    def cognitive_profile_to_dto(model: CognitiveProfile) -> CognitiveProfileDTO:
        """Convert cognitive profile model to DTO"""
        
        return CognitiveProfileDTO(
            assessment_date=model.assessment_date,
            full_scale_iq=model.full_scale_iq,
            verbal_comprehension_index=model.verbal_comprehension_index,
            visual_spatial_index=model.visual_spatial_index,
            fluid_reasoning_index=model.fluid_reasoning_index,
            working_memory_index=model.working_memory_index,
            processing_speed_index=model.processing_speed_index,
            general_ability_index=model.general_ability_index,
            cognitive_proficiency_index=model.cognitive_proficiency_index,
            cognitive_strengths=model.cognitive_strengths or [],
            cognitive_weaknesses=model.cognitive_weaknesses or [],
            processing_patterns=model.psw_analysis or {},
            composite_confidence=model.composite_confidence or 0.85
        )
    
    @staticmethod
    def academic_profile_to_dto(model: AcademicProfile) -> AcademicProfileDTO:
        """Convert academic profile model to DTO"""
        
        return AcademicProfileDTO(
            assessment_date=model.assessment_date,
            basic_reading_skills=model.basic_reading_skills,
            reading_comprehension=model.reading_comprehension,
            reading_fluency=model.reading_fluency,
            reading_rate_wpm=model.reading_rate,
            math_calculation=model.math_calculation,
            math_problem_solving=model.math_problem_solving,
            math_fluency=model.math_fluency,
            written_expression=model.written_expression,
            spelling=model.spelling,
            writing_fluency=model.writing_fluency,
            academic_strengths=model.academic_strengths or [],
            academic_needs=model.academic_needs or [],
            error_patterns=model.error_patterns or {}
        )
    
    @staticmethod
    def behavioral_profile_to_dto(model: BehavioralProfile) -> BehavioralProfileDTO:
        """Convert behavioral profile model to DTO"""
        
        # Extract executive function scores
        executive_scores = {
            "inhibit": model.inhibit,
            "shift": model.shift,
            "emotional_control": model.emotional_control,
            "working_memory": model.working_memory_behavior,
            "plan_organize": model.plan_organize
        }
        
        # Remove None values
        executive_scores = {k: v for k, v in executive_scores.items() if v is not None}
        
        return BehavioralProfileDTO(
            assessment_date=model.assessment_date,
            externalizing_problems=model.externalizing_problems,
            internalizing_problems=model.internalizing_problems,
            behavioral_symptoms_index=model.behavioral_symptoms_index,
            adaptive_skills_composite=model.adaptive_skills_composite,
            hyperactivity=model.hyperactivity,
            aggression=model.aggression,
            anxiety=model.anxiety,
            depression=model.depression,
            attention_problems=model.attention_problems,
            executive_function_scores=executive_scores,
            behavior_frequency_data=model.behavior_frequency_data or [],
            antecedent_patterns=model.antecedent_data or [],
            effective_interventions=[]  # Would be derived from analysis
        )
    
    @staticmethod
    def quantified_data_to_metrics_dto(model: QuantifiedAssessmentData) -> QuantifiedMetricsDTO:
        """Convert quantified assessment data to metrics DTO"""
        
        # Extract reading metrics
        reading_metrics = {
            "composite_score": model.reading_composite,
            "growth_rate": model.growth_rate.get("reading", 0) if model.growth_rate else 0
        }
        
        # Extract math metrics
        math_metrics = {
            "composite_score": model.math_composite,
            "growth_rate": model.growth_rate.get("math", 0) if model.growth_rate else 0
        }
        
        # Extract writing metrics
        writing_metrics = {
            "composite_score": model.writing_composite,
            "growth_rate": model.growth_rate.get("writing", 0) if model.growth_rate else 0
        }
        
        # Extract cognitive indices
        cognitive_indices = model.cognitive_processing_profile or {}
        
        # Extract behavioral metrics
        attention_metrics = {
            "composite": model.behavioral_composite,
            "executive_function": model.executive_composite
        }
        
        social_emotional_metrics = {
            "composite": model.social_emotional_composite,
            "adaptive": model.adaptive_composite
        }
        
        return QuantifiedMetricsDTO(
            reading_metrics=reading_metrics,
            math_metrics=math_metrics,
            writing_metrics=writing_metrics,
            cognitive_indices=cognitive_indices,
            processing_strengths=model.standardized_plop.get("strengths", []) if model.standardized_plop else [],
            processing_weaknesses=model.standardized_plop.get("weaknesses", []) if model.standardized_plop else [],
            attention_metrics=attention_metrics,
            social_emotional_metrics=social_emotional_metrics,
            executive_function_metrics={},
            growth_rates=model.growth_rate or {},
            progress_indicators=model.progress_indicators or [],
            learning_style=model.learning_style_profile.get("primary_style", "") if model.learning_style_profile else "",
            optimal_conditions=model.learning_style_profile.get("optimal_conditions", []) if model.learning_style_profile else [],
            barriers=model.standardized_plop.get("barriers", []) if model.standardized_plop else [],
            priority_goals=model.priority_goals or [],
            service_recommendations=model.service_recommendations or []
        )
    
    @staticmethod
    def pipeline_to_status_dto(model: AssessmentPipeline) -> PipelineStatusResponseDTO:
        """Convert pipeline model to status DTO"""
        
        # Calculate progress
        stage_weights = {
            "initiated": 0,
            "intake": 20,
            "extracting": 40,
            "quantifying": 60,
            "generating": 80,
            "review": 90,
            "completed": 100,
            "failed": 0
        }
        
        progress = stage_weights.get(model.status, 0)
        
        # Determine stages completed
        stages_order = ["intake", "extracting", "quantifying", "generating", "review"]
        current_index = stages_order.index(model.current_stage) if model.current_stage in stages_order else -1
        stages_completed = stages_order[:current_index] if current_index >= 0 else []
        
        # Calculate elapsed time
        elapsed = (datetime.utcnow() - model.created_at).total_seconds()
        
        # Estimate completion (rough estimate: 5 minutes per stage)
        remaining_stages = len(stages_order) - len(stages_completed)
        estimated_completion = datetime.utcnow() + (remaining_stages * 300)  # 5 min per stage
        
        return PipelineStatusResponseDTO(
            pipeline_id=model.id,
            status=model.status,
            current_stage=model.current_stage,
            progress_percentage=progress,
            stages_completed=stages_completed,
            current_stage_progress=None,  # Would need sub-stage tracking
            started_at=model.created_at,
            estimated_completion=estimated_completion if model.status not in ["completed", "failed"] else None,
            elapsed_seconds=elapsed,
            has_results=model.status == "completed",
            preview_available=model.status in ["generating", "review", "completed"],
            has_errors=model.status == "failed",
            error_message=model.error_message
        )
    
    @staticmethod
    def pipeline_to_response_dto(model: AssessmentPipeline) -> AssessmentPipelineResponseDTO:
        """Convert pipeline model to full response DTO"""
        
        # Parse stage results
        intake_results = None
        if model.intake_results:
            intake_results = IntakeResultDTO(
                documents_processed=model.intake_results.get("documents_processed", 0),
                extraction_results=model.intake_results.get("extraction_results", []),
                average_confidence=model.intake_results.get("average_confidence", 0),
                psychoed_scores_extracted=model.intake_results.get("scores_extracted", 0),
                review_required_count=model.intake_results.get("review_required", 0)
            )
        
        quantification_results = None
        if model.quantification_results:
            quantification_results = QuantificationResultDTO(
                domains_quantified=model.quantification_results.get("domains", []),
                completeness_score=model.quantification_results.get("completeness", 0),
                academic_metrics_generated=model.quantification_results.get("academic_metrics", 0),
                behavioral_matrices_generated=model.quantification_results.get("behavioral_matrices", 0),
                composite_profile_complete=model.quantification_results.get("profile_complete", False),
                missing_data_areas=model.quantification_results.get("missing_areas", [])
            )
        
        generation_results = None
        if model.rag_generation_results:
            generation_results = GenerationResultDTO(
                sections_generated=model.rag_generation_results.get("sections", []),
                goals_created=model.rag_generation_results.get("goals_count", 0),
                quality_score=model.rag_generation_results.get("quality_score", 0),
                regurgitation_check_passed=model.rag_generation_results.get("regurgitation_passed", False),
                smart_compliance_rate=model.rag_generation_results.get("smart_compliance", 0),
                professional_terminology_count=model.rag_generation_results.get("terminology_count", 0)
            )
        
        # Extract IEP content if available
        iep_content = None
        if model.rag_generation_results and "iep_content" in model.rag_generation_results:
            iep_content = model.rag_generation_results["iep_content"]
        
        return AssessmentPipelineResponseDTO(
            pipeline_id=model.id,
            status=model.status,
            intake_results=intake_results,
            quantification_results=quantification_results,
            generation_results=generation_results,
            review_package=None,  # Would be populated from review_results
            overall_confidence=model.overall_confidence or 0,
            total_processing_time=model.processing_time_seconds or 0,
            iep_content=iep_content,
            supporting_documents=[],  # Would be populated from relationships
            quality_summary={
                "extraction_confidence": model.extraction_confidence,
                "quantification_completeness": model.quantification_completeness,
                "generation_quality": model.generation_quality_score
            },
            requires_review=model.review_status == "pending" if model.review_status else False
        )
    
    @staticmethod
    def map_frontend_to_backend_assessment_data(frontend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map frontend form data to backend processing format"""
        
        backend_data = {
            "student_info": {
                "id": frontend_data.get("studentId"),
                "name": frontend_data.get("studentName"),
                "grade": frontend_data.get("gradeLevel"),
                "date_of_birth": frontend_data.get("dateOfBirth"),
                "primary_disability": frontend_data.get("primaryDisability")
            },
            "assessment_info": {
                "date": frontend_data.get("assessmentDate"),
                "type": frontend_data.get("assessmentType"),
                "assessor": frontend_data.get("assessorName"),
                "reason": frontend_data.get("referralReason")
            },
            "scores": DataMapper._map_frontend_scores(frontend_data.get("scores", {})),
            "observations": frontend_data.get("observations", []),
            "recommendations": frontend_data.get("recommendations", [])
        }
        
        return backend_data
    
    @staticmethod
    def _map_frontend_scores(frontend_scores: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Map frontend score format to backend format"""
        
        mapped_scores = []
        
        # Cognitive scores
        if "cognitive" in frontend_scores:
            for index_name, score_data in frontend_scores["cognitive"].items():
                mapped_scores.append({
                    "test_name": "WISC-V",  # Would be dynamic
                    "subtest_name": index_name,
                    "standard_score": score_data.get("score"),
                    "percentile_rank": score_data.get("percentile"),
                    "confidence_interval": score_data.get("confidenceInterval")
                })
        
        # Academic scores
        if "academic" in frontend_scores:
            for domain, domain_scores in frontend_scores["academic"].items():
                for subtest, score_data in domain_scores.items():
                    mapped_scores.append({
                        "test_name": "WIAT-IV",  # Would be dynamic
                        "subtest_name": f"{domain} - {subtest}",
                        "standard_score": score_data.get("score"),
                        "percentile_rank": score_data.get("percentile"),
                        "grade_equivalent": score_data.get("gradeEquivalent")
                    })
        
        return mapped_scores
    
    @staticmethod
    def map_backend_to_frontend_iep_data(backend_iep: Dict[str, Any]) -> Dict[str, Any]:
        """Map backend IEP data to frontend display format"""
        
        frontend_data = {
            "studentInfo": backend_iep.get("student_info", {}),
            "presentLevels": DataMapper._format_present_levels_for_frontend(
                backend_iep.get("present_levels", {})
            ),
            "goals": DataMapper._format_goals_for_frontend(
                backend_iep.get("annual_goals", [])
            ),
            "services": DataMapper._format_services_for_frontend(
                backend_iep.get("services", {})
            ),
            "accommodations": backend_iep.get("accommodations", {}).get("items", []),
            "metadata": {
                "generatedDate": backend_iep.get("generation_metadata", {}).get("timestamp"),
                "confidence": backend_iep.get("quality_metrics", {}).get("overall_score", 0),
                "dataSourcesCount": len(backend_iep.get("generation_metadata", {}).get("data_sources", []))
            }
        }
        
        return frontend_data
    
    @staticmethod
    def _format_present_levels_for_frontend(present_levels: Dict[str, Any]) -> Dict[str, Any]:
        """Format present levels for frontend display"""
        
        formatted = {
            "academic": {},
            "functional": {},
            "strengths": present_levels.get("strengths", []),
            "needs": present_levels.get("needs", [])
        }
        
        # Format academic performance
        for domain, data in present_levels.get("academic_performance", {}).items():
            formatted["academic"][domain] = {
                "narrative": data.get("narrative", ""),
                "gradeLevel": data.get("grade_level"),
                "dataPoints": data.get("data_points", [])
            }
        
        # Format functional performance
        for domain, data in present_levels.get("functional_performance", {}).items():
            formatted["functional"][domain] = {
                "narrative": data.get("narrative", ""),
                "frequencyData": data.get("frequency_data", {}),
                "environmentalFactors": data.get("environmental_factors", [])
            }
        
        return formatted
    
    @staticmethod
    def _format_goals_for_frontend(goals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format goals for frontend display"""
        
        formatted_goals = []
        
        for goal in goals:
            formatted_goal = {
                "id": goal.get("id"),
                "area": goal.get("need_area"),
                "currentLevel": goal.get("current_level"),
                "goalText": goal.get("primary_goal", {}).get("text", ""),
                "measurableCriteria": goal.get("primary_goal", {}).get("criteria", ""),
                "targetDate": goal.get("primary_goal", {}).get("target_date"),
                "alternatives": [
                    {
                        "text": alt.get("text", ""),
                        "criteria": alt.get("criteria", "")
                    }
                    for alt in goal.get("alternatives", [])
                ],
                "progressMonitoring": goal.get("progress_monitoring", {})
            }
            formatted_goals.append(formatted_goal)
        
        return formatted_goals
    
    @staticmethod
    def _format_services_for_frontend(services: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format services for frontend display"""
        
        formatted_services = []
        
        for service_type, service_data in services.items():
            if isinstance(service_data, dict):
                formatted_service = {
                    "type": service_type,
                    "frequency": service_data.get("frequency", ""),
                    "duration": service_data.get("duration", ""),
                    "location": service_data.get("location", ""),
                    "provider": service_data.get("provider", ""),
                    "startDate": service_data.get("start_date"),
                    "endDate": service_data.get("end_date")
                }
                formatted_services.append(formatted_service)
        
        return formatted_services