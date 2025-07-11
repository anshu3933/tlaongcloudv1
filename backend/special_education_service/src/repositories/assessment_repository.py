"""Assessment data repository for database operations"""
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc
from sqlalchemy.orm import selectinload
from datetime import datetime

from ..models.special_education_models import (
    AssessmentDocument, PsychoedScore, ExtractedAssessmentData, 
    QuantifiedAssessmentData, Student
)

logger = logging.getLogger(__name__)

class AssessmentRepository:
    """Repository for assessment data operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Assessment Document operations
    async def create_assessment_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new assessment document"""
        try:
            # Convert string IDs to UUIDs if needed
            if isinstance(document_data.get("student_id"), str):
                document_data["student_id"] = UUID(document_data["student_id"])
            
            assessment_doc = AssessmentDocument(**document_data)
            self.db.add(assessment_doc)
            await self.db.commit()
            await self.db.refresh(assessment_doc)
            
            return self._assessment_document_to_dict(assessment_doc)
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating assessment document: {e}")
            raise
    
    async def get_assessment_document(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get assessment document by ID"""
        try:
            stmt = select(AssessmentDocument).where(AssessmentDocument.id == document_id)
            result = await self.db.execute(stmt)
            document = result.scalar_one_or_none()
            
            if document:
                return self._assessment_document_to_dict(document)
            return None
        except Exception as e:
            logger.error(f"Error getting assessment document {document_id}: {e}")
            raise
    
    async def update_assessment_document(
        self, 
        document_id: UUID, 
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update assessment document"""
        try:
            stmt = (
                update(AssessmentDocument)
                .where(AssessmentDocument.id == document_id)
                .values(**updates)
                .returning(AssessmentDocument)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            updated_document = result.scalar_one_or_none()
            if updated_document:
                return self._assessment_document_to_dict(updated_document)
            return None
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating assessment document {document_id}: {e}")
            raise
    
    async def get_student_assessment_documents(self, student_id: UUID) -> List[Dict[str, Any]]:
        """Get all assessment documents for a student"""
        try:
            stmt = (
                select(AssessmentDocument)
                .where(AssessmentDocument.student_id == student_id)
                .order_by(desc(AssessmentDocument.assessment_date))
            )
            result = await self.db.execute(stmt)
            documents = result.scalars().all()
            
            return [self._assessment_document_to_dict(doc) for doc in documents]
        except Exception as e:
            logger.error(f"Error getting student assessment documents for {student_id}: {e}")
            raise
    
    # Psychoeducational Score operations
    async def create_psychoed_scores_batch(self, scores_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create multiple psychoeducational scores"""
        try:
            created_scores = []
            for score_data in scores_data:
                # Convert string IDs to UUIDs if needed
                if isinstance(score_data.get("document_id"), str):
                    score_data["document_id"] = UUID(score_data["document_id"])
                
                score = PsychoedScore(**score_data)
                self.db.add(score)
                created_scores.append(score)
            
            await self.db.commit()
            
            # Refresh all created scores
            for score in created_scores:
                await self.db.refresh(score)
            
            return [self._psychoed_score_to_dict(score) for score in created_scores]
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating psychoed scores batch: {e}")
            raise
    
    async def get_document_psychoed_scores(self, document_id: UUID) -> List[Dict[str, Any]]:
        """Get all psychoeducational scores for a document"""
        try:
            stmt = (
                select(PsychoedScore)
                .where(PsychoedScore.document_id == document_id)
                .order_by(PsychoedScore.test_name, PsychoedScore.subtest_name)
            )
            result = await self.db.execute(stmt)
            scores = result.scalars().all()
            
            return [self._psychoed_score_to_dict(score) for score in scores]
        except Exception as e:
            logger.error(f"Error getting document psychoed scores for {document_id}: {e}")
            raise
    
    async def get_student_psychoed_scores(
        self, 
        student_id: UUID, 
        test_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get psychoeducational scores for a student"""
        try:
            # Join with AssessmentDocument to filter by student
            stmt = (
                select(PsychoedScore)
                .join(AssessmentDocument, PsychoedScore.document_id == AssessmentDocument.id)
                .where(AssessmentDocument.student_id == student_id)
            )
            
            if test_name:
                stmt = stmt.where(PsychoedScore.test_name == test_name)
            
            stmt = stmt.order_by(PsychoedScore.test_name, PsychoedScore.subtest_name)
            
            result = await self.db.execute(stmt)
            scores = result.scalars().all()
            
            return [self._psychoed_score_to_dict(score) for score in scores]
        except Exception as e:
            logger.error(f"Error getting student psychoed scores for {student_id}: {e}")
            raise
    
    # Extracted Assessment Data operations
    async def create_extracted_assessment_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create extracted assessment data record"""
        try:
            if isinstance(extracted_data.get("document_id"), str):
                extracted_data["document_id"] = UUID(extracted_data["document_id"])
            
            extracted = ExtractedAssessmentData(**extracted_data)
            self.db.add(extracted)
            await self.db.commit()
            await self.db.refresh(extracted)
            
            return self._extracted_assessment_data_to_dict(extracted)
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating extracted assessment data: {e}")
            raise
    
    async def get_document_extracted_data(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get extracted data for a document"""
        try:
            stmt = select(ExtractedAssessmentData).where(
                ExtractedAssessmentData.document_id == document_id
            )
            result = await self.db.execute(stmt)
            extracted_data = result.scalar_one_or_none()
            
            if extracted_data:
                return self._extracted_assessment_data_to_dict(extracted_data)
            return None
        except Exception as e:
            logger.error(f"Error getting extracted data for document {document_id}: {e}")
            raise
    
    # Quantified Assessment Data operations
    async def create_quantified_assessment_data(self, quantified_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create quantified assessment data record"""
        try:
            if isinstance(quantified_data.get("student_id"), str):
                quantified_data["student_id"] = UUID(quantified_data["student_id"])
            
            quantified = QuantifiedAssessmentData(**quantified_data)
            self.db.add(quantified)
            await self.db.commit()
            await self.db.refresh(quantified)
            
            return self._quantified_assessment_data_to_dict(quantified)
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating quantified assessment data: {e}")
            raise
    
    async def get_student_quantified_data(self, student_id: UUID) -> List[Dict[str, Any]]:
        """Get all quantified assessment data for a student"""
        try:
            stmt = (
                select(QuantifiedAssessmentData)
                .where(QuantifiedAssessmentData.student_id == student_id)
                .order_by(desc(QuantifiedAssessmentData.assessment_date))
            )
            result = await self.db.execute(stmt)
            quantified_data = result.scalars().all()
            
            return [self._quantified_assessment_data_to_dict(data) for data in quantified_data]
        except Exception as e:
            logger.error(f"Error getting student quantified data for {student_id}: {e}")
            raise
    
    async def get_quantified_assessment_data(self, data_id: UUID) -> Optional[Dict[str, Any]]:
        """Get quantified assessment data by ID"""
        try:
            stmt = select(QuantifiedAssessmentData).where(QuantifiedAssessmentData.id == data_id)
            result = await self.db.execute(stmt)
            quantified_data = result.scalar_one_or_none()
            
            if quantified_data:
                return self._quantified_assessment_data_to_dict(quantified_data)
            return None
        except Exception as e:
            logger.error(f"Error getting quantified assessment data {data_id}: {e}")
            raise
    
    # Helper methods for converting models to dictionaries
    def _assessment_document_to_dict(self, document: AssessmentDocument) -> Dict[str, Any]:
        """Convert AssessmentDocument model to dictionary"""
        return {
            "id": str(document.id),
            "student_id": str(document.student_id),
            "document_type": document.document_type.value if hasattr(document.document_type, 'value') else str(document.document_type),
            "file_path": document.file_path,
            "file_name": document.file_name,
            "gcs_path": document.gcs_path,
            "upload_date": document.upload_date,
            "processing_status": document.processing_status,
            "assessment_date": document.assessment_date,
            "assessor_name": document.assessor_name,
            "assessor_title": document.assessor_title,
            "assessment_location": document.assessment_location,
            "extraction_confidence": document.extraction_confidence,
            "processing_duration": document.processing_duration,
            "error_message": document.error_message,
            "created_at": document.created_at,
            "updated_at": document.updated_at
        }
    
    def _psychoed_score_to_dict(self, score: PsychoedScore) -> Dict[str, Any]:
        """Convert PsychoedScore model to dictionary"""
        return {
            "id": str(score.id),
            "document_id": str(score.document_id),
            "test_name": score.test_name,
            "subtest_name": score.subtest_name,
            "score_type": score.score_type,
            "raw_score": score.raw_score,
            "standard_score": score.standard_score,
            "percentile_rank": score.percentile_rank,
            "scaled_score": score.scaled_score,
            "grade_equivalent": score.grade_equivalent,
            "age_equivalent": score.age_equivalent,
            "confidence_interval_lower": score.confidence_interval_lower,
            "confidence_interval_upper": score.confidence_interval_upper,
            "confidence_level": score.confidence_level,
            "extraction_confidence": score.extraction_confidence,
            "normative_sample": score.normative_sample,
            "test_date": score.test_date,
            "basal_score": score.basal_score,
            "ceiling_score": score.ceiling_score,
            "created_at": score.created_at
        }
    
    def _extracted_assessment_data_to_dict(self, extracted: ExtractedAssessmentData) -> Dict[str, Any]:
        """Convert ExtractedAssessmentData model to dictionary"""
        return {
            "id": str(extracted.id),
            "document_id": str(extracted.document_id),
            "raw_text": extracted.raw_text,
            "structured_data": extracted.structured_data,
            "extraction_method": extracted.extraction_method,
            "extraction_confidence": extracted.extraction_confidence,
            "completeness_score": extracted.completeness_score,
            "pages_processed": extracted.pages_processed,
            "total_pages": extracted.total_pages,
            "processing_errors": extracted.processing_errors,
            "created_at": extracted.created_at
        }
    
    def _quantified_assessment_data_to_dict(self, quantified: QuantifiedAssessmentData) -> Dict[str, Any]:
        """Convert QuantifiedAssessmentData model to dictionary"""
        return {
            "id": str(quantified.id),
            "student_id": str(quantified.student_id),
            "assessment_date": quantified.assessment_date,
            "cognitive_composite": quantified.cognitive_composite,
            "academic_composite": quantified.academic_composite,
            "behavioral_composite": quantified.behavioral_composite,
            "social_emotional_composite": quantified.social_emotional_composite,
            "adaptive_composite": quantified.adaptive_composite,
            "executive_composite": quantified.executive_composite,
            "reading_composite": quantified.reading_composite,
            "math_composite": quantified.math_composite,
            "writing_composite": quantified.writing_composite,
            "language_composite": quantified.language_composite,
            "standardized_plop": quantified.standardized_plop,
            "growth_rate": quantified.growth_rate,
            "progress_indicators": quantified.progress_indicators,
            "learning_style_profile": quantified.learning_style_profile,
            "cognitive_processing_profile": quantified.cognitive_processing_profile,
            "priority_goals": quantified.priority_goals,
            "service_recommendations": quantified.service_recommendations,
            "accommodation_recommendations": quantified.accommodation_recommendations,
            "eligibility_category": quantified.eligibility_category,
            "primary_disability": quantified.primary_disability,
            "secondary_disabilities": quantified.secondary_disabilities,
            "confidence_metrics": quantified.confidence_metrics,
            "source_documents": quantified.source_documents,
            "created_at": quantified.created_at,
            "updated_at": quantified.updated_at
        }