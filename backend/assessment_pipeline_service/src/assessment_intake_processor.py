"""
Stage 1: Assessment document intake and processing
"""
import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np
from pathlib import Path

from google.cloud import documentai_v1 as documentai
from google.cloud import storage
import httpx

from assessment_pipeline_service.models.assessment_models import AssessmentType, PsychoedScore
from assessment_pipeline_service.schemas.assessment_schemas import PsychoedScoreDTO, ExtractedDataDTO

logger = logging.getLogger(__name__)

class AssessmentIntakeProcessor:
    """Process and extract data from assessment documents"""
    
    def __init__(self, project_id: str = None, location: str = "us"):
        import os
        
        # Use environment variables if not provided
        self.project_id = project_id or os.getenv("DOCUMENT_AI_PROJECT_ID", "518395328285")
        self.location = location or os.getenv("DOCUMENT_AI_LOCATION", "us")
        self.processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID", "8ea662491b6ff80d")
        
        self.client = documentai.DocumentProcessorServiceClient()
        
        # Main processor for psychoeducational assessments
        self.processor_name = f"projects/{self.project_id}/locations/{self.location}/processors/{self.processor_id}"
        
        # Score extraction patterns
        self.score_patterns = {
            "standard_score": [
                r"(?:SS|Standard Score)[:\s]*(\d{2,3})",
                r"(?:Standard)[:\s]*(\d{2,3})",
                r"(?:SS)[:\s]*=?[:\s]*(\d{2,3})"
            ],
            "percentile": [
                r"(?:Percentile|%ile)[:\s]*(\d{1,2})",
                r"(\d{1,2})(?:th|st|nd|rd)?\s*(?:percentile|%ile)",
                r"(?:PR)[:\s]*(\d{1,2})"
            ],
            "scaled_score": [
                r"(?:Scaled Score)[:\s]*(\d{1,2})",
                r"(?:Scaled)[:\s]*(\d{1,2})"
            ],
            "t_score": [
                r"(?:T-?Score)[:\s]*(\d{2,3})",
                r"(?:T)[:\s]*(\d{2,3})"
            ]
        }
        
        # Test battery patterns
        self.test_patterns = {
            AssessmentType.WISC_V: {
                "name": "WISC-V",
                "indices": ["VCI", "VSI", "FRI", "WMI", "PSI", "FSIQ", "GAI", "CPI"],
                "subtests": [
                    "Similarities", "Vocabulary", "Information", "Comprehension",
                    "Block Design", "Visual Puzzles", "Matrix Reasoning", "Figure Weights",
                    "Digit Span", "Picture Span", "Letter-Number Sequencing",
                    "Coding", "Symbol Search", "Cancellation"
                ]
            },
            AssessmentType.WIAT_IV: {
                "name": "WIAT-IV",
                "composites": ["Total Achievement", "Reading", "Mathematics", "Written Language"],
                "subtests": [
                    "Word Reading", "Reading Comprehension", "Pseudoword Decoding",
                    "Numerical Operations", "Math Problem Solving", "Math Fluency",
                    "Spelling", "Sentence Composition", "Essay Composition"
                ]
            },
            AssessmentType.BASC_3: {
                "name": "BASC-3",
                "scales": [
                    "Externalizing Problems", "Internalizing Problems", 
                    "Behavioral Symptoms Index", "Adaptive Skills"
                ],
                "subscales": [
                    "Hyperactivity", "Aggression", "Conduct Problems",
                    "Anxiety", "Depression", "Somatization",
                    "Attention Problems", "Learning Problems",
                    "Adaptability", "Social Skills", "Leadership"
                ]
            }
        }
    
    async def process_assessment_document(
        self,
        document_path: str,
        document_metadata: Dict[str, Any]
    ) -> ExtractedDataDTO:
        """Process a single assessment document"""
        
        logger.info(f"Processing assessment document: {document_path}")
        
        # Detect assessment type
        assessment_type = await self._detect_assessment_type(document_path)
        logger.info(f"Detected assessment type: {assessment_type}")
        
        # Process with Document AI
        document = await self._process_with_document_ai(document_path)
        
        # Extract structured data
        extracted_data = {
            "assessment_type": assessment_type,
            "document_metadata": document_metadata,
            "extraction_timestamp": datetime.utcnow()
        }
        
        # Extract scores
        scores = self._extract_all_scores(document, assessment_type)
        extracted_data["scores"] = scores
        
        # Extract cognitive data
        if assessment_type in [AssessmentType.WISC_V, AssessmentType.DAS_II]:
            extracted_data["cognitive_data"] = self._extract_cognitive_data(document, scores, assessment_type)
        
        # Extract academic data
        if assessment_type in [AssessmentType.WIAT_IV, AssessmentType.WJ_IV, AssessmentType.KTEA_3]:
            extracted_data["academic_data"] = self._extract_academic_data(document, scores, assessment_type)
        
        # Extract behavioral data
        if assessment_type in [AssessmentType.BASC_3, AssessmentType.CONNERS_3, AssessmentType.BRIEF_2]:
            extracted_data["behavioral_data"] = self._extract_behavioral_data(document, scores, assessment_type)
        
        # Extract observations and recommendations
        extracted_data["observations"] = self._extract_observations(document)
        extracted_data["recommendations"] = self._extract_recommendations(document)
        
        # Calculate confidence
        confidence = self._calculate_extraction_confidence(extracted_data)
        extracted_data["extraction_confidence"] = confidence
        
        # Convert to DTO
        return self._convert_to_dto(extracted_data)
    
    async def _detect_assessment_type(self, document_path: str) -> AssessmentType:
        """Auto-detect the type of assessment"""
        
        # Quick text extraction for classification
        with open(document_path, 'rb') as f:
            content = f.read()
        
        # Try to extract text (simplified - would use proper extraction)
        text = str(content).lower()
        
        # Check each test pattern
        for assessment_type, pattern_info in self.test_patterns.items():
            test_name = pattern_info["name"].lower()
            if test_name in text:
                return assessment_type
            
            # Check for specific indices/subtests
            matches = sum(1 for item in pattern_info.get("indices", []) + pattern_info.get("subtests", []) 
                         if item.lower() in text)
            if matches >= 3:  # At least 3 matches
                return assessment_type
        
        # Default to observation if no specific test detected
        return AssessmentType.OBSERVATION
    
    async def _process_with_document_ai(self, document_path: str) -> documentai.Document:
        """Process document with Google Document AI"""
        
        # Read document
        with open(document_path, 'rb') as f:
            content = f.read()
        
        # Determine MIME type
        mime_type = self._get_mime_type(document_path)
        
        # Create request
        request = documentai.ProcessRequest(
            name=self.processors["form_parser"],  # Use form parser as default
            raw_document=documentai.RawDocument(
                content=content,
                mime_type=mime_type
            )
        )
        
        # Process document
        result = self.client.process_document(request=request)
        
        return result.document
    
    def _extract_all_scores(
        self, 
        document: documentai.Document, 
        assessment_type: AssessmentType
    ) -> List[PsychoedScoreDTO]:
        """Extract all test scores from document"""
        
        scores = []
        
        # Extract from tables
        for table in document.tables:
            table_scores = self._extract_scores_from_table(table, document, assessment_type)
            scores.extend(table_scores)
        
        # Extract from form fields
        for field in document.form_fields:
            field_score = self._extract_score_from_field(field, document, assessment_type)
            if field_score:
                scores.append(field_score)
        
        # Extract from entities (if using specialized processor)
        for entity in document.entities:
            entity_score = self._extract_score_from_entity(entity, document, assessment_type)
            if entity_score:
                scores.append(entity_score)
        
        # Apply pattern matching on text
        text_scores = self._extract_scores_from_text(document.text, assessment_type)
        scores.extend(text_scores)
        
        # Deduplicate and validate
        scores = self._deduplicate_scores(scores)
        
        return scores
    
    def _extract_scores_from_table(
        self,
        table: documentai.Document.Page.Table,
        document: documentai.Document,
        assessment_type: AssessmentType
    ) -> List[PsychoedScoreDTO]:
        """Extract scores from a table"""
        
        scores = []
        
        # Get table headers
        headers = []
        if table.header_rows:
            for cell in table.header_rows[0].cells:
                headers.append(self._get_text(cell.layout, document))
        
        # Process each row
        for row in table.body_rows:
            row_data = {}
            for i, cell in enumerate(row.cells):
                if i < len(headers):
                    row_data[headers[i]] = self._get_text(cell.layout, document)
            
            # Try to parse as score
            score = self._parse_table_row_as_score(row_data, assessment_type)
            if score:
                scores.append(score)
        
        return scores
    
    def _parse_table_row_as_score(
        self,
        row_data: Dict[str, str],
        assessment_type: AssessmentType
    ) -> Optional[PsychoedScoreDTO]:
        """Parse a table row into a score object"""
        
        # Look for test/subtest name
        test_name = None
        subtest_name = None
        
        for key in ["Test", "Subtest", "Scale", "Index", "Composite"]:
            if key in row_data:
                subtest_name = row_data[key]
                test_name = self.test_patterns.get(assessment_type, {}).get("name", str(assessment_type))
                break
        
        if not subtest_name:
            return None
        
        # Extract scores
        score_data = {
            "test_name": test_name,
            "subtest_name": subtest_name
        }
        
        # Standard score
        for key in ["SS", "Standard Score", "Standard"]:
            if key in row_data:
                try:
                    score_data["standard_score"] = float(row_data[key])
                except:
                    pass
        
        # Percentile
        for key in ["Percentile", "%ile", "PR"]:
            if key in row_data:
                try:
                    score_data["percentile_rank"] = float(row_data[key])
                except:
                    pass
        
        # Scaled score
        for key in ["Scaled Score", "Scaled"]:
            if key in row_data:
                try:
                    score_data["scaled_score"] = float(row_data[key])
                except:
                    pass
        
        # Confidence interval
        for key in ["95% CI", "Confidence Interval", "CI"]:
            if key in row_data:
                ci_match = re.search(r"(\d+)-(\d+)", row_data[key])
                if ci_match:
                    score_data["confidence_interval"] = (
                        float(ci_match.group(1)),
                        float(ci_match.group(2))
                    )
        
        # Descriptors
        for key in ["Descriptor", "Classification", "Range"]:
            if key in row_data:
                score_data["qualitative_descriptor"] = row_data[key]
        
        # Only create score if we have actual score values
        if any(k in score_data for k in ["standard_score", "scaled_score", "percentile_rank", "t_score"]):
            score_data["extraction_confidence"] = 0.85  # High confidence for table data
            return PsychoedScoreDTO(**score_data)
        
        return None
    
    def _extract_scores_from_text(
        self,
        text: str,
        assessment_type: AssessmentType
    ) -> List[PsychoedScoreDTO]:
        """Extract scores using regex patterns"""
        
        scores = []
        test_info = self.test_patterns.get(assessment_type, {})
        test_name = test_info.get("name", str(assessment_type))
        
        # Split text into sections/paragraphs
        sections = text.split('\n\n')
        
        for section in sections:
            # Look for subtest names
            subtest_name = None
            for subtest in test_info.get("subtests", []) + test_info.get("indices", []):
                if subtest.lower() in section.lower():
                    subtest_name = subtest
                    break
            
            if not subtest_name:
                continue
            
            score_data = {
                "test_name": test_name,
                "subtest_name": subtest_name
            }
            
            # Extract scores using patterns
            for score_type, patterns in self.score_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, section, re.IGNORECASE)
                    if match:
                        try:
                            value = float(match.group(1))
                            if score_type == "standard_score":
                                score_data["standard_score"] = value
                            elif score_type == "percentile":
                                score_data["percentile_rank"] = value
                            elif score_type == "scaled_score":
                                score_data["scaled_score"] = value
                            elif score_type == "t_score":
                                score_data["t_score"] = value
                        except:
                            pass
            
            # Only add if we found scores
            if any(k in score_data for k in ["standard_score", "scaled_score", "percentile_rank", "t_score"]):
                score_data["extraction_confidence"] = 0.75  # Lower confidence for regex extraction
                scores.append(PsychoedScoreDTO(**score_data))
        
        return scores
    
    def _extract_cognitive_data(
        self,
        document: documentai.Document,
        scores: List[PsychoedScoreDTO],
        assessment_type: AssessmentType
    ) -> Dict[str, Any]:
        """Extract cognitive assessment data"""
        
        cognitive_data = {
            "indices": {},
            "subtests": {},
            "strengths": [],
            "weaknesses": []
        }
        
        # Group scores by type
        for score in scores:
            if score.test_name == self.test_patterns[assessment_type]["name"]:
                # Check if it's an index score
                if score.subtest_name in self.test_patterns[assessment_type].get("indices", []):
                    cognitive_data["indices"][score.subtest_name] = {
                        "standard_score": score.standard_score,
                        "percentile": score.percentile_rank,
                        "confidence_interval": score.confidence_interval,
                        "descriptor": score.qualitative_descriptor
                    }
                # Otherwise it's a subtest
                else:
                    cognitive_data["subtests"][score.subtest_name] = {
                        "scaled_score": score.scaled_score,
                        "percentile": score.percentile_rank
                    }
        
        # Identify strengths and weaknesses
        cognitive_data["strengths"], cognitive_data["weaknesses"] = self._identify_strengths_weaknesses(
            cognitive_data["indices"]
        )
        
        return cognitive_data
    
    def _identify_strengths_weaknesses(self, indices: Dict[str, Dict]) -> Tuple[List[str], List[str]]:
        """Identify cognitive strengths and weaknesses"""
        
        strengths = []
        weaknesses = []
        
        # Calculate mean of indices
        scores = [idx["standard_score"] for idx in indices.values() if idx.get("standard_score")]
        if not scores:
            return strengths, weaknesses
        
        mean_score = np.mean(scores)
        
        # Identify significant deviations (1 SD = 15 points)
        for index_name, index_data in indices.items():
            score = index_data.get("standard_score")
            if not score:
                continue
            
            if score >= mean_score + 15:  # Strength
                strengths.append(f"{index_name} ({score})")
            elif score <= mean_score - 15:  # Weakness
                weaknesses.append(f"{index_name} ({score})")
        
        return strengths, weaknesses
    
    def _calculate_extraction_confidence(self, extracted_data: Dict) -> float:
        """Calculate overall extraction confidence (76-98% range)"""
        
        confidence_scores = []
        
        # Check completeness of scores
        if extracted_data.get("scores"):
            score_confidence = min(len(extracted_data["scores"]) / 10, 1.0)  # Expect ~10 scores
            confidence_scores.append(score_confidence)
        
        # Check presence of key data
        if extracted_data.get("cognitive_data", {}).get("indices"):
            confidence_scores.append(0.9)
        
        if extracted_data.get("recommendations"):
            confidence_scores.append(0.85)
        
        # Calculate weighted average
        if confidence_scores:
            raw_confidence = np.mean(confidence_scores)
            # Map to 76-98% range
            mapped_confidence = 76 + (raw_confidence * 22)
            return mapped_confidence / 100
        
        return 0.76  # Minimum confidence
    
    def _convert_to_dto(self, extracted_data: Dict) -> ExtractedDataDTO:
        """Convert extracted data to DTO"""
        
        # Prepare cognitive scores
        cognitive_scores = []
        if "scores" in extracted_data:
            for score in extracted_data["scores"]:
                if isinstance(score, PsychoedScoreDTO):
                    cognitive_scores.append(score)
        
        # Prepare present levels
        present_levels = {}
        if extracted_data.get("cognitive_data"):
            present_levels["cognitive"] = extracted_data["cognitive_data"]
        if extracted_data.get("academic_data"):
            present_levels["academic"] = extracted_data["academic_data"]
        if extracted_data.get("behavioral_data"):
            present_levels["behavioral"] = extracted_data["behavioral_data"]
        
        return ExtractedDataDTO(
            document_id=extracted_data.get("document_id", "temp-id"),
            extraction_date=extracted_data.get("extraction_timestamp", datetime.utcnow()),
            cognitive_scores=cognitive_scores,
            cognitive_indices=extracted_data.get("cognitive_data", {}).get("indices", {}),
            present_levels=present_levels,
            strengths=extracted_data.get("cognitive_data", {}).get("strengths", []),
            needs=extracted_data.get("cognitive_data", {}).get("weaknesses", []),
            recommendations=extracted_data.get("recommendations", []),
            extraction_confidence=extracted_data.get("extraction_confidence", 0.76),
            completeness_score=self._calculate_completeness(extracted_data),
            manual_review_required=extracted_data.get("extraction_confidence", 0) < 0.80
        )
    
    def _calculate_completeness(self, data: Dict) -> float:
        """Calculate how complete the extraction is"""
        
        required_fields = [
            "scores", "cognitive_data", "observations", "recommendations"
        ]
        
        present_fields = sum(1 for field in required_fields if data.get(field))
        
        return present_fields / len(required_fields)
    
    def _get_text(self, layout: documentai.Document.Page.Layout, document: documentai.Document) -> str:
        """Extract text from layout element"""
        
        text = ""
        if layout.text_anchor and layout.text_anchor.text_segments:
            for segment in layout.text_anchor.text_segments:
                start = segment.start_index if segment.start_index else 0
                end = segment.end_index if segment.end_index else len(document.text)
                text += document.text[start:end]
        
        return text.strip()
    
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type from file extension"""
        
        extension = Path(file_path).suffix.lower()
        mime_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".tiff": "image/tiff",
            ".bmp": "image/bmp",
            ".gif": "image/gif"
        }
        
        return mime_types.get(extension, "application/pdf")
    
    def _extract_observations(self, document: documentai.Document) -> List[str]:
        """Extract clinical observations from document"""
        
        observations = []
        
        # Look for observation sections
        observation_keywords = [
            "observations", "behavior during testing", "clinical observations",
            "test behavior", "behavioral observations"
        ]
        
        text = document.text.lower()
        for keyword in observation_keywords:
            if keyword in text:
                # Extract the section (simplified)
                start = text.find(keyword)
                end = text.find("\n\n", start + 200)  # Look for paragraph break
                if end == -1:
                    end = start + 500  # Default to 500 chars
                
                observation_text = document.text[start:end].strip()
                if len(observation_text) > 50:  # Meaningful content
                    observations.append(observation_text)
        
        return observations
    
    def _extract_recommendations(self, document: documentai.Document) -> List[str]:
        """Extract recommendations from document"""
        
        recommendations = []
        
        # Look for recommendation sections
        recommendation_keywords = [
            "recommendations", "suggested interventions", "treatment recommendations",
            "educational recommendations", "accommodations"
        ]
        
        text = document.text.lower()
        for keyword in recommendation_keywords:
            if keyword in text:
                # Extract the section
                start = text.find(keyword)
                # Look for numbered or bulleted list
                section = document.text[start:start+2000]
                
                # Extract items (simplified pattern matching)
                items = re.findall(r'[•\-\d\.]\s*([^\n•\-\d\.]+)', section)
                recommendations.extend([item.strip() for item in items if len(item.strip()) > 20])
        
        return recommendations
    
    def _extract_score_from_field(
        self,
        field: documentai.Document.Page.FormField,
        document: documentai.Document,
        assessment_type: AssessmentType
    ) -> Optional[PsychoedScoreDTO]:
        """Extract score from a form field"""
        
        field_name = self._get_text(field.field_name, document) if field.field_name else ""
        field_value = self._get_text(field.field_value, document) if field.field_value else ""
        
        if not field_name or not field_value:
            return None
        
        # Check if this is a score field
        score_keywords = ["score", "percentile", "index", "composite"]
        if not any(keyword in field_name.lower() for keyword in score_keywords):
            return None
        
        # Try to parse the value
        try:
            score_value = float(re.search(r'\d+\.?\d*', field_value).group())
        except:
            return None
        
        # Determine score type
        score_data = {
            "test_name": self.test_patterns.get(assessment_type, {}).get("name", str(assessment_type)),
            "subtest_name": field_name,
            "extraction_confidence": 0.8
        }
        
        # Assign to appropriate score type
        if "percentile" in field_name.lower():
            score_data["percentile_rank"] = score_value
        elif "scaled" in field_name.lower():
            score_data["scaled_score"] = score_value
        elif "t-score" in field_name.lower() or "t score" in field_name.lower():
            score_data["t_score"] = score_value
        else:
            score_data["standard_score"] = score_value
        
        return PsychoedScoreDTO(**score_data)
    
    def _extract_score_from_entity(
        self,
        entity: documentai.Document.Entity,
        document: documentai.Document,
        assessment_type: AssessmentType
    ) -> Optional[PsychoedScoreDTO]:
        """Extract score from a Document AI entity"""
        
        # Check if this is a score entity
        score_types = ["test_score", "standard_score", "percentile", "assessment_score"]
        if entity.type_ not in score_types:
            return None
        
        score_data = {
            "test_name": self.test_patterns.get(assessment_type, {}).get("name", str(assessment_type)),
            "extraction_confidence": entity.confidence if hasattr(entity, 'confidence') else 0.85
        }
        
        # Extract properties
        for prop in entity.properties:
            if prop.type_ == "subtest_name":
                score_data["subtest_name"] = self._get_text(prop.mention_text, document)
            elif prop.type_ == "score_value":
                value = self._get_text(prop.mention_text, document)
                try:
                    score_data["standard_score"] = float(value)
                except:
                    pass
            elif prop.type_ == "percentile":
                value = self._get_text(prop.mention_text, document)
                try:
                    score_data["percentile_rank"] = float(value)
                except:
                    pass
        
        if "subtest_name" in score_data and any(k in score_data for k in ["standard_score", "percentile_rank"]):
            return PsychoedScoreDTO(**score_data)
        
        return None
    
    def _deduplicate_scores(self, scores: List[PsychoedScoreDTO]) -> List[PsychoedScoreDTO]:
        """Remove duplicate scores, keeping highest confidence"""
        
        unique_scores = {}
        
        for score in scores:
            key = (score.test_name, score.subtest_name)
            
            if key not in unique_scores:
                unique_scores[key] = score
            else:
                # Keep the one with higher confidence
                if score.extraction_confidence > unique_scores[key].extraction_confidence:
                    unique_scores[key] = score
        
        return list(unique_scores.values())
    
    def _extract_academic_data(
        self,
        document: documentai.Document,
        scores: List[PsychoedScoreDTO],
        assessment_type: AssessmentType
    ) -> Dict[str, Any]:
        """Extract academic assessment data"""
        
        academic_data = {
            "reading": {},
            "mathematics": {},
            "written_language": {},
            "oral_language": {},
            "academic_fluency": {}
        }
        
        # Map scores to academic domains
        domain_mappings = {
            "reading": ["word reading", "reading comprehension", "pseudoword decoding", "reading fluency"],
            "mathematics": ["numerical operations", "math problem solving", "math fluency"],
            "written_language": ["spelling", "sentence composition", "essay composition", "writing fluency"],
            "oral_language": ["listening comprehension", "oral expression"]
        }
        
        for score in scores:
            subtest_lower = score.subtest_name.lower()
            
            for domain, keywords in domain_mappings.items():
                if any(keyword in subtest_lower for keyword in keywords):
                    academic_data[domain][score.subtest_name] = {
                        "standard_score": score.standard_score,
                        "percentile": score.percentile_rank,
                        "grade_equivalent": score.grade_equivalent
                    }
                    break
        
        return academic_data
    
    def _extract_behavioral_data(
        self,
        document: documentai.Document,
        scores: List[PsychoedScoreDTO],
        assessment_type: AssessmentType
    ) -> Dict[str, Any]:
        """Extract behavioral assessment data"""
        
        behavioral_data = {
            "composites": {},
            "scales": {},
            "clinical_scales": {},
            "adaptive_scales": {}
        }
        
        # Process behavioral rating scales
        for score in scores:
            if score.test_name == self.test_patterns[assessment_type]["name"]:
                # Composite scores
                if score.subtest_name in self.test_patterns[assessment_type].get("scales", []):
                    behavioral_data["composites"][score.subtest_name] = {
                        "t_score": score.t_score,
                        "percentile": score.percentile_rank,
                        "classification": score.qualitative_descriptor
                    }
                # Subscales
                elif score.subtest_name in self.test_patterns[assessment_type].get("subscales", []):
                    # Categorize subscales
                    if any(term in score.subtest_name.lower() for term in ["adaptive", "social", "leadership"]):
                        behavioral_data["adaptive_scales"][score.subtest_name] = {
                            "t_score": score.t_score,
                            "percentile": score.percentile_rank
                        }
                    else:
                        behavioral_data["clinical_scales"][score.subtest_name] = {
                            "t_score": score.t_score,
                            "percentile": score.percentile_rank
                        }
        
        return behavioral_data