"""
RAG Integration Layer - Connects Assessment Pipeline to Special Education RAG System
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
import httpx

from assessment_pipeline_service.schemas.assessment_schemas import QuantifiedMetricsDTO
from assessment_pipeline_service.src.quality_assurance import QualityAssuranceEngine
from .service_clients import special_education_client

logger = logging.getLogger(__name__)

class RAGIntegrationService:
    """Integrates quantified assessment data with the existing RAG system with quality controls"""
    
    def __init__(self, special_ed_service_url: str = "http://localhost:8005"):
        self.special_ed_service_url = special_ed_service_url
        self.timeout = 300  # 5 minutes for RAG operations
        self.quality_engine = QualityAssuranceEngine()
        
    async def create_rag_enhanced_iep_with_quality_controls(
        self,
        student_id: str,
        quantified_data: Dict[str, Any],
        template_id: Optional[str] = None,
        academic_year: str = "2025-2026",
        apply_quality_gates: bool = True
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
                    
                    # Apply quality assurance validation
                    quality_results = await self._validate_iep_quality(
                        iep_result, quantified_data, rag_context
                    )
                    
                    # Enhance the result with assessment pipeline metadata and quality metrics
                    enhanced_result = {
                        **iep_result,
                        "assessment_pipeline_metadata": {
                            "quantified_data_id": str(quantified_data.get("id", "unknown")),
                            "assessment_date": quantified_data.get("assessment_date", datetime.utcnow().isoformat()),
                            "confidence_metrics": quantified_data.get("confidence_metrics", {}),
                            "source_documents": quantified_data.get("source_documents", []),
                            "pipeline_version": "2.0"
                        },
                        "quality_assessment": quality_results
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
    
    def _prepare_rag_context(self, quantified_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare quantified assessment data for RAG consumption"""
        
        # Extract key metrics for RAG
        context = {
            "assessment_summary": self._generate_assessment_summary(quantified_data),
            "present_levels": self._format_present_levels_for_rag(quantified_data.get("standardized_plop")),
            "quantified_metrics": self._extract_quantified_metrics(quantified_data),
            "priority_goals": quantified_data.get("priority_goals", []),
            "service_recommendations": quantified_data.get("service_recommendations", []),
            "learning_profile": quantified_data.get("learning_style_profile", {}),
            "eligibility_data": {
                "category": quantified_data.get("eligibility_category"),
                "primary_disability": quantified_data.get("primary_disability"),
                "secondary_disabilities": quantified_data.get("secondary_disabilities", [])
            }
        }
        
        return context
    
    def _generate_assessment_summary(self, quantified_data: Dict[str, Any]) -> str:
        """Generate a comprehensive assessment summary for RAG"""
        
        summary_parts = []
        
        # Cognitive summary
        if quantified_data.get("cognitive_composite"):
            cognitive_level = self._interpret_composite_score(quantified_data["cognitive_composite"])
            summary_parts.append(f"Cognitive functioning is in the {cognitive_level} range")
        
        # Academic summary
        academic_areas = []
        if quantified_data.get("reading_composite"):
            reading_level = self._interpret_composite_score(quantified_data["reading_composite"])
            academic_areas.append(f"reading ({reading_level})")
        
        if quantified_data.get("math_composite"):
            math_level = self._interpret_composite_score(quantified_data["math_composite"])
            academic_areas.append(f"mathematics ({math_level})")
        
        if quantified_data.get("writing_composite"):
            writing_level = self._interpret_composite_score(quantified_data["writing_composite"])
            academic_areas.append(f"written expression ({writing_level})")
        
        if academic_areas:
            summary_parts.append(f"Academic performance: {', '.join(academic_areas)}")
        
        # Behavioral summary
        if quantified_data.get("behavioral_composite"):
            behavioral_level = self._interpret_composite_score(quantified_data["behavioral_composite"])
            summary_parts.append(f"Behavioral functioning shows {behavioral_level} patterns")
        
        # Growth summary
        if quantified_data.get("growth_rate"):
            growth_summary = self._summarize_growth_patterns(quantified_data["growth_rate"])
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
    
    def _extract_quantified_metrics(self, quantified_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key quantified metrics for RAG"""
        
        metrics = {
            "composite_scores": {
                "cognitive": quantified_data.get("cognitive_composite"),
                "academic": quantified_data.get("academic_composite"),
                "behavioral": quantified_data.get("behavioral_composite"),
                "reading": quantified_data.get("reading_composite"),
                "math": quantified_data.get("math_composite"),
                "writing": quantified_data.get("writing_composite")
            },
            "growth_indicators": quantified_data.get("progress_indicators", []),
            "processing_profile": quantified_data.get("cognitive_processing_profile", {}),
            "learning_style": quantified_data.get("learning_style_profile", {}),
            "confidence_metrics": quantified_data.get("confidence_metrics", {})
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
    
    async def _validate_iep_quality(
        self, 
        iep_result: Dict[str, Any], 
        quantified_data: Dict[str, Any],
        rag_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply comprehensive quality validation to generated IEP content"""
        
        logger.info("Applying quality assurance validation to generated IEP")
        
        # Extract generated content from IEP result
        generated_content = self._extract_generated_content(iep_result)
        
        # Prepare source documents for regurgitation detection
        source_documents = self._prepare_source_documents(quantified_data)
        
        # Apply quality validation
        quality_results = await self.quality_engine.validate_generated_content(
            generated_content=generated_content,
            source_documents=source_documents,
            quantified_data=self._format_quantified_data_for_quality_check(quantified_data)
        )
        
        # Log quality results
        logger.info(
            f"Quality validation complete: "
            f"Score: {quality_results['overall_quality_score']:.2f}, "
            f"Passes gates: {quality_results['passes_quality_gates']}, "
            f"Status: {quality_results['approval_status']}"
        )
        
        return quality_results
    
    def _extract_generated_content(self, iep_result: Dict[str, Any]) -> Dict[str, str]:
        """Extract textual content from IEP result for quality analysis"""
        
        generated_content = {}
        
        # Extract content from the IEP structure
        iep_content = iep_result.get("content", {})
        
        # Standard IEP sections to analyze
        sections_to_analyze = [
            "present_levels", "long_term_goals", "short_term_goals", 
            "oral_language", "reading_familiar", "reading_unfamiliar", 
            "reading_comprehension", "spelling", "writing", "concept_development",
            "math_goals", "recommendations"
        ]
        
        for section in sections_to_analyze:
            if section in iep_content and iep_content[section]:
                content = iep_content[section]
                # Handle different content formats
                if isinstance(content, dict):
                    # Flatten nested content
                    text_content = self._flatten_content_to_text(content)
                elif isinstance(content, list):
                    # Join list items
                    text_content = " ".join(str(item) for item in content if item)
                else:
                    text_content = str(content)
                
                if text_content and len(text_content.strip()) > 20:
                    generated_content[section] = text_content.strip()
        
        return generated_content
    
    def _flatten_content_to_text(self, content: Dict[str, Any]) -> str:
        """Flatten nested content dictionary to text for analysis"""
        
        text_parts = []
        
        for key, value in content.items():
            if isinstance(value, dict):
                nested_text = self._flatten_content_to_text(value)
                if nested_text:
                    text_parts.append(nested_text)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item.strip():
                        text_parts.append(item.strip())
                    elif isinstance(item, dict):
                        nested_text = self._flatten_content_to_text(item)
                        if nested_text:
                            text_parts.append(nested_text)
            elif isinstance(value, str) and value.strip():
                text_parts.append(value.strip())
        
        return " ".join(text_parts)
    
    def _prepare_source_documents(self, quantified_data: Dict[str, Any]) -> List[str]:
        """Prepare source documents for regurgitation detection"""
        
        source_documents = []
        
        # Add source documents if available
        source_docs = quantified_data.get("source_documents")
        if source_docs:
            if isinstance(source_docs, list):
                source_documents.extend(source_docs)
            elif isinstance(source_docs, str):
                source_documents.append(source_docs)
        
        # Add standardized PLOP content
        standardized_plop = quantified_data.get("standardized_plop")
        if standardized_plop:
            plop_text = self._flatten_content_to_text(standardized_plop)
            if plop_text:
                source_documents.append(plop_text)
        
        # Add assessment narrative if available
        assessment_narrative = quantified_data.get("assessment_narrative")
        if assessment_narrative:
            source_documents.append(assessment_narrative)
        
        return source_documents
    
    def _format_quantified_data_for_quality_check(self, quantified_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format quantified data for quality validation"""
        
        return {
            "academic_metrics": {
                "reading": {
                    "overall_rating": quantified_data.get("reading_composite"),
                    "grade_equivalent": quantified_data.get("reading_grade_equivalent")
                },
                "mathematics": {
                    "overall_rating": quantified_data.get("math_composite"),
                    "grade_equivalent": quantified_data.get("math_grade_equivalent")
                },
                "writing": {
                    "overall_rating": quantified_data.get("writing_composite"),
                    "grade_equivalent": quantified_data.get("writing_grade_equivalent")
                }
            },
            "behavioral_metrics": {
                "attention_focus": {
                    "rating": quantified_data.get("attention_rating")
                },
                "social_emotional": {
                    "rating": quantified_data.get("social_emotional_rating")
                }
            },
            "grade_level_performance": {
                "overall": {
                    "grade_equivalent": quantified_data.get("overall_grade_equivalent"),
                    "percentile": quantified_data.get("overall_percentile")
                }
            },
            "strengths_and_needs": {
                "strengths": quantified_data.get("priority_goals", []),
                "needs": quantified_data.get("identified_needs", [])
            }
        }