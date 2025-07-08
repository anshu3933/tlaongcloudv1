"""
Complete End-to-End Assessment Pipeline Orchestrator
Coordinates the entire flow from document upload to RAG-enhanced IEP generation
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from pathlib import Path
import json

from assessment_pipeline_service.src.assessment_intake_processor import AssessmentIntakeProcessor
from assessment_pipeline_service.src.quantification_engine import QuantificationEngine
from assessment_pipeline_service.src.rag_integration import RAGIntegrationService
from assessment_pipeline_service.schemas.assessment_schemas import (
    AssessmentUploadDTO, ExtractedDataDTO, QuantifiedMetricsDTO
)

logger = logging.getLogger(__name__)

class PipelineStage:
    """Represents a stage in the assessment pipeline"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = "pending"  # pending, running, completed, failed
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.result = None
        self.error_message = None
        self.confidence_score = None
    
    def start(self):
        """Mark stage as started"""
        self.status = "running"
        self.start_time = datetime.utcnow()
        logger.info(f"Starting pipeline stage: {self.name}")
    
    def complete(self, result: Any = None, confidence: float = None):
        """Mark stage as completed"""
        self.status = "completed"
        self.end_time = datetime.utcnow()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.result = result
        self.confidence_score = confidence
        logger.info(f"Completed pipeline stage: {self.name} in {self.duration:.2f}s")
    
    def fail(self, error: str):
        """Mark stage as failed"""
        self.status = "failed"
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
        self.error_message = error
        logger.error(f"Failed pipeline stage: {self.name} - {error}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stage to dictionary for reporting"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration,
            "confidence_score": self.confidence_score,
            "error_message": self.error_message
        }

class AssessmentPipelineOrchestrator:
    """Orchestrates the complete assessment pipeline from upload to IEP generation"""
    
    def __init__(self):
        self.intake_processor = AssessmentIntakeProcessor()
        self.quantification_engine = QuantificationEngine()
        self.rag_integration = RAGIntegrationService()
        
        # Pipeline configuration
        self.pipeline_id = None
        self.stages = []
        self.overall_status = "initialized"
        self.start_time = None
        self.end_time = None
        self.total_duration = None
        
        # Results storage
        self.pipeline_results = {}
        self.final_output = None
        
    def initialize_pipeline(self, pipeline_id: str = None) -> str:
        """Initialize a new pipeline run"""
        self.pipeline_id = pipeline_id or str(uuid4())
        self.overall_status = "initialized"
        self.start_time = datetime.utcnow()
        self.stages = []
        self.pipeline_results = {}
        
        # Define pipeline stages
        self.stages = [
            PipelineStage(
                "document_intake",
                "Process uploaded assessment documents using Google Document AI"
            ),
            PipelineStage(
                "score_extraction", 
                "Extract and structure psychoeducational test scores"
            ),
            PipelineStage(
                "data_quantification",
                "Convert raw scores to quantified metrics and PLOP data"
            ),
            PipelineStage(
                "rag_enhancement",
                "Generate RAG-enhanced IEP using quantified assessment data"
            )
        ]
        
        logger.info(f"Initialized assessment pipeline: {self.pipeline_id}")
        return self.pipeline_id
    
    async def execute_complete_pipeline(
        self,
        student_id: str,
        assessment_documents: List[AssessmentUploadDTO],
        template_id: Optional[str] = None,
        academic_year: str = "2025-2026",
        generate_iep: bool = True
    ) -> Dict[str, Any]:
        """Execute the complete assessment pipeline"""
        
        try:
            pipeline_id = self.initialize_pipeline()
            self.overall_status = "running"
            
            logger.info(f"Executing complete assessment pipeline for student {student_id}")
            logger.info(f"Processing {len(assessment_documents)} documents")
            
            # Stage 1: Document Intake and Processing
            stage_1 = self.stages[0]
            stage_1.start()
            
            try:
                extracted_data = []
                for doc in assessment_documents:
                    # Process each document through Document AI
                    extraction_result = await self.intake_processor.process_document(
                        file_path=doc.file_path,
                        assessment_type=doc.assessment_type,
                        metadata={
                            "student_id": student_id,
                            "document_id": doc.document_id if hasattr(doc, 'document_id') else str(uuid4())
                        }
                    )
                    extracted_data.append(extraction_result)
                
                # Calculate overall extraction confidence
                confidences = [data.extraction_confidence for data in extracted_data if data.extraction_confidence]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                stage_1.complete(result=extracted_data, confidence=avg_confidence)
                self.pipeline_results["extracted_data"] = extracted_data
                
            except Exception as e:
                stage_1.fail(str(e))
                raise
            
            # Stage 2: Score Extraction and Structuring
            stage_2 = self.stages[1]
            stage_2.start()
            
            try:
                # Extract structured scores from all documents
                all_scores = []
                for data in extracted_data:
                    # This would extract individual test scores
                    scores = await self._extract_scores_from_data(data)
                    all_scores.extend(scores)
                
                stage_2.complete(result=all_scores, confidence=avg_confidence)
                self.pipeline_results["psychoed_scores"] = all_scores
                
            except Exception as e:
                stage_2.fail(str(e))
                raise
            
            # Stage 3: Data Quantification
            stage_3 = self.stages[2]
            stage_3.start()
            
            try:
                # Convert to quantified assessment data
                student_info = {"id": student_id}  # Would get from database
                quantified_data = await self.quantification_engine.quantify_assessment_data(
                    extracted_data, student_info
                )
                
                stage_3.complete(result=quantified_data)
                self.pipeline_results["quantified_data"] = quantified_data
                
            except Exception as e:
                stage_3.fail(str(e))
                raise
            
            # Stage 4: RAG-Enhanced IEP Generation (optional)
            if generate_iep:
                stage_4 = self.stages[3]
                stage_4.start()
                
                try:
                    # Generate RAG-enhanced IEP
                    iep_result = await self.rag_integration.create_rag_enhanced_iep(
                        student_id=student_id,
                        quantified_data=quantified_data,
                        template_id=template_id,
                        academic_year=academic_year
                    )
                    
                    stage_4.complete(result=iep_result)
                    self.pipeline_results["iep_result"] = iep_result
                    self.final_output = iep_result
                    
                except Exception as e:
                    stage_4.fail(str(e))
                    raise
            
            # Complete pipeline
            self._complete_pipeline()
            
            return self._generate_pipeline_report()
            
        except Exception as e:
            self._fail_pipeline(str(e))
            raise
    
    async def execute_partial_pipeline(
        self,
        student_id: str,
        start_stage: str,
        end_stage: str,
        input_data: Any = None
    ) -> Dict[str, Any]:
        """Execute a partial pipeline (specific stages only)"""
        
        pipeline_id = self.initialize_pipeline()
        self.overall_status = "running"
        
        logger.info(f"Executing partial pipeline: {start_stage} to {end_stage}")
        
        try:
            if start_stage == "quantification" and end_stage == "rag_generation":
                # Skip to quantification and RAG generation
                stage_3 = self.stages[2]
                stage_3.start()
                
                # Use provided quantified data or generate it
                if input_data:
                    quantified_data = input_data
                    stage_3.complete(result=quantified_data)
                else:
                    raise ValueError("Quantified data required for partial pipeline starting at quantification")
                
                # Execute RAG generation
                stage_4 = self.stages[3]
                stage_4.start()
                
                iep_result = await self.rag_integration.create_rag_enhanced_iep(
                    student_id=student_id,
                    quantified_data=quantified_data
                )
                
                stage_4.complete(result=iep_result)
                self.final_output = iep_result
            
            self._complete_pipeline()
            return self._generate_pipeline_report()
            
        except Exception as e:
            self._fail_pipeline(str(e))
            raise
    
    async def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """Get current status of a pipeline run"""
        
        return {
            "pipeline_id": self.pipeline_id,
            "overall_status": self.overall_status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration": self.total_duration,
            "stages": [stage.to_dict() for stage in self.stages],
            "current_stage": self._get_current_stage(),
            "progress_percentage": self._calculate_progress()
        }
    
    async def validate_pipeline_inputs(
        self,
        student_id: str,
        assessment_documents: List[AssessmentUploadDTO]
    ) -> Dict[str, Any]:
        """Validate inputs before starting pipeline"""
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "student_validated": False,
            "documents_validated": False
        }
        
        # Validate student exists
        try:
            # Would check database for student
            validation_results["student_validated"] = True
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Student validation failed: {e}")
        
        # Validate documents
        for i, doc in enumerate(assessment_documents):
            if not Path(doc.file_path).exists():
                validation_results["valid"] = False
                validation_results["errors"].append(f"Document {i+1} file not found: {doc.file_path}")
            
            if not doc.assessment_type:
                validation_results["warnings"].append(f"Document {i+1} missing assessment type")
        
        if len(assessment_documents) == 0:
            validation_results["valid"] = False
            validation_results["errors"].append("No assessment documents provided")
        
        validation_results["documents_validated"] = len(validation_results["errors"]) == 0
        
        return validation_results
    
    async def _extract_scores_from_data(self, extracted_data: ExtractedDataDTO) -> List[Dict[str, Any]]:
        """Extract individual test scores from extracted data"""
        
        # Parse the structured data and extract individual scores
        # Implementation depends on the structure of ExtractedDataDTO
        scores = []
        
        if hasattr(extracted_data, 'structured_data') and extracted_data.structured_data:
            # Extract scores from structured data
            for test_data in extracted_data.structured_data.get('tests', []):
                for subtest in test_data.get('subtests', []):
                    scores.append({
                        "test_name": test_data.get('name', 'Unknown'),
                        "subtest_name": subtest.get('name', 'Unknown'),
                        "standard_score": subtest.get('standard_score'),
                        "percentile_rank": subtest.get('percentile_rank'),
                        "confidence_interval": subtest.get('confidence_interval')
                    })
        
        return scores
    
    def _complete_pipeline(self):
        """Mark pipeline as completed"""
        self.overall_status = "completed"
        self.end_time = datetime.utcnow()
        self.total_duration = (self.end_time - self.start_time).total_seconds()
        logger.info(f"Pipeline {self.pipeline_id} completed in {self.total_duration:.2f}s")
    
    def _fail_pipeline(self, error: str):
        """Mark pipeline as failed"""
        self.overall_status = "failed"
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.total_duration = (self.end_time - self.start_time).total_seconds()
        logger.error(f"Pipeline {self.pipeline_id} failed: {error}")
    
    def _get_current_stage(self) -> Optional[str]:
        """Get the name of the currently running stage"""
        for stage in self.stages:
            if stage.status == "running":
                return stage.name
        return None
    
    def _calculate_progress(self) -> float:
        """Calculate overall pipeline progress percentage"""
        if not self.stages:
            return 0.0
        
        completed = sum(1 for stage in self.stages if stage.status == "completed")
        return (completed / len(self.stages)) * 100
    
    def _generate_pipeline_report(self) -> Dict[str, Any]:
        """Generate comprehensive pipeline execution report"""
        
        return {
            "pipeline_id": self.pipeline_id,
            "overall_status": self.overall_status,
            "execution_summary": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "total_duration_seconds": self.total_duration,
                "stages_completed": sum(1 for s in self.stages if s.status == "completed"),
                "stages_failed": sum(1 for s in self.stages if s.status == "failed"),
                "overall_confidence": self._calculate_overall_confidence()
            },
            "stage_details": [stage.to_dict() for stage in self.stages],
            "results": {
                "extracted_data_count": len(self.pipeline_results.get("extracted_data", [])),
                "psychoed_scores_count": len(self.pipeline_results.get("psychoed_scores", [])),
                "quantified_data_available": "quantified_data" in self.pipeline_results,
                "iep_generated": "iep_result" in self.pipeline_results
            },
            "final_output": self.final_output,
            "performance_metrics": self._calculate_performance_metrics(),
            "recommendations": self._generate_recommendations()
        }
    
    def _calculate_overall_confidence(self) -> float:
        """Calculate overall pipeline confidence score"""
        confidences = [s.confidence_score for s in self.stages if s.confidence_score]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics for the pipeline run"""
        
        return {
            "total_processing_time": self.total_duration,
            "average_stage_time": self.total_duration / len(self.stages) if self.stages else 0,
            "fastest_stage": min(self.stages, key=lambda s: s.duration or float('inf')).name if self.stages else None,
            "slowest_stage": max(self.stages, key=lambda s: s.duration or 0).name if self.stages else None,
            "success_rate": (sum(1 for s in self.stages if s.status == "completed") / len(self.stages)) * 100 if self.stages else 0
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on pipeline execution"""
        
        recommendations = []
        
        # Performance recommendations
        if self.total_duration and self.total_duration > 300:  # 5 minutes
            recommendations.append("Consider optimizing document processing for faster pipeline execution")
        
        # Confidence recommendations
        overall_confidence = self._calculate_overall_confidence()
        if overall_confidence < 0.8:
            recommendations.append("Low confidence scores detected - review document quality and processing parameters")
        
        # Stage-specific recommendations
        for stage in self.stages:
            if stage.status == "failed":
                recommendations.append(f"Address failures in {stage.name} stage before reprocessing")
            elif stage.confidence_score and stage.confidence_score < 0.7:
                recommendations.append(f"Review {stage.name} stage configuration for improved accuracy")
        
        return recommendations