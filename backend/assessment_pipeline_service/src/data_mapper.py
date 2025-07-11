"""
Data mapping layer between frontend and backend structures
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
import json

from ..schemas.assessment_schemas import (
    AssessmentUploadDTO, PsychoedScoreDTO, ExtractedDataDTO,
    QuantifiedMetricsDTO, CognitiveProfileDTO, AcademicProfileDTO,
    BehavioralProfileDTO, AssessmentSummaryDTO
)
from ..schemas.pipeline_schemas import (
    PipelineStatusResponseDTO, AssessmentPipelineResponseDTO,
    IntakeResultDTO, QuantificationResultDTO, GenerationResultDTO,
    IEPSectionDTO, GeneratedIEPDTO
)
# Database models have been consolidated into special_education_service
# This mapper now works with dictionaries for service-to-service communication

class DataMapper:
    """Maps between frontend DTOs and backend database models"""
    
    @staticmethod
    def upload_dto_to_dict(dto: AssessmentUploadDTO) -> Dict[str, Any]:
        """Convert upload DTO to dictionary for service communication"""
        
        return {
            "student_id": str(dto.student_id),
            "document_type": dto.document_type.value if hasattr(dto.document_type, 'value') else str(dto.document_type),
            "file_name": dto.file_name,
            "file_path": dto.file_path or f"/tmp/{dto.file_name}",
            "assessment_date": dto.assessment_date.isoformat() if dto.assessment_date else None,
            "assessor_name": dto.assessor_name,
            "assessor_title": dto.assessor_title,
            "referral_reason": dto.referral_reason,
            "processing_status": "pending"
        }
    
    @staticmethod
    def score_dto_to_dict(dto: PsychoedScoreDTO, document_id: UUID) -> Dict[str, Any]:
        """Convert score DTO to dictionary for service communication"""
        
        score_dict = {
            "document_id": str(document_id),
            "test_name": dto.test_name,
            "test_version": dto.test_version,
            "subtest_name": dto.subtest_name,
            "raw_score": dto.raw_score,
            "standard_score": dto.standard_score,
            "scaled_score": dto.scaled_score,
            "t_score": dto.t_score,
            "percentile_rank": dto.percentile_rank,
            "age_equivalent_years": dto.age_equivalent_years,
            "age_equivalent_months": dto.age_equivalent_months,
            "grade_equivalent": dto.grade_equivalent,
            "qualitative_descriptor": dto.qualitative_descriptor,
            "score_classification": dto.score_classification,
            "extraction_confidence": dto.extraction_confidence,
            "confidence_level": dto.confidence_level or 95
        }
        
        # Handle confidence interval
        if dto.confidence_interval:
            score_dict["confidence_interval_lower"] = dto.confidence_interval[0]
            score_dict["confidence_interval_upper"] = dto.confidence_interval[1]
        
        return score_dict
    
    @staticmethod
    def dict_to_score_dto(score_dict: Dict[str, Any]) -> PsychoedScoreDTO:
        """Convert dictionary from service to score DTO"""
        
        confidence_interval = None
        if score_dict.get("confidence_interval_lower") and score_dict.get("confidence_interval_upper"):
            confidence_interval = (score_dict["confidence_interval_lower"], score_dict["confidence_interval_upper"])
        
        return PsychoedScoreDTO(
            test_name=score_dict.get("test_name"),
            test_version=score_dict.get("test_version"),
            subtest_name=score_dict.get("subtest_name"),
            raw_score=score_dict.get("raw_score"),
            standard_score=score_dict.get("standard_score"),
            scaled_score=score_dict.get("scaled_score"),
            t_score=score_dict.get("t_score"),
            percentile_rank=score_dict.get("percentile_rank"),
            age_equivalent_years=score_dict.get("age_equivalent_years"),
            age_equivalent_months=score_dict.get("age_equivalent_months"),
            grade_equivalent=score_dict.get("grade_equivalent"),
            confidence_interval=confidence_interval,
            confidence_level=score_dict.get("confidence_level"),
            qualitative_descriptor=score_dict.get("qualitative_descriptor"),
            score_classification=score_dict.get("score_classification"),
            extraction_confidence=score_dict.get("extraction_confidence")
        )
    
    @staticmethod
    def extracted_data_dto_to_dict(
        dto: ExtractedDataDTO,
        document_id: str
    ) -> Dict[str, Any]:
        """Convert extracted data DTO to dictionary for persistence"""
        
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
        
        return {
            "document_id": document_id,
            "extraction_date": dto.extraction_date.isoformat() if dto.extraction_date else None,
            "cognitive_data": cognitive_data,
            "academic_data": academic_data,
            "behavioral_data": behavioral_data,
            "present_levels": dto.present_levels,
            "strengths": dto.strengths,
            "needs": dto.needs,
            "recommendations": dto.recommendations,
            "accommodations": dto.accommodations,
            "extraction_confidence": dto.extraction_confidence,
            "completeness_score": dto.completeness_score,
            "manual_review_required": dto.manual_review_required
        }
    
    @staticmethod
    def cognitive_profile_dict_to_dto(data_dict: Dict[str, Any]) -> CognitiveProfileDTO:
        """Convert cognitive profile dictionary to DTO"""
        
        return CognitiveProfileDTO(
            assessment_date=data_dict.get("assessment_date"),
            full_scale_iq=data_dict.get("full_scale_iq"),
            verbal_comprehension_index=data_dict.get("verbal_comprehension_index"),
            visual_spatial_index=data_dict.get("visual_spatial_index"),
            fluid_reasoning_index=data_dict.get("fluid_reasoning_index"),
            working_memory_index=data_dict.get("working_memory_index"),
            processing_speed_index=data_dict.get("processing_speed_index"),
            general_ability_index=data_dict.get("general_ability_index"),
            cognitive_proficiency_index=data_dict.get("cognitive_proficiency_index"),
            cognitive_strengths=data_dict.get("cognitive_strengths", []),
            cognitive_weaknesses=data_dict.get("cognitive_weaknesses", []),
            processing_patterns=data_dict.get("psw_analysis", {}),
            composite_confidence=data_dict.get("composite_confidence", 0.85)
        )
    
    @staticmethod
    def academic_profile_dict_to_dto(data_dict: Dict[str, Any]) -> AcademicProfileDTO:
        """Convert academic profile dictionary to DTO"""
        
        return AcademicProfileDTO(
            assessment_date=data_dict.get("assessment_date"),
            basic_reading_skills=data_dict.get("basic_reading_skills"),
            reading_comprehension=data_dict.get("reading_comprehension"),
            reading_fluency=data_dict.get("reading_fluency"),
            reading_rate_wpm=data_dict.get("reading_rate"),
            math_calculation=data_dict.get("math_calculation"),
            math_problem_solving=data_dict.get("math_problem_solving"),
            math_fluency=data_dict.get("math_fluency"),
            written_expression=data_dict.get("written_expression"),
            spelling=data_dict.get("spelling"),
            writing_fluency=data_dict.get("writing_fluency"),
            academic_strengths=data_dict.get("academic_strengths", []),
            academic_needs=data_dict.get("academic_needs", []),
            error_patterns=data_dict.get("error_patterns", {})
        )
    
    @staticmethod
    def behavioral_profile_dict_to_dto(data_dict: Dict[str, Any]) -> BehavioralProfileDTO:
        """Convert behavioral profile dictionary to DTO"""
        
        # Extract executive function scores
        executive_scores = {
            "inhibit": data_dict.get("inhibit"),
            "shift": data_dict.get("shift"),
            "emotional_control": data_dict.get("emotional_control"),
            "working_memory": data_dict.get("working_memory_behavior"),
            "plan_organize": data_dict.get("plan_organize")
        }
        
        # Remove None values
        executive_scores = {k: v for k, v in executive_scores.items() if v is not None}
        
        return BehavioralProfileDTO(
            assessment_date=data_dict.get("assessment_date"),
            externalizing_problems=data_dict.get("externalizing_problems"),
            internalizing_problems=data_dict.get("internalizing_problems"),
            behavioral_symptoms_index=data_dict.get("behavioral_symptoms_index"),
            adaptive_skills_composite=data_dict.get("adaptive_skills_composite"),
            hyperactivity=data_dict.get("hyperactivity"),
            aggression=data_dict.get("aggression"),
            anxiety=data_dict.get("anxiety"),
            depression=data_dict.get("depression"),
            attention_problems=data_dict.get("attention_problems"),
            executive_function_scores=executive_scores,
            behavior_frequency_data=data_dict.get("behavior_frequency_data", []),
            antecedent_patterns=data_dict.get("antecedent_data", []),
            effective_interventions=[]  # Would be derived from analysis
        )
    
    @staticmethod
    def quantified_data_dict_to_metrics_dto(data_dict: Dict[str, Any]) -> QuantifiedMetricsDTO:
        """Convert quantified assessment data dictionary to metrics DTO"""
        
        # Extract reading metrics
        reading_metrics = {
            "composite_score": data_dict.get("reading_composite"),
            "growth_rate": data_dict.get("growth_rate", {}).get("reading", 0) if data_dict.get("growth_rate") else 0
        }
        
        # Extract math metrics
        math_metrics = {
            "composite_score": data_dict.get("math_composite"),
            "growth_rate": data_dict.get("growth_rate", {}).get("math", 0) if data_dict.get("growth_rate") else 0
        }
        
        # Extract writing metrics
        writing_metrics = {
            "composite_score": data_dict.get("writing_composite"),
            "growth_rate": data_dict.get("growth_rate", {}).get("writing", 0) if data_dict.get("growth_rate") else 0
        }
        
        # Extract cognitive indices
        cognitive_indices = data_dict.get("cognitive_processing_profile", {})
        
        # Extract behavioral metrics
        attention_metrics = {
            "composite": data_dict.get("behavioral_composite"),
            "executive_function": data_dict.get("executive_composite")
        }
        
        social_emotional_metrics = {
            "composite": data_dict.get("social_emotional_composite"),
            "adaptive": data_dict.get("adaptive_composite")
        }
        
        standardized_plop = data_dict.get("standardized_plop", {})
        learning_style_profile = data_dict.get("learning_style_profile", {})
        
        return QuantifiedMetricsDTO(
            reading_metrics=reading_metrics,
            math_metrics=math_metrics,
            writing_metrics=writing_metrics,
            cognitive_indices=cognitive_indices,
            processing_strengths=standardized_plop.get("strengths", []),
            processing_weaknesses=standardized_plop.get("weaknesses", []),
            attention_metrics=attention_metrics,
            social_emotional_metrics=social_emotional_metrics,
            executive_function_metrics={},
            growth_rates=data_dict.get("growth_rate", {}),
            progress_indicators=data_dict.get("progress_indicators", []),
            learning_style=learning_style_profile.get("primary_style", ""),
            optimal_conditions=learning_style_profile.get("optimal_conditions", []),
            barriers=standardized_plop.get("barriers", []),
            priority_goals=data_dict.get("priority_goals", []),
            service_recommendations=data_dict.get("service_recommendations", [])
        )
    
    @staticmethod
    def pipeline_dict_to_status_dto(data_dict: Dict[str, Any]) -> PipelineStatusResponseDTO:
        """Convert pipeline dictionary to status DTO"""
        from datetime import datetime
        
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
        
        status = data_dict.get("status", "initiated")
        progress = stage_weights.get(status, 0)
        
        # Determine stages completed
        stages_order = ["intake", "extracting", "quantifying", "generating", "review"]
        current_stage = data_dict.get("current_stage")
        current_index = stages_order.index(current_stage) if current_stage in stages_order else -1
        stages_completed = stages_order[:current_index] if current_index >= 0 else []
        
        # Calculate elapsed time
        created_at = data_dict.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif created_at is None:
            created_at = datetime.utcnow()
            
        elapsed = (datetime.utcnow() - created_at).total_seconds()
        
        # Estimate completion (rough estimate: 5 minutes per stage)
        remaining_stages = len(stages_order) - len(stages_completed)
        estimated_completion = datetime.utcnow() + (remaining_stages * 300)  # 5 min per stage
        
        return PipelineStatusResponseDTO(
            pipeline_id=data_dict.get("id"),
            status=status,
            current_stage=current_stage,
            progress_percentage=progress,
            stages_completed=stages_completed,
            current_stage_progress=None,  # Would need sub-stage tracking
            started_at=created_at,
            estimated_completion=estimated_completion if status not in ["completed", "failed"] else None,
            elapsed_seconds=elapsed,
            has_results=status == "completed",
            preview_available=status in ["generating", "review", "completed"],
            has_errors=status == "failed",
            error_message=data_dict.get("error_message")
        )
    
    @staticmethod
    def pipeline_dict_to_response_dto(data_dict: Dict[str, Any]) -> AssessmentPipelineResponseDTO:
        """Convert pipeline dictionary to full response DTO"""
        
        # Parse stage results
        intake_results = None
        if data_dict.get("intake_results"):
            intake_data = data_dict["intake_results"]
            intake_results = IntakeResultDTO(
                documents_processed=intake_data.get("documents_processed", 0),
                extraction_results=intake_data.get("extraction_results", []),
                average_confidence=intake_data.get("average_confidence", 0),
                psychoed_scores_extracted=intake_data.get("scores_extracted", 0),
                review_required_count=intake_data.get("review_required", 0)
            )
        
        quantification_results = None
        if data_dict.get("quantification_results"):
            quant_data = data_dict["quantification_results"]
            quantification_results = QuantificationResultDTO(
                domains_quantified=quant_data.get("domains", []),
                completeness_score=quant_data.get("completeness", 0),
                academic_metrics_generated=quant_data.get("academic_metrics", 0),
                behavioral_matrices_generated=quant_data.get("behavioral_matrices", 0),
                composite_profile_complete=quant_data.get("profile_complete", False),
                missing_data_areas=quant_data.get("missing_areas", [])
            )
        
        generation_results = None
        if data_dict.get("rag_generation_results"):
            gen_data = data_dict["rag_generation_results"]
            generation_results = GenerationResultDTO(
                sections_generated=gen_data.get("sections", []),
                goals_created=gen_data.get("goals_count", 0),
                quality_score=gen_data.get("quality_score", 0),
                regurgitation_check_passed=gen_data.get("regurgitation_passed", False),
                smart_compliance_rate=gen_data.get("smart_compliance", 0),
                professional_terminology_count=gen_data.get("terminology_count", 0)
            )
        
        # Extract IEP content if available
        iep_content = None
        rag_results = data_dict.get("rag_generation_results")
        if rag_results and "iep_content" in rag_results:
            iep_content = rag_results["iep_content"]
        
        return AssessmentPipelineResponseDTO(
            pipeline_id=data_dict.get("id"),
            status=data_dict.get("status"),
            intake_results=intake_results,
            quantification_results=quantification_results,
            generation_results=generation_results,
            review_package=None,  # Would be populated from review_results
            overall_confidence=data_dict.get("overall_confidence", 0),
            total_processing_time=data_dict.get("processing_time_seconds", 0),
            iep_content=iep_content,
            supporting_documents=[],  # Would be populated from relationships
            quality_summary={
                "extraction_confidence": data_dict.get("extraction_confidence"),
                "quantification_completeness": data_dict.get("quantification_completeness"),
                "generation_quality": data_dict.get("generation_quality_score")
            },
            requires_review=data_dict.get("review_status") == "pending" if data_dict.get("review_status") else False
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