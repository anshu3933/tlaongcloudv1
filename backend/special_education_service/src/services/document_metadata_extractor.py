"""
Document Metadata Extractor Service
===================================

Comprehensive service for extracting, classifying, and enriching document metadata
for the RAG pipeline enhancement. Implements intelligent content analysis and
quality assessment for educational documents.

Created: 2025-07-16
Task: TASK-002 - Document Metadata Extractor
Dependencies: TASK-001 (Enhanced Metadata Schemas)
"""

import os
import hashlib
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import mimetypes
import asyncio
from collections import Counter

from ..schemas.rag_metadata_schemas import (
    DocumentType, AssessmentType, DocumentLevelMetadata, 
    QualityMetrics, TemporalMetadata, SemanticMetadata
)


logger = logging.getLogger(__name__)


class DocumentMetadataExtractor:
    """
    Comprehensive document metadata extraction service
    
    Analyzes educational documents to extract:
    - File system metadata
    - Document classification 
    - Assessment type identification
    - Quality metrics
    - Temporal information
    - Educational context
    """
    
    def __init__(self):
        """Initialize the metadata extractor with pattern libraries"""
        
        # Document type patterns
        self.document_patterns = {
            DocumentType.IEP: [
                r'individualized.?education.?program',
                r'\biep\b',
                r'annual.?goals',
                r'present.?levels?.?performance',
                r'transition.?services'
            ],
            DocumentType.ASSESSMENT_REPORT: [
                r'assessment.?report',
                r'evaluation.?report', 
                r'psychoeducational.?evaluation',
                r'cognitive.?assessment',
                r'achievement.?test'
            ],
            DocumentType.PROGRESS_REPORT: [
                r'progress.?report',
                r'quarterly.?report',
                r'progress.?monitoring',
                r'goal.?progress'
            ],
            DocumentType.BEHAVIORAL_ASSESSMENT: [
                r'behavioral.?assessment',
                r'functional.?behavior.?assessment',
                r'\bfba\b',
                r'behavior.?intervention.?plan',
                r'\bbip\b'
            ],
            DocumentType.SPEECH_LANGUAGE_EVAL: [
                r'speech.?language.?evaluation',
                r'speech.?therapy.?evaluation',
                r'language.?assessment',
                r'articulation.?assessment'
            ]
        }
        
        # Assessment type patterns
        self.assessment_patterns = {
            AssessmentType.WISC_V: [
                r'wisc.?v\b',
                r'wechsler.?intelligence.?scale.?children.?fifth',
                r'wisc.?5'
            ],
            AssessmentType.WIAT_IV: [
                r'wiat.?iv\b',
                r'wechsler.?individual.?achievement.?test.?fourth',
                r'wiat.?4'
            ],
            AssessmentType.WJ_IV: [
                r'wj.?iv\b',
                r'woodcock.?johnson.?iv',
                r'woodcock.?johnson.?fourth'
            ],
            AssessmentType.BASC_3: [
                r'basc.?3\b',
                r'behavior.?assessment.?system.?children.?third',
                r'basc.?iii'
            ],
            AssessmentType.CONNERS_3: [
                r'conners.?3\b',
                r'conners.?third.?edition',
                r'conners.?iii'
            ]
        }
        
        # Quality indicators
        self.quality_indicators = {
            'high_quality': [
                r'standard.?scores?',
                r'percentile.?ranks?',
                r'confidence.?intervals?',
                r'normative.?data',
                r'reliability.?coefficient'
            ],
            'medium_quality': [
                r'raw.?scores?',
                r'age.?equivalents?',
                r'grade.?equivalents?',
                r'scaled.?scores?'
            ],
            'structure_indicators': [
                r'table.?of.?contents',
                r'summary.?of.?findings',
                r'recommendations',
                r'conclusions'
            ]
        }
        
        # Educational domain keywords
        self.domain_keywords = {
            'reading': [
                'reading', 'phonics', 'decoding', 'fluency', 'comprehension',
                'phonological', 'sight words', 'vocabulary'
            ],
            'writing': [
                'writing', 'composition', 'spelling', 'handwriting', 'grammar',
                'sentence structure', 'paragraph'
            ],
            'math': [
                'mathematics', 'arithmetic', 'calculation', 'problem solving',
                'number sense', 'geometry', 'algebra'
            ],
            'behavior': [
                'behavior', 'attention', 'hyperactivity', 'impulsivity',
                'social skills', 'emotional regulation', 'conduct'
            ],
            'communication': [
                'speech', 'language', 'articulation', 'fluency', 'voice',
                'pragmatics', 'expressive', 'receptive'
            ],
            'adaptive': [
                'adaptive behavior', 'daily living', 'self-care', 'independence',
                'social skills', 'community skills'
            ]
        }

    async def extract_document_metadata(
        self, 
        file_path: str, 
        content: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> DocumentLevelMetadata:
        """
        Extract comprehensive metadata from a document
        
        Args:
            file_path: Path to the source document
            content: Extracted text content
            additional_context: Optional additional context information
            
        Returns:
            DocumentLevelMetadata: Comprehensive document metadata
        """
        logger.info(f"🔍 Starting metadata extraction for: {file_path}")
        
        try:
            # Extract file system metadata
            file_metadata = await self._extract_file_metadata(file_path)
            logger.debug(f"📁 File metadata extracted: {file_metadata}")
            
            # Classify document type and subtype
            doc_classification = await self._classify_document(content)
            logger.debug(f"📋 Document classification: {doc_classification}")
            
            # Extract temporal information
            temporal_info = await self._extract_temporal_metadata(content, file_metadata)
            logger.debug(f"⏰ Temporal metadata: {temporal_info}")
            
            # Assess content quality
            quality_metrics = await self._assess_content_quality(content)
            logger.debug(f"⭐ Quality metrics: {quality_metrics}")
            
            # Extract educational context
            educational_context = await self._extract_educational_context(content)
            logger.debug(f"🎓 Educational context: {educational_context}")
            
            # Combine all metadata
            document_metadata = DocumentLevelMetadata(
                # Identity fields
                document_id=self._generate_document_id(file_path, content),
                document_hash=self._calculate_content_hash(content),
                source_path=file_path,
                filename=Path(file_path).name,
                
                # Classification
                document_type=doc_classification['document_type'],
                document_subtype=doc_classification.get('document_subtype'),
                assessment_type=doc_classification.get('assessment_type'),
                language=self._detect_language(content),
                
                # File metadata
                file_size_bytes=file_metadata['size'],
                page_count=self._estimate_page_count(content),
                word_count=len(content.split()),
                
                # Temporal information
                temporal_metadata=temporal_info,
                
                # Quality assessment
                quality_metrics=quality_metrics,
                
                # Processing metadata
                total_chunks=0,  # Will be updated when chunking
                processing_version="1.0",
                extraction_method="enhanced_extractor_v1",
                
                # Educational context
                student_identifiers=educational_context.get('student_ids', []),
                assessor_information=educational_context.get('assessor_info', {}),
                school_context=educational_context.get('school_context', {})
            )
            
            logger.info(f"✅ Metadata extraction completed for: {file_path}")
            logger.info(f"📊 Document type: {document_metadata.document_type}")
            logger.info(f"📈 Quality score: {quality_metrics.overall_quality:.3f}")
            
            return document_metadata
            
        except Exception as e:
            logger.error(f"❌ Metadata extraction failed for {file_path}: {e}")
            raise

    async def _extract_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract file system metadata"""
        
        try:
            stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'mime_type': mime_type or 'unknown',
                'extension': Path(file_path).suffix.lower()
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Could not extract file metadata: {e}")
            return {
                'size': 0,
                'created': datetime.now(),
                'modified': datetime.now(),
                'mime_type': 'unknown',
                'extension': ''
            }

    async def _classify_document(self, content: str) -> Dict[str, Any]:
        """Classify document type and assessment type"""
        
        content_lower = content.lower()
        
        # Score document types
        doc_type_scores = {}
        for doc_type, patterns in self.document_patterns.items():
            score = sum(
                len(re.findall(pattern, content_lower, re.IGNORECASE))
                for pattern in patterns
            )
            if score > 0:
                doc_type_scores[doc_type] = score
        
        # Determine primary document type
        if doc_type_scores:
            primary_type = max(doc_type_scores, key=doc_type_scores.get)
            logger.debug(f"📋 Document type scores: {doc_type_scores}")
        else:
            primary_type = DocumentType.OTHER
            logger.debug("📋 No document type patterns matched, defaulting to OTHER")
        
        # Score assessment types
        assessment_type = None
        assessment_scores = {}
        for assess_type, patterns in self.assessment_patterns.items():
            score = sum(
                len(re.findall(pattern, content_lower, re.IGNORECASE))
                for pattern in patterns
            )
            if score > 0:
                assessment_scores[assess_type] = score
        
        if assessment_scores:
            assessment_type = max(assessment_scores, key=assessment_scores.get)
            logger.debug(f"🧪 Assessment type scores: {assessment_scores}")
        
        # Extract document subtype
        subtype = None
        if primary_type == DocumentType.ASSESSMENT_REPORT and assessment_type:
            subtype = f"{assessment_type.value}_report"
        
        return {
            'document_type': primary_type,
            'document_subtype': subtype,
            'assessment_type': assessment_type,
            'classification_confidence': max(doc_type_scores.values()) if doc_type_scores else 0.1
        }

    async def _extract_temporal_metadata(
        self, 
        content: str, 
        file_metadata: Dict[str, Any]
    ) -> TemporalMetadata:
        """Extract temporal information from content and file metadata"""
        
        # Date pattern matching
        date_patterns = [
            r'(?:date[:\s]*)?(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'(?:date[:\s]*)?(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(?:administered[:\s]+)?(\w+ \d{1,2}, \d{4})',
            r'(?:evaluation date[:\s]*)?(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
        ]
        
        extracted_dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            extracted_dates.extend(matches)
        
        # Parse dates
        document_date = None
        assessment_date = None
        
        if extracted_dates:
            # Simple heuristic: first date is often document/assessment date
            try:
                first_date_str = extracted_dates[0]
                document_date = self._parse_date_string(first_date_str)
                assessment_date = document_date  # Often the same
                logger.debug(f"📅 Extracted dates: {extracted_dates}")
            except Exception as e:
                logger.warning(f"⚠️ Could not parse date '{first_date_str}': {e}")
        
        # Extract school year
        school_year = None
        year_match = re.search(r'(\d{4})-(\d{4})', content)
        if year_match:
            school_year = f"{year_match.group(1)}-{year_match.group(2)}"
        
        return TemporalMetadata(
            document_date=document_date,
            assessment_date=assessment_date,
            processing_date=datetime.now(),
            last_modified=file_metadata['modified'],
            school_year=school_year,
            temporal_sequence=None  # Will be determined later during processing
        )

    async def _assess_content_quality(self, content: str) -> QualityMetrics:
        """Assess the quality of document content"""
        
        content_lower = content.lower()
        
        # Extraction confidence (based on text characteristics)
        extraction_confidence = self._calculate_extraction_confidence(content)
        
        # Information density (based on educational content indicators)
        information_density = self._calculate_information_density(content_lower)
        
        # Readability score (simple heuristic)
        readability_score = self._calculate_readability_score(content)
        
        # Completeness score (based on structure indicators)
        completeness_score = self._calculate_completeness_score(content_lower)
        
        # Overall quality (weighted average)
        overall_quality = (
            extraction_confidence * 0.3 +
            information_density * 0.3 +
            readability_score * 0.2 +
            completeness_score * 0.2
        )
        
        logger.debug(f"📊 Quality assessment - Extraction: {extraction_confidence:.3f}, "
                    f"Density: {information_density:.3f}, "
                    f"Readability: {readability_score:.3f}, "
                    f"Completeness: {completeness_score:.3f}")
        
        return QualityMetrics(
            extraction_confidence=extraction_confidence,
            information_density=information_density,
            readability_score=readability_score,
            completeness_score=completeness_score,
            validation_status="unvalidated",  # Will be updated by validation service
            overall_quality=overall_quality
        )

    def _calculate_extraction_confidence(self, content: str) -> float:
        """Calculate confidence in text extraction quality"""
        
        # Factors that increase confidence
        confidence_score = 0.5  # Base score
        
        # Check for complete sentences
        sentence_endings = len(re.findall(r'[.!?]\s+[A-Z]', content))
        if sentence_endings > 10:
            confidence_score += 0.2
        
        # Check for proper capitalization
        capital_ratio = len(re.findall(r'[A-Z]', content)) / max(len(content), 1)
        if 0.02 <= capital_ratio <= 0.15:  # Reasonable capital letter ratio
            confidence_score += 0.1
        
        # Check for coherent text (not garbled OCR)
        garbled_patterns = len(re.findall(r'[^a-zA-Z\s]{3,}', content))
        if garbled_patterns < len(content) * 0.01:  # Less than 1% garbled
            confidence_score += 0.2
        
        return min(confidence_score, 1.0)

    def _calculate_information_density(self, content_lower: str) -> float:
        """Calculate density of useful educational information"""
        
        density_score = 0.0
        
        # Count educational keywords
        total_keywords = 0
        for domain, keywords in self.domain_keywords.items():
            domain_count = sum(content_lower.count(keyword.lower()) for keyword in keywords)
            total_keywords += domain_count
        
        # Normalize by content length
        word_count = len(content_lower.split())
        if word_count > 0:
            keyword_density = min(total_keywords / word_count, 0.5)  # Cap at 50%
            density_score = keyword_density * 2  # Scale to 0-1
        
        # Bonus for quality indicators
        quality_indicators_found = 0
        for indicator_type, patterns in self.quality_indicators.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    quality_indicators_found += 1
        
        indicator_bonus = min(quality_indicators_found * 0.1, 0.3)
        density_score += indicator_bonus
        
        return min(density_score, 1.0)

    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score (simplified)"""
        
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # Average sentence length
        total_words = len(content.split())
        avg_sentence_length = total_words / len(sentences)
        
        # Penalize very short or very long sentences
        if 10 <= avg_sentence_length <= 25:
            length_score = 1.0
        elif 5 <= avg_sentence_length <= 35:
            length_score = 0.8
        else:
            length_score = 0.5
        
        # Check for professional language indicators
        professional_indicators = [
            'assessment', 'evaluation', 'student', 'performance',
            'recommendations', 'goals', 'objectives', 'services'
        ]
        
        professional_count = sum(
            content.lower().count(indicator) for indicator in professional_indicators
        )
        
        professional_score = min(professional_count / 20, 1.0)  # Normalize
        
        return (length_score * 0.6 + professional_score * 0.4)

    def _calculate_completeness_score(self, content_lower: str) -> float:
        """Calculate completeness based on structure indicators"""
        
        completeness_score = 0.0
        
        # Check for structural elements
        structure_elements = [
            r'summary',
            r'background',
            r'results',
            r'recommendations',
            r'conclusions',
            r'goals',
            r'objectives'
        ]
        
        elements_found = 0
        for element in structure_elements:
            if re.search(element, content_lower):
                elements_found += 1
        
        structure_score = min(elements_found / len(structure_elements), 1.0)
        completeness_score += structure_score * 0.6
        
        # Check for data completeness (scores, dates, names)
        data_elements = [
            r'\d+(?:\.\d+)?(?:st|nd|rd|th)?\s*percentile',
            r'standard\s+score[:\s]*\d+',
            r'age\s+equivalent[:\s]*\d+',
            r'grade\s+equivalent[:\s]*\d+'
        ]
        
        data_found = sum(
            1 for pattern in data_elements 
            if re.search(pattern, content_lower)
        )
        
        data_score = min(data_found / len(data_elements), 1.0)
        completeness_score += data_score * 0.4
        
        return completeness_score

    async def _extract_educational_context(self, content: str) -> Dict[str, Any]:
        """Extract educational context information"""
        
        context = {
            'student_ids': [],
            'assessor_info': {},
            'school_context': {}
        }
        
        # Extract potential student identifiers (simplified)
        student_patterns = [
            r'student\s+(?:id[:\s]*)?(\w+)',
            r'name[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
        ]
        
        for pattern in student_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            context['student_ids'].extend(matches[:3])  # Limit to first 3 matches
        
        # Extract assessor information
        assessor_patterns = [
            r'assessed\s+by[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'examiner[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'psychologist[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)'
        ]
        
        for pattern in assessor_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                context['assessor_info']['name'] = match.group(1)
                break
        
        # Extract school context
        school_patterns = [
            r'school[:\s]+([A-Z][a-z\s]+ (?:Elementary|Middle|High) School)',
            r'district[:\s]+([A-Z][a-z\s]+ (?:School )?District)',
        ]
        
        for pattern in school_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                if 'school' in pattern.lower():
                    context['school_context']['school_name'] = match.group(1)
                else:
                    context['school_context']['district_name'] = match.group(1)
        
        return context

    def _generate_document_id(self, file_path: str, content: str) -> str:
        """Generate unique document ID"""
        
        # Combine file path and content hash for uniqueness
        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d")
        
        return f"doc_{timestamp}_{path_hash}_{content_hash}"

    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for deduplication"""
        
        return hashlib.sha256(content.encode()).hexdigest()

    def _detect_language(self, content: str) -> str:
        """Simple language detection (placeholder for more sophisticated detection)"""
        
        # Simple heuristic: check for common English educational terms
        english_indicators = [
            'assessment', 'evaluation', 'student', 'grade', 'score',
            'percentile', 'standard', 'the', 'and', 'of', 'to', 'in'
        ]
        
        content_lower = content.lower()
        english_count = sum(
            content_lower.count(indicator) for indicator in english_indicators
        )
        
        return "en" if english_count > 10 else "unknown"

    def _estimate_page_count(self, content: str) -> Optional[int]:
        """Estimate page count based on content length"""
        
        # Rough estimate: 250-300 words per page
        word_count = len(content.split())
        if word_count > 0:
            return max(1, round(word_count / 275))
        return None

    def _parse_date_string(self, date_str: str) -> datetime:
        """Parse various date formats"""
        
        # Common date formats
        formats = [
            "%m/%d/%Y",
            "%m-%d-%Y", 
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%B %d, %Y",
            "%b %d, %Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Could not parse date: {date_str}")


# Example usage and testing
async def test_metadata_extractor():
    """Test the metadata extractor with sample content"""
    
    extractor = DocumentMetadataExtractor()
    
    sample_content = """
    WISC-V Cognitive Assessment Report
    
    Student: John Doe
    Date of Assessment: 03/15/2024
    Assessed by: Dr. Smith, School Psychologist
    School: Lincoln Elementary School
    
    SUMMARY OF FINDINGS:
    
    The WISC-V assessment revealed the following standard scores:
    - Verbal Comprehension Index: 95 (37th percentile)
    - Visual Spatial Index: 110 (75th percentile)
    - Fluid Reasoning Index: 88 (21st percentile)
    - Working Memory Index: 92 (30th percentile)
    - Processing Speed Index: 85 (16th percentile)
    
    RECOMMENDATIONS:
    
    1. Provide additional time for processing complex information
    2. Use visual supports to enhance comprehension
    3. Break tasks into smaller, manageable components
    """
    
    metadata = await extractor.extract_document_metadata(
        file_path="/test/sample_wisc_report.pdf",
        content=sample_content
    )
    
    logger.info(f"🧪 Test extraction completed")
    logger.info(f"📋 Document type: {metadata.document_type}")
    logger.info(f"🧪 Assessment type: {metadata.assessment_type}")
    logger.info(f"📊 Quality score: {metadata.quality_metrics.overall_quality:.3f}")
    
    return metadata


if __name__ == "__main__":
    # Run test if script is executed directly
    import asyncio
    asyncio.run(test_metadata_extractor())