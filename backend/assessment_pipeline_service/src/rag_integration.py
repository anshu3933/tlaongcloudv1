"""
RAG Integration Layer - Connects Assessment Pipeline to Special Education RAG System
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
import httpx

from assessment_pipeline_service.models.assessment_models import QuantifiedAssessmentData
from assessment_pipeline_service.schemas.assessment_schemas import QuantifiedMetricsDTO

logger = logging.getLogger(__name__)

class RAGIntegrationService:
    """Integrates quantified assessment data with the existing RAG system"""
    
    def __init__(self, special_ed_service_url: str = "http://localhost:8005"):
        self.special_ed_service_url = special_ed_service_url
        self.timeout = 300  # 5 minutes for RAG operations
        
    async def create_rag_enhanced_iep(
        self,
        student_id: str,
        quantified_data: QuantifiedAssessmentData,
        template_id: Optional[str] = None,
        academic_year: str = "2025-2026"
    ) -> Dict[str, Any]:
        """Create IEP using RAG with quantified assessment data"""
        
        logger.info(f"Creating RAG-enhanced IEP for student {student_id}")
        
        # Convert quantified data to RAG-compatible format
        rag_context = self._prepare_rag_context(quantified_data)
        
        # Create IEP request payload
        iep_request = {
            "student_id": student_id,
            "template_id": template_id,
            "academic_year": academic_year,
            "content": {
                "assessment_summary": rag_context.get("assessment_summary"),
                "present_levels": rag_context.get("present_levels"),
                "quantified_metrics": rag_context.get("quantified_metrics"),
                "priority_goals": rag_context.get("priority_goals"),
                "service_recommendations": rag_context.get("service_recommendations")
            },
            "meeting_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "effective_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "review_date": f"{int(academic_year[:4]) + 1}-01-15"
        }
        
        # Call the special education service RAG endpoint
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.special_ed_service_url}/api/v1/ieps/advanced/create-with-rag",
                    params={"current_user_id": 1, "current_user_role": "teacher"},
                    json=iep_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    iep_result = response.json()
                    logger.info(f"RAG IEP created successfully for student {student_id}")
                    
                    # Enhance the result with assessment pipeline metadata
                    enhanced_result = {
                        **iep_result,
                        "assessment_pipeline_metadata": {
                            "quantified_data_id": str(quantified_data.id),
                            "assessment_date": quantified_data.assessment_date.isoformat(),
                            "confidence_metrics": quantified_data.confidence_metrics,
                            "source_documents": quantified_data.source_documents,
                            "pipeline_version": "2.0"
                        }
                    }
                    
                    return enhanced_result
                else:
                    logger.error(f"RAG IEP creation failed: {response.status_code} - {response.text}")
                    raise Exception(f"RAG service returned status {response.status_code}")
                    
            except httpx.TimeoutException:
                logger.error(f"RAG IEP creation timed out for student {student_id}")
                raise Exception("RAG IEP creation timed out")
            except Exception as e:
                logger.error(f"RAG IEP creation error: {e}")
                raise
    
    def _prepare_rag_context(self, quantified_data: QuantifiedAssessmentData) -> Dict[str, Any]:
        """Prepare quantified assessment data for RAG consumption"""
        
        # Extract key metrics for RAG
        context = {
            "assessment_summary": self._generate_assessment_summary(quantified_data),
            "present_levels": self._format_present_levels_for_rag(quantified_data.standardized_plop),
            "quantified_metrics": self._extract_quantified_metrics(quantified_data),
            "priority_goals": quantified_data.priority_goals or [],
            "service_recommendations": quantified_data.service_recommendations or [],
            "learning_profile": quantified_data.learning_style_profile or {},
            "eligibility_data": {
                "category": quantified_data.eligibility_category,
                "primary_disability": quantified_data.primary_disability,
                "secondary_disabilities": quantified_data.secondary_disabilities or []
            }
        }
        
        return context
    
    def _generate_assessment_summary(self, quantified_data: QuantifiedAssessmentData) -> str:
        """Generate a comprehensive assessment summary for RAG"""
        
        summary_parts = []
        
        # Cognitive summary
        if quantified_data.cognitive_composite:
            cognitive_level = self._interpret_composite_score(quantified_data.cognitive_composite)
            summary_parts.append(f"Cognitive functioning is in the {cognitive_level} range")
        
        # Academic summary
        academic_areas = []
        if quantified_data.reading_composite:
            reading_level = self._interpret_composite_score(quantified_data.reading_composite)
            academic_areas.append(f"reading ({reading_level})")
        
        if quantified_data.math_composite:
            math_level = self._interpret_composite_score(quantified_data.math_composite)
            academic_areas.append(f"mathematics ({math_level})")
        
        if quantified_data.writing_composite:
            writing_level = self._interpret_composite_score(quantified_data.writing_composite)
            academic_areas.append(f"written expression ({writing_level})")
        
        if academic_areas:
            summary_parts.append(f"Academic performance: {', '.join(academic_areas)}")
        
        # Behavioral summary
        if quantified_data.behavioral_composite:
            behavioral_level = self._interpret_composite_score(quantified_data.behavioral_composite)
            summary_parts.append(f"Behavioral functioning shows {behavioral_level} patterns")
        
        # Growth summary
        if quantified_data.growth_rate:
            growth_summary = self._summarize_growth_patterns(quantified_data.growth_rate)
            summary_parts.append(growth_summary)
        
        return ". ".join(summary_parts) + "."
    
    def _format_present_levels_for_rag(self, standardized_plop: Dict[str, Any]) -> Dict[str, Any]:
        """Format present levels for optimal RAG consumption"""
        
        if not standardized_plop:
            return {}
        
        formatted = {
            "academic_performance": {},
            "cognitive_functioning": {},
            "behavioral_functioning": {},
            "functional_performance": {}
        }
        
        # Format academic performance
        academic_perf = standardized_plop.get("academic_performance", {})
        for domain, data in academic_perf.items():
            if isinstance(data, dict):
                formatted["academic_performance"][domain] = {
                    "current_level": f"Grade {data.get('current_level', 'N/A')} equivalent",
                    "strengths": data.get("strengths", []),
                    "needs": data.get("needs", []),
                    "growth_rate": f"{data.get('growth_rate', 0):.1f} grade levels per year"
                }
        
        # Format cognitive functioning
        cognitive_func = standardized_plop.get("cognitive_functioning", {})
        if cognitive_func:
            formatted["cognitive_functioning"] = {
                "overall_ability": self._interpret_composite_score(cognitive_func.get("overall_ability", 50)),
                "processing_strengths": cognitive_func.get("processing_strengths", []),
                "processing_weaknesses": cognitive_func.get("processing_weaknesses", []),
                "learning_style": cognitive_func.get("learning_style", "balanced")
            }
        
        # Format behavioral functioning
        behavioral_func = standardized_plop.get("behavioral_functioning", {})
        if behavioral_func:
            formatted["behavioral_functioning"] = {
                "attention_focus": behavioral_func.get("attention_focus", {}),
                "social_emotional": self._interpret_composite_score(behavioral_func.get("social_emotional", 50)),
                "executive_function": self._interpret_composite_score(behavioral_func.get("executive_function", 50)),
                "adaptive_skills": self._interpret_composite_score(behavioral_func.get("adaptive_skills", 50))
            }
        
        return formatted
    
    def _extract_quantified_metrics(self, quantified_data: QuantifiedAssessmentData) -> Dict[str, Any]:
        """Extract key quantified metrics for RAG"""
        
        metrics = {
            "composite_scores": {
                "cognitive": quantified_data.cognitive_composite,
                "academic": quantified_data.academic_composite,
                "behavioral": quantified_data.behavioral_composite,
                "reading": quantified_data.reading_composite,
                "math": quantified_data.math_composite,
                "writing": quantified_data.writing_composite
            },
            "growth_indicators": quantified_data.progress_indicators or [],
            "processing_profile": quantified_data.cognitive_processing_profile or {},
            "learning_style": quantified_data.learning_style_profile or {},
            "confidence_metrics": quantified_data.confidence_metrics or {}
        }
        
        # Remove None values
        metrics["composite_scores"] = {k: v for k, v in metrics["composite_scores"].items() if v is not None}
        
        return metrics
    
    def _interpret_composite_score(self, score: float) -> str:
        """Interpret normalized composite score (0-100 scale)"""
        
        if score >= 75:
            return "above average"
        elif score >= 50:
            return "average"
        elif score >= 25:
            return "below average"
        else:
            return "significantly below average"
    
    def _summarize_growth_patterns(self, growth_rate: Dict[str, float]) -> str:
        """Summarize growth patterns from quantified data"""
        
        growth_summary = []
        
        for domain, rate in growth_rate.items():
            if domain == "overall":
                continue
                
            if rate >= 1.2:
                growth_summary.append(f"{domain} shows strong growth")
            elif rate >= 0.8:
                growth_summary.append(f"{domain} shows typical growth")
            else:
                growth_summary.append(f"{domain} shows concerning growth patterns")
        
        return "Growth patterns indicate: " + ", ".join(growth_summary)
    
    async def get_student_context_for_rag(self, student_id: str) -> Dict[str, Any]:
        """Get additional student context from special education service"""
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get student information
                student_response = await client.get(
                    f"{self.special_ed_service_url}/api/v1/students/{student_id}"
                )
                
                if student_response.status_code == 200:
                    return student_response.json()
                else:
                    logger.warning(f"Could not get student context: {student_response.status_code}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting student context: {e}")
            return {}
    
    async def get_available_templates(self, grade_level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available IEP templates from special education service"""
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                params = {}
                if grade_level:
                    params["grade_level"] = grade_level
                
                response = await client.get(
                    f"{self.special_ed_service_url}/api/v1/templates",
                    params=params
                )
                
                if response.status_code == 200:
                    return response.json().get("items", [])
                else:
                    logger.warning(f"Could not get templates: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return []
    
    async def validate_rag_service_connection(self) -> bool:
        """Validate connection to the RAG service"""
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.special_ed_service_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"RAG service connection failed: {e}")
            return False