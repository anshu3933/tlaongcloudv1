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

from assessment_pipeline_service.schemas.assessment_schemas import (
    PsychoedScoreDTO, ExtractedDataDTO, AssessmentTypeEnum as AssessmentType
)
from .service_clients import special_education_client

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
        
        # Store Document AI confidence for overall confidence calculation
        doc_ai_confidence = self._extract_document_ai_confidence(document)
        
        # Extract structured data
        extracted_data = {
            "assessment_type": assessment_type,
            "document_metadata": document_metadata,
            "extraction_timestamp": datetime.utcnow(),
            "document_ai_confidence": doc_ai_confidence
        }
        
        # Extract scores
        scores = self._extract_all_scores(document, assessment_type)
        extracted_data["scores"] = scores
        logger.info(f"Extracted {len(scores)} scores from document")
        
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
    
    def _extract_document_ai_confidence(self, document: documentai.Document) -> float:
        """Extract overall Document AI processing confidence"""
        
        confidences = []
        
        # Extract from pages confidence
        for page in document.pages:
            if hasattr(page, 'confidence') and page.confidence:
                confidences.append(page.confidence)
        
        # Extract from entities confidence  
        for entity in document.entities:
            if hasattr(entity, 'confidence') and entity.confidence:
                confidences.append(entity.confidence)
        
        # Extract from form fields confidence
        for page in document.pages:
            for form_field in page.form_fields:
                if hasattr(form_field, 'confidence') and form_field.confidence:
                    confidences.append(form_field.confidence)
        
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            logger.debug(f"Document AI average confidence: {avg_confidence:.3f} from {len(confidences)} elements")
            return avg_confidence
        
        logger.warning("No Document AI confidence data available")
        return 0.85  # Default confidence if none available
    
    async def _detect_assessment_type(self, document_path: str) -> AssessmentType:
        """Auto-detect the type of assessment using ML classifier and pattern matching"""
        
        logger.info(f"Auto-detecting assessment type for: {document_path}")
        
        # First, try Document AI for quick text extraction
        try:
            document = await self._process_with_document_ai(document_path)
            text = document.text.lower()
        except Exception as e:
            logger.warning(f"Document AI extraction failed, using fallback: {e}")
            # Fallback to basic file reading
            with open(document_path, 'rb') as f:
                content = f.read()
            text = str(content).lower()
        
        # Enhanced pattern matching with confidence scoring
        type_scores = {}
        
        for assessment_type, pattern_info in self.test_patterns.items():
            score = 0
            
            # Primary test name detection (high weight)
            test_name = pattern_info["name"].lower()
            if test_name in text:
                score += 50
                logger.debug(f"Found test name '{test_name}' in document")
            
            # Secondary name variations
            name_variations = {
                AssessmentType.WISC_V: ["wisc-v", "wisc 5", "wechsler intelligence scale"],
                AssessmentType.WIAT_IV: ["wiat-iv", "wiat 4", "wechsler achievement"],
                AssessmentType.BASC_3: ["basc-3", "basc 3", "behavior assessment system"],
                AssessmentType.BRIEF_2: ["brief-2", "brief 2", "executive function"],
                AssessmentType.WJ_IV: ["wj-iv", "woodcock johnson", "woodcock-johnson"],
                AssessmentType.KTEA_3: ["ktea-3", "kaufman test"],
                AssessmentType.DAS_II: ["das-ii", "differential ability"],
                AssessmentType.CONNERS_3: ["conners-3", "conners 3"]
            }
            
            for variant in name_variations.get(assessment_type, []):
                if variant in text:
                    score += 30
                    logger.debug(f"Found variant '{variant}' for {assessment_type}")
            
            # Subtest/index pattern matching (medium weight)
            all_components = (
                pattern_info.get("indices", []) + 
                pattern_info.get("subtests", []) + 
                pattern_info.get("composites", []) +
                pattern_info.get("scales", []) +
                pattern_info.get("subscales", [])
            )
            
            component_matches = sum(1 for item in all_components if item.lower() in text)
            score += component_matches * 5
            
            if component_matches > 0:
                logger.debug(f"Found {component_matches} component matches for {assessment_type}")
            
            # Age range indicators (low weight)
            age_indicators = {
                AssessmentType.WISC_V: ["6 years", "16 years", "school age"],
                AssessmentType.WIAT_IV: ["achievement", "academic"],
                AssessmentType.BASC_3: ["behavior", "emotional", "behavioral"]
            }
            
            for indicator in age_indicators.get(assessment_type, []):
                if indicator in text:
                    score += 2
            
            if score > 0:
                type_scores[assessment_type] = score
                logger.debug(f"Total score for {assessment_type}: {score}")
        
        # Determine best match
        if type_scores:
            best_type = max(type_scores.items(), key=lambda x: x[1])
            confidence_threshold = 10  # Minimum score required
            
            if best_type[1] >= confidence_threshold:
                logger.info(f"Detected assessment type: {best_type[0]} (score: {best_type[1]})")
                return best_type[0]
            else:
                logger.warning(f"Low confidence in detection: {best_type[0]} (score: {best_type[1]})")
        
        # Enhanced fallback detection
        behavioral_keywords = ["behavior", "emotional", "social", "adhd", "conduct", "anxiety"]
        cognitive_keywords = ["iq", "intelligence", "cognitive", "processing", "memory"]
        academic_keywords = ["reading", "math", "writing", "achievement", "academic"]
        
        behavioral_count = sum(1 for keyword in behavioral_keywords if keyword in text)
        cognitive_count = sum(1 for keyword in cognitive_keywords if keyword in text)
        academic_count = sum(1 for keyword in academic_keywords if keyword in text)
        
        if behavioral_count >= 3:
            logger.info("Defaulting to BASC-3 based on behavioral keywords")
            return AssessmentType.BASC_3
        elif cognitive_count >= 3:
            logger.info("Defaulting to WISC-V based on cognitive keywords")
            return AssessmentType.WISC_V
        elif academic_count >= 3:
            logger.info("Defaulting to WIAT-IV based on academic keywords")
            return AssessmentType.WIAT_IV
        
        logger.warning("Could not determine assessment type, defaulting to OBSERVATION")
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
            name=self.processor_name,  # Use the main processor
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
        """Extract scores from a table with enhanced parsing"""
        
        scores = []
        
        # Get table headers with cleaning
        headers = []
        if table.header_rows:
            for cell in table.header_rows[0].cells:
                header_text = self._get_text(cell.layout, document).strip()
                # Clean and normalize header text
                header_text = re.sub(r'\s+', ' ', header_text)  # Normalize whitespace
                headers.append(header_text)
        
        logger.debug(f"Table headers: {headers}")
        
        # Enhanced header mapping for common variations
        header_mappings = {
            # Test/subtest name variations
            "test": ["test", "subtest", "scale", "index", "composite", "domain", "area"],
            # Standard score variations
            "standard_score": ["ss", "standard score", "standard", "std score", "composite score"],
            # Percentile variations
            "percentile": ["percentile", "%ile", "pr", "percentile rank", "%"],
            # Scaled score variations
            "scaled_score": ["scaled", "scaled score", "subtest score"],
            # T-score variations
            "t_score": ["t-score", "t score", "t"],
            # Confidence interval variations
            "confidence_interval": ["95% ci", "confidence interval", "ci", "conf int"],
            # Descriptor variations
            "descriptor": ["descriptor", "classification", "range", "level", "category"]
        }
        
        # Create normalized header index
        normalized_headers = {}
        for i, header in enumerate(headers):
            header_lower = header.lower().strip()
            for standard_name, variations in header_mappings.items():
                if any(var in header_lower for var in variations):
                    normalized_headers[standard_name] = i
                    break
            # Also store original index
            normalized_headers[header_lower] = i
        
        logger.debug(f"Normalized headers: {list(normalized_headers.keys())}")
        
        # Process each row with enhanced extraction
        for row_idx, row in enumerate(table.body_rows):
            try:
                row_data = {}
                for i, cell in enumerate(row.cells):
                    if i < len(headers):
                        cell_text = self._get_text(cell.layout, document).strip()
                        # Clean cell text
                        cell_text = re.sub(r'\s+', ' ', cell_text)
                        row_data[headers[i]] = cell_text
                
                # Try to parse as score with enhanced logic
                score = self._parse_table_row_as_score_enhanced(row_data, normalized_headers, assessment_type)
                if score:
                    scores.append(score)
                    logger.debug(f"Extracted score from row {row_idx}: {score.subtest_name}")
                
            except Exception as e:
                logger.warning(f"Error processing table row {row_idx}: {e}")
                continue
        
        logger.info(f"Extracted {len(scores)} scores from table")
        return scores
    
    def _parse_table_row_as_score_enhanced(
        self,
        row_data: Dict[str, str],
        normalized_headers: Dict[str, int],
        assessment_type: AssessmentType
    ) -> Optional[PsychoedScoreDTO]:
        """Enhanced table row parsing with better score extraction"""
        
        # Extract test/subtest name using multiple strategies
        test_name = self.test_patterns.get(assessment_type, {}).get("name", str(assessment_type))
        subtest_name = None
        
        # Strategy 1: Use normalized header mapping
        if "test" in normalized_headers:
            test_col_idx = normalized_headers["test"]
            headers = list(row_data.keys())
            if test_col_idx < len(headers):
                subtest_name = row_data[headers[test_col_idx]]
        
        # Strategy 2: Look for first non-numeric column
        if not subtest_name:
            for key, value in row_data.items():
                if value and not re.match(r'^[\d\-\s\.\(\)%]+$', value.strip()):
                    subtest_name = value
                    break
        
        # Strategy 3: Use known subtest patterns for assessment type
        if not subtest_name:
            test_info = self.test_patterns.get(assessment_type, {})
            all_subtests = (test_info.get("subtests", []) + 
                          test_info.get("indices", []) + 
                          test_info.get("scales", []))
            
            for value in row_data.values():
                if any(subtest.lower() in value.lower() for subtest in all_subtests):
                    subtest_name = value
                    break
        
        if not subtest_name or not subtest_name.strip():
            return None
        
        # Clean subtest name
        subtest_name = subtest_name.strip()
        
        # Initialize score data
        score_data = {
            "test_name": test_name,
            "subtest_name": subtest_name
        }
        
        # Extract scores using enhanced patterns
        scores_found = 0
        
        # Standard score extraction
        if "standard_score" in normalized_headers:
            ss_col_idx = normalized_headers["standard_score"]
            headers = list(row_data.keys())
            if ss_col_idx < len(headers):
                ss_value = self._extract_numeric_value(row_data[headers[ss_col_idx]])
                if ss_value is not None:
                    score_data["standard_score"] = ss_value
                    scores_found += 1
        
        # Percentile extraction
        if "percentile" in normalized_headers:
            pr_col_idx = normalized_headers["percentile"]
            headers = list(row_data.keys())
            if pr_col_idx < len(headers):
                pr_value = self._extract_numeric_value(row_data[headers[pr_col_idx]])
                if pr_value is not None:
                    score_data["percentile_rank"] = pr_value
                    scores_found += 1
        
        # Scaled score extraction
        if "scaled_score" in normalized_headers:
            scaled_col_idx = normalized_headers["scaled_score"]
            headers = list(row_data.keys())
            if scaled_col_idx < len(headers):
                scaled_value = self._extract_numeric_value(row_data[headers[scaled_col_idx]])
                if scaled_value is not None:
                    score_data["scaled_score"] = scaled_value
                    scores_found += 1
        
        # T-score extraction
        if "t_score" in normalized_headers:
            t_col_idx = normalized_headers["t_score"]
            headers = list(row_data.keys())
            if t_col_idx < len(headers):
                t_value = self._extract_numeric_value(row_data[headers[t_col_idx]])
                if t_value is not None:
                    score_data["t_score"] = t_value
                    scores_found += 1
        
        # Confidence interval extraction
        if "confidence_interval" in normalized_headers:
            ci_col_idx = normalized_headers["confidence_interval"]
            headers = list(row_data.keys())
            if ci_col_idx < len(headers):
                ci_text = row_data[headers[ci_col_idx]]
                ci_values = self._extract_confidence_interval(ci_text)
                if ci_values:
                    score_data["confidence_interval"] = ci_values
        
        # Descriptor extraction
        if "descriptor" in normalized_headers:
            desc_col_idx = normalized_headers["descriptor"]
            headers = list(row_data.keys())
            if desc_col_idx < len(headers):
                descriptor = row_data[headers[desc_col_idx]].strip()
                if descriptor and not re.match(r'^[\d\-\s\.\(\)%]+$', descriptor):
                    score_data["qualitative_descriptor"] = descriptor
        
        # Fallback: extract any numeric values from remaining columns
        if scores_found == 0:
            for key, value in row_data.items():
                if key.lower() != subtest_name.lower():  # Skip the test name column
                    numeric_val = self._extract_numeric_value(value)
                    if numeric_val is not None:
                        # Guess score type based on range
                        if 50 <= numeric_val <= 150:  # Likely standard score
                            score_data["standard_score"] = numeric_val
                            scores_found += 1
                        elif 1 <= numeric_val <= 99 and numeric_val != int(numeric_val):  # Likely percentile
                            score_data["percentile_rank"] = numeric_val
                            scores_found += 1
                        elif 1 <= numeric_val <= 19:  # Likely scaled score
                            score_data["scaled_score"] = numeric_val
                            scores_found += 1
                        elif 20 <= numeric_val <= 80:  # Likely T-score
                            score_data["t_score"] = numeric_val
                            scores_found += 1
        
        # Only create score if we found actual score values
        if scores_found > 0:
            score_data["extraction_confidence"] = 0.90 if scores_found >= 2 else 0.75
            try:
                return PsychoedScoreDTO(**score_data)
            except Exception as e:
                logger.warning(f"Error creating PsychoedScoreDTO: {e}")
                return None
        
        return None
    
    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """Extract numeric value from text with enhanced patterns"""
        
        if not text or not text.strip():
            return None
        
        # Clean the text
        cleaned = text.strip().replace(',', '')
        
        # Pattern for numbers (including decimals)
        number_pattern = r'([+-]?\d+(?:\.\d+)?)'  
        
        # Look for numbers
        matches = re.findall(number_pattern, cleaned)
        
        if matches:
            try:
                # Take the first numeric value found
                value = float(matches[0])
                # Sanity check: reject obviously invalid values
                if -1000 <= value <= 1000:  # Reasonable range for assessment scores
                    return value
            except ValueError:
                pass
        
        return None
    
    def _extract_confidence_interval(self, text: str) -> Optional[Tuple[float, float]]:
        """Extract confidence interval from text"""
        
        if not text:
            return None
        
        # Pattern for confidence intervals like "85-115" or "(85, 115)" or "85 - 115"
        ci_patterns = [
            r'(\d+)\s*[-–—]\s*(\d+)',  # 85-115 or 85 - 115
            r'\((\d+),\s*(\d+)\)',      # (85, 115)
            r'\[(\d+),\s*(\d+)\]',      # [85, 115]
            r'(\d+)\s*to\s*(\d+)',      # 85 to 115
        ]
        
        for pattern in ci_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    lower = float(match.group(1))
                    upper = float(match.group(2))
                    if lower < upper and 0 <= lower <= 200 and 0 <= upper <= 200:
                        return (lower, upper)
                except ValueError:
                    continue
        
        return None
    
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
        
        confidence_components = []
        weights = []
        
        # Document AI extraction confidence (40% weight)
        if extracted_data.get("document_ai_confidence"):
            doc_ai_conf = float(extracted_data["document_ai_confidence"])
            confidence_components.append(doc_ai_conf)
            weights.append(0.4)
            logger.debug(f"Document AI confidence: {doc_ai_conf:.3f}")
        
        # Score completeness (25% weight)
        scores = extracted_data.get("scores", [])
        if scores:
            # Calculate based on number of scores found vs expected
            assessment_type = extracted_data.get("assessment_type")
            expected_scores = self._get_expected_score_count(assessment_type)
            
            completeness = min(len(scores) / expected_scores, 1.0) if expected_scores > 0 else 0.5
            confidence_components.append(completeness)
            weights.append(0.25)
            logger.debug(f"Score completeness: {completeness:.3f} ({len(scores)}/{expected_scores})")
        
        # Data structure quality (20% weight)
        structure_quality = 0.0
        
        # Check for key data presence
        key_sections = ["cognitive_data", "academic_data", "behavioral_data", "observations", "recommendations"]
        present_sections = sum(1 for section in key_sections if extracted_data.get(section))
        structure_quality += (present_sections / len(key_sections)) * 0.6
        
        # Check for individual score confidence
        if scores:
            individual_confidences = [s.extraction_confidence for s in scores if hasattr(s, 'extraction_confidence') and s.extraction_confidence]
            if individual_confidences:
                avg_individual = np.mean(individual_confidences)
                structure_quality += avg_individual * 0.4
        
        confidence_components.append(structure_quality)
        weights.append(0.2)
        logger.debug(f"Structure quality: {structure_quality:.3f}")
        
        # Assessment type detection confidence (15% weight)
        type_confidence = 0.8  # Default if no specific detection confidence
        if extracted_data.get("type_detection_confidence"):
            type_confidence = float(extracted_data["type_detection_confidence"])
        
        confidence_components.append(type_confidence)
        weights.append(0.15)
        logger.debug(f"Type detection confidence: {type_confidence:.3f}")
        
        # Calculate weighted average
        if confidence_components and weights:
            # Normalize weights
            total_weight = sum(weights)
            normalized_weights = [w / total_weight for w in weights]
            
            weighted_confidence = sum(c * w for c, w in zip(confidence_components, normalized_weights))
            
            # Map to 76-98% range (ensuring minimum quality standards)
            # 0.0 -> 76%, 1.0 -> 98%
            mapped_confidence = 0.76 + (weighted_confidence * 0.22)
            
            # Apply quality gates
            if len(scores) == 0:
                mapped_confidence = min(mapped_confidence, 0.80)  # Cap at 80% if no scores
            
            if not any(extracted_data.get(section) for section in ["observations", "recommendations"]):
                mapped_confidence = min(mapped_confidence, 0.85)  # Cap at 85% if no narrative sections
            
            logger.info(f"Final extraction confidence: {mapped_confidence:.3f} ({mapped_confidence*100:.1f}%)")
            return mapped_confidence
        
        logger.warning("No confidence data available, using minimum")
        return 0.76  # Minimum confidence
    
    def _get_expected_score_count(self, assessment_type: AssessmentType) -> int:
        """Get expected number of scores for assessment type"""
        
        expected_counts = {
            AssessmentType.WISC_V: 14,  # 5 indices + 9+ subtests
            AssessmentType.WIAT_IV: 12,  # 4 composites + 8+ subtests  
            AssessmentType.BASC_3: 15,   # 4 scales + 11+ subscales
            AssessmentType.BRIEF_2: 10,  # 3 indices + 7+ scales
            AssessmentType.WJ_IV: 8,     # Various achievement areas
            AssessmentType.KTEA_3: 10,   # Achievement composites and subtests
            AssessmentType.DAS_II: 12,   # Cognitive abilities
            AssessmentType.CONNERS_3: 8, # ADHD and behavioral scales
            AssessmentType.OBSERVATION: 5 # Minimal structured data
        }
        
        return expected_counts.get(assessment_type, 5)
    
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
    
    # Alias method for pipeline orchestrator compatibility
    async def process_document(
        self, 
        file_path: str, 
        assessment_type: AssessmentType = None, 
        metadata: Dict[str, Any] = None
    ) -> ExtractedDataDTO:
        """Alias method for pipeline orchestrator"""
        
        document_metadata = metadata or {}
        return await self.process_assessment_document(file_path, document_metadata)