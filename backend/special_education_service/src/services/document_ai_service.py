"""
Google Document AI integration for assessment document processing
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from google.cloud import documentai
from google.cloud.documentai import Document
from google.api_core.exceptions import GoogleAPIError

logger = logging.getLogger(__name__)

class DocumentAIService:
    """Service for processing assessment documents using Google Document AI"""
    
    def __init__(self, project_id: str = "thela002", location: str = "us", processor_id: str = "8ea662491b6ff80d"):
        """
        Initialize Document AI service
        
        Args:
            project_id: GCP project ID
            location: Processor location (us, eu, asia)
            processor_id: Document AI processor ID for form parsing
        """
        self.project_id = project_id
        self.location = location 
        self.processor_id = processor_id
        self.client = None
        self.processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
        
    async def _get_client(self) -> documentai.DocumentProcessorServiceClient:
        """Get or create Document AI client"""
        if self.client is None:
            self.client = documentai.DocumentProcessorServiceClient()
        return self.client
    
    async def process_document(self, file_path: str, document_id: str) -> Dict[str, Any]:
        """
        Process assessment document and extract structured data
        
        Args:
            file_path: Path to the uploaded document file
            document_id: Database document ID for tracking
            
        Returns:
            Dict containing extracted data and metadata
        """
        processing_start = time.time()
        try:
            logger.info(f"🔍 [DOC-AI] Starting Document AI processing for {document_id}")
            logger.info(f"📁 [DOC-AI] File path: {file_path}")
            
            # Read file content
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"Document file not found: {file_path}")
            
            file_size = file_path_obj.stat().st_size
            logger.info(f"📊 [DOC-AI] File size: {file_size} bytes ({file_size/1024:.1f} KB)")
            
            with open(file_path_obj, 'rb') as file:
                document_content = file.read()
            
            # Determine MIME type
            mime_type = self._get_mime_type(file_path_obj.suffix)
            logger.info(f"📄 [DOC-AI] MIME type: {mime_type}")
            
            # Create Document AI request
            client = await self._get_client()
            raw_document = documentai.RawDocument(
                content=document_content,
                mime_type=mime_type
            )
            
            request = documentai.ProcessRequest(
                name=self.processor_name,
                raw_document=raw_document
            )
            
            # Process document
            api_start = time.time()
            logger.info(f"📋 [DOC-AI] Sending document to Google Document AI...")
            logger.info(f"🌐 [DOC-AI] Processor: {self.processor_name}")
            
            result = client.process_document(request=request)
            document = result.document
            
            api_time = time.time() - api_start
            logger.info(f"⏱️ [DOC-AI] Google API call completed in {api_time:.2f} seconds")
            logger.info(f"📃 [DOC-AI] Document text length: {len(document.text)} characters")
            logger.info(f"📄 [DOC-AI] Document pages: {len(document.pages) if hasattr(document, 'pages') else 'Unknown'}")
            
            # Extract structured data
            extraction_start = time.time()
            extracted_data = await self._extract_assessment_data(document, document_id)
            extraction_time = time.time() - extraction_start
            
            total_time = time.time() - processing_start
            logger.info(f"⏱️ [DOC-AI] Score extraction completed in {extraction_time:.2f} seconds")
            logger.info(f"🎯 [DOC-AI] Total processing time: {total_time:.2f} seconds")
            logger.info(f"✅ [DOC-AI] Document AI processing completed for {document_id}")
            
            return extracted_data
            
        except GoogleAPIError as e:
            logger.error(f"❌ Google Document AI error for {document_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error processing {document_id}: {e}", exc_info=True)
            raise
    
    async def _extract_assessment_data(self, document: Document, document_id: str) -> Dict[str, Any]:
        """Extract assessment-specific data from Document AI response"""
        logger.info(f"🔍 Extracting assessment data from document {document_id}")
        
        # Basic document information
        extracted_data = {
            "document_id": document_id,
            "text_content": document.text,
            "confidence": 0.0,
            "extracted_scores": [],
            "assessment_metadata": {},
            "processing_status": "completed"
        }
        
        # Extract text entities (forms, tables, etc.)
        entities = []
        if hasattr(document, 'entities'):
            for entity in document.entities:
                entities.append({
                    "type": entity.type_,
                    "mention_text": entity.mention_text,
                    "confidence": entity.confidence,
                    "normalized_value": getattr(entity, 'normalized_value', None)
                })
        
        # Extract tables
        tables_data = []
        if hasattr(document, 'pages'):
            for page in document.pages:
                if hasattr(page, 'tables'):
                    for table in page.tables:
                        table_data = self._extract_table_data(table, document)
                        tables_data.append(table_data)
        
        # Look for assessment scores in text and tables
        scores = await self._extract_scores_from_content(document.text, tables_data)
        
        # Extract educational objectives and performance levels from narrative content
        educational_data = await self._extract_educational_content(document.text, document_id)
        
        extracted_data.update({
            "entities": entities,
            "tables": tables_data,
            "extracted_scores": scores,
            "educational_objectives": educational_data.get("objectives", []),
            "performance_levels": educational_data.get("performance_levels", {}),
            "recommendations": educational_data.get("recommendations", []),
            "confidence": self._calculate_confidence(entities, scores)
        })
        
        logger.info(f"📊 Extracted {len(scores)} scores from document {document_id}")
        return extracted_data
    
    async def _extract_educational_content(self, text: str, document_id: str) -> Dict[str, Any]:
        """
        Extract educational objectives, performance levels, and goals from narrative assessment reports
        """
        import re
        
        educational_data = {
            "objectives": [],
            "performance_levels": {},
            "recommendations": [],
            "areas_of_concern": [],
            "strengths": []
        }
        
        logger.info(f"🎯 Extracting educational content from document {document_id}")
        
        # Extract performance levels by academic area
        performance_patterns = {
            "reading": {
                "patterns": [
                    r"Reading\s+(?:Skills?|Level)[:,\s]*([^.]+?)(?:\.|$)",
                    r"reading\s+level[:\s]*([^.]+?)(?:\.|$)",
                    r"She\s+reads?\s+([^.]+?)(?:\.|$)",
                    r"(?:Basic|Word)\s+Reading[:\s]*([^.]+?)(?:\.|$)"
                ]
            },
            "math": {
                "patterns": [
                    r"Math\s+(?:Skills?|Level)[:,\s]*([^.]+?)(?:\.|$)",
                    r"math\s+level[:\s]*([^.]+?)(?:\.|$)",
                    r"Mathematics[:\s]*([^.]+?)(?:\.|$)",
                    r"arithmetic[:\s]*([^.]+?)(?:\.|$)"
                ]
            },
            "writing": {
                "patterns": [
                    r"Written?\s+(?:Expression|Skills?)[:\s]*([^.]+?)(?:\.|$)",
                    r"Writing\s+(?:Skills?|Level)[:\s]*([^.]+?)(?:\.|$)",
                    r"handwriting[:\s]*([^.]+?)(?:\.|$)",
                    r"writing\s+level[:\s]*([^.]+?)(?:\.|$)"
                ]
            },
            "spelling": {
                "patterns": [
                    r"Spelling\s+(?:Skills?|Level)[:\s]*([^.]+?)(?:\.|$)",
                    r"spelling\s+level[:\s]*([^.]+?)(?:\.|$)",
                    r"She\s+can\s+spell[:\s]*([^.]+?)(?:\.|$)"
                ]
            },
            "attention": {
                "patterns": [
                    r"Attention[:\s]*([^.]+?)(?:\.|$)",
                    r"attention\s+(?:span|difficulties)[:\s]*([^.]+?)(?:\.|$)",
                    r"focus[:\s]*([^.]+?)(?:\.|$)",
                    r"(?:restless|restlessness)[:\s]*([^.]+?)(?:\.|$)"
                ]
            },
            "behavior": {
                "patterns": [
                    r"Behavior[:\s]*([^.]+?)(?:\.|$)",
                    r"behavioral[:\s]*([^.]+?)(?:\.|$)",
                    r"She\s+(?:shows|demonstrates)\s+([^.]+?)(?:\.|$)"
                ]
            }
        }
        
        # Extract performance levels for each academic area
        for area, config in performance_patterns.items():
            area_findings = []
            for pattern in config["patterns"]:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    finding = match.group(1).strip()
                    if finding and len(finding) > 10:  # Filter out very short matches
                        area_findings.append(finding)
            
            if area_findings:
                educational_data["performance_levels"][area] = {
                    "current_level": area_findings[0],
                    "additional_notes": area_findings[1:] if len(area_findings) > 1 else []
                }
        
        # Extract recommendations
        recommendation_patterns = [
            r"RECOMMENDATIONS?\s*\n(.*?)(?:\n\n|$)",
            r"Recommendations?[:\s]*\n(.*?)(?:\n\n|$)",
            r"(?:•\s*)?([^.]+(?:strategy|intervention|support|therapy|guidance|instruction)[^.]*\.)",
            r"(?:•\s*)?([^.]+(?:recommend|suggest|advise|propose)[^.]*\.)"
        ]
        
        recommendations = []
        for pattern in recommendation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                rec_text = match.group(1).strip()
                if rec_text and len(rec_text) > 15:
                    # Split by bullet points or line breaks
                    rec_items = re.split(r'[•\n]', rec_text)
                    for item in rec_items:
                        clean_item = item.strip()
                        if clean_item and len(clean_item) > 20:
                            recommendations.append(clean_item)
        
        educational_data["recommendations"] = recommendations[:10]  # Limit to 10 recommendations
        
        # Extract areas of concern
        concern_patterns = [
            r"(?:shows|demonstrates|exhibits)\s+(?:signs of|difficulty with|problems with)\s+([^.]+?)(?:\.|$)",
            r"(?:struggles with|finds it hard to|difficulty)\s+([^.]+?)(?:\.|$)",
            r"(?:below|under)\s+(?:grade level|expectation)s?\s+(?:in|for)\s+([^.]+?)(?:\.|$)"
        ]
        
        areas_of_concern = []
        for pattern in concern_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                concern = match.group(1).strip()
                if concern and len(concern) > 5:
                    areas_of_concern.append(concern)
        
        educational_data["areas_of_concern"] = areas_of_concern[:8]  # Limit to 8 concerns
        
        # Extract strengths
        strength_patterns = [
            r"(?:strength|able to|can|demonstrates)\s+([^.]+?)(?:\.|$)",
            r"(?:appropriate|normal|within normal limits)\s+([^.]+?)(?:\.|$)",
            r"(?:friendly|demonstrates age-appropriate)\s+([^.]+?)(?:\.|$)"
        ]
        
        strengths = []
        for pattern in strength_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                strength = match.group(1).strip()
                if strength and len(strength) > 10:
                    strengths.append(strength)
        
        educational_data["strengths"] = strengths[:6]  # Limit to 6 strengths
        
        # Generate educational objectives based on the extracted content
        objectives = []
        
        # Create objectives based on performance levels
        for area, level_data in educational_data["performance_levels"].items():
            current_level = level_data["current_level"]
            
            # Generate SMART objectives based on current performance
            if "below" in current_level.lower() or "difficulty" in current_level.lower():
                objective = {
                    "area": area.title(),
                    "current_performance": current_level,
                    "goal": f"Improve {area} skills to grade-appropriate level",
                    "measurable_outcome": f"Student will demonstrate improved {area} performance as measured by curriculum-based assessments",
                    "timeline": "by the end of the IEP year",
                    "support_needed": "specialized instruction and accommodations"
                }
                objectives.append(objective)
        
        educational_data["objectives"] = objectives
        
        logger.info(f"📚 Educational content extracted: {len(objectives)} objectives, {len(educational_data['performance_levels'])} performance areas, {len(recommendations)} recommendations")
        
        return educational_data
    
    def _extract_table_data(self, table, document) -> Dict[str, Any]:
        """Extract data from a Document AI table"""
        rows = []
        if hasattr(table, 'body_rows'):
            for row in table.body_rows:
                row_data = []
                if hasattr(row, 'cells'):
                    for cell in row.cells:
                        cell_text = ""
                        if hasattr(cell, 'layout') and hasattr(cell.layout, 'text_anchor'):
                            # Extract text from cell using text segments and document text
                            cell_text_parts = []
                            for segment in cell.layout.text_anchor.text_segments:
                                if hasattr(segment, 'start_index') and hasattr(segment, 'end_index'):
                                    start_idx = segment.start_index if segment.start_index is not None else 0
                                    end_idx = segment.end_index if segment.end_index is not None else len(document.text)
                                    cell_text_parts.append(document.text[start_idx:end_idx])
                            cell_text = "".join(cell_text_parts)
                        row_data.append(cell_text.strip())
                rows.append(row_data)
        
        return {
            "rows": rows,
            "row_count": len(rows),
            "column_count": len(rows[0]) if rows else 0
        }
    
    async def _extract_scores_from_content(self, text: str, tables: List[Dict]) -> List[Dict[str, Any]]:
        """
        Extract assessment scores from document text and tables
        Enhanced with comprehensive score patterns for multiple assessment types
        """
        scores = []
        import re
        
        # Enhanced assessment score patterns
        score_patterns = {
            "WISC-V": {
                "patterns": [
                    (r"Full Scale IQ.*?(?:SS|Standard Score)[:\s]*(\d{2,3})", "Full Scale IQ", 0.90),
                    (r"Verbal Comprehension.*?(?:Index|VCI)[:\s]*(\d{2,3})", "Verbal Comprehension Index", 0.85),
                    (r"Perceptual Reasoning.*?(?:Index|PRI)[:\s]*(\d{2,3})", "Perceptual Reasoning Index", 0.85),
                    (r"Working Memory.*?(?:Index|WMI)[:\s]*(\d{2,3})", "Working Memory Index", 0.85),
                    (r"Processing Speed.*?(?:Index|PSI)[:\s]*(\d{2,3})", "Processing Speed Index", 0.85),
                    (r"General Ability.*?(?:Index|GAI)[:\s]*(\d{2,3})", "General Ability Index", 0.80),
                    (r"Cognitive Proficiency.*?(?:Index|CPI)[:\s]*(\d{2,3})", "Cognitive Proficiency Index", 0.80)
                ]
            },
            "WIAT-IV": {
                "patterns": [
                    (r"(?:Total|Overall|Composite).*?Achievement.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Total Achievement", 0.85),
                    (r"(?:Basic|Word) Reading.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Basic Reading", 0.80),
                    (r"Reading Comprehension.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Reading Comprehension", 0.80),
                    (r"Spelling.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Spelling", 0.80),
                    (r"Written Expression.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Written Expression", 0.80),
                    (r"Numerical Operations.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Numerical Operations", 0.80),
                    (r"Math Problem Solving.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Math Problem Solving", 0.80),
                    (r"Academic Skills.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Academic Skills", 0.75),
                    (r"Academic Fluency.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Academic Fluency", 0.75)
                ]
            },
            "BASC-3": {
                "patterns": [
                    (r"Behavioral Symptoms.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Behavioral Symptoms Index", 0.80),
                    (r"Externalizing.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Externalizing Problems", 0.80),
                    (r"Internalizing.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Internalizing Problems", 0.80),
                    (r"School Problems.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "School Problems", 0.80),
                    (r"Adaptive Skills.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Adaptive Skills", 0.80),
                    (r"Attention Problems.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Attention Problems", 0.75),
                    (r"Hyperactivity.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Hyperactivity", 0.75),
                    (r"Aggression.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Aggression", 0.75),
                    (r"Conduct Problems.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Conduct Problems", 0.75),
                    (r"Anxiety.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Anxiety", 0.75),
                    (r"Depression.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Depression", 0.75),
                    (r"Learning Problems.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Learning Problems", 0.75)
                ]
            },
            "KTEA-3": {
                "patterns": [
                    (r"Comprehensive Achievement.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Comprehensive Achievement", 0.85),
                    (r"Reading.*?Composite.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Reading Composite", 0.80),
                    (r"Math.*?Composite.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Math Composite", 0.80),
                    (r"Written Language.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Written Language", 0.80),
                    (r"Oral Language.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Oral Language", 0.80),
                    (r"Letter.*?Word Recognition.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Letter & Word Recognition", 0.75),
                    (r"Reading Comprehension.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Reading Comprehension", 0.75),
                    (r"Math Concepts.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Math Concepts & Applications", 0.75),
                    (r"Math Computation.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Math Computation", 0.75)
                ]
            },
            "CONNERS-3": {
                "patterns": [
                    (r"Conners.*?Global.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Conners Global Index", 0.80),
                    (r"Inattention.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Inattention", 0.80),
                    (r"Hyperactivity.*?Impulsivity.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Hyperactivity/Impulsivity", 0.80),
                    (r"Learning Problems.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Learning Problems", 0.75),
                    (r"Executive Functioning.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Executive Functioning", 0.75),
                    (r"Aggression.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Aggression", 0.75),
                    (r"Peer Relations.*?(?:T-Score|T Score)[:\s]*(\d{2,3})", "Peer Relations", 0.70)
                ]
            },
            "WJ-IV": {
                "patterns": [
                    (r"General Intellectual Ability.*?(?:SS|Standard)[:\s]*(\d{2,3})", "General Intellectual Ability", 0.85),
                    (r"Brief Intellectual Ability.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Brief Intellectual Ability", 0.80),
                    (r"Comprehension-Knowledge.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Comprehension-Knowledge", 0.80),
                    (r"Fluid Reasoning.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Fluid Reasoning", 0.80),
                    (r"Processing Speed.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Processing Speed", 0.80),
                    (r"Short-Term Working Memory.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Short-Term Working Memory", 0.80),
                    (r"Academic Achievement.*?(?:SS|Standard)[:\s]*(\d{2,3})", "Broad Achievement", 0.75)
                ]
            },
            "DAS-II": {
                "patterns": [
                    (r"General Conceptual Ability.*?(?:GCA|Standard)[:\s]*(\d{2,3})", "General Conceptual Ability", 0.85),
                    (r"Verbal.*?(?:Cluster|Standard)[:\s]*(\d{2,3})", "Verbal", 0.80),
                    (r"Nonverbal.*?(?:Cluster|Standard)[:\s]*(\d{2,3})", "Nonverbal", 0.80),
                    (r"Spatial.*?(?:Cluster|Standard)[:\s]*(\d{2,3})", "Spatial", 0.80),
                    (r"Working Memory.*?(?:Cluster|Standard)[:\s]*(\d{2,3})", "Working Memory", 0.80),
                    (r"Processing Speed.*?(?:Cluster|Standard)[:\s]*(\d{2,3})", "Processing Speed", 0.80)
                ]
            }
        }
        
        # Search for scores using enhanced patterns
        for test_name, test_data in score_patterns.items():
            for pattern, subtest_name, confidence in test_data["patterns"]:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    try:
                        score_value = int(match.group(1))
                        
                        # Validate score ranges
                        if self._is_valid_score(score_value, test_name, subtest_name):
                            scores.append({
                                "test_name": test_name,
                                "subtest_name": subtest_name,
                                "standard_score": score_value,
                                "extraction_confidence": confidence,
                                "source": "enhanced_pattern",
                                "raw_match": match.group(0)[:100]  # First 100 chars of match
                            })
                    except ValueError:
                        continue
        
        # Extract scores from tables with enhanced logic
        for table in tables:
            table_scores = self._extract_scores_from_table_enhanced(table)
            scores.extend(table_scores)
        
        # Remove duplicates (keep highest confidence)
        scores = self._deduplicate_scores(scores)
        
        logger.info(f"📊 Enhanced extraction found {len(scores)} scores across {len(score_patterns)} assessment types")
        return scores
    
    def _is_valid_score(self, score: int, test_name: str, subtest_name: str) -> bool:
        """Validate score ranges based on assessment type"""
        # Standard score ranges (typically 40-160)
        standard_score_tests = ["WISC-V", "WIAT-IV", "KTEA-3", "WJ-IV", "DAS-II"]
        if test_name in standard_score_tests:
            return 40 <= score <= 160
        
        # T-score ranges (typically 20-100)
        t_score_tests = ["BASC-3", "CONNERS-3"]
        if test_name in t_score_tests:
            return 20 <= score <= 100
        
        # Default validation for unknown tests
        return 20 <= score <= 160
    
    def _extract_scores_from_table_enhanced(self, table: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced table score extraction with assessment type detection"""
        scores = []
        
        # Look for header row indicators
        assessment_type = None
        headers = []
        
        for row_idx, row in enumerate(table.get("rows", [])):
            if row_idx == 0:  # Check first row for headers
                headers = [cell.lower() for cell in row]
                
                # Detect assessment type from headers
                header_text = " ".join(headers)
                if any(keyword in header_text for keyword in ["wisc", "wechsler"]):
                    assessment_type = "WISC-V"
                elif any(keyword in header_text for keyword in ["wiat", "achievement"]):
                    assessment_type = "WIAT-IV"
                elif any(keyword in header_text for keyword in ["basc", "behavior"]):
                    assessment_type = "BASC-3"
                continue
            
            # Extract scores from data rows
            if len(row) >= 2:
                for col_idx, cell in enumerate(row):
                    if cell.isdigit():
                        score_value = int(cell)
                        
                        # Get subtest name (usually first column)
                        subtest_name = row[0] if row[0] and not row[0].isdigit() else f"Subtest {col_idx}"
                        
                        # Determine test type if not already detected
                        if not assessment_type:
                            assessment_type = self._detect_test_type_from_subtest(subtest_name)
                        
                        # Validate score
                        if self._is_valid_score(score_value, assessment_type or "Unknown", subtest_name):
                            scores.append({
                                "test_name": assessment_type or "Unknown",
                                "subtest_name": subtest_name,
                                "standard_score": score_value,
                                "extraction_confidence": 0.65,  # Lower confidence for table extraction
                                "source": "table_enhanced",
                                "table_position": f"row_{row_idx}_col_{col_idx}"
                            })
        
        return scores
    
    def _detect_test_type_from_subtest(self, subtest_name: str) -> str:
        """Detect assessment type based on subtest name"""
        name_lower = subtest_name.lower()
        
        # WISC-V subtests
        wisc_subtests = ["similarities", "vocabulary", "block design", "matrix reasoning", 
                        "digit span", "coding", "symbol search", "figure weights"]
        if any(subtest in name_lower for subtest in wisc_subtests):
            return "WISC-V"
        
        # WIAT-IV subtests
        wiat_subtests = ["word reading", "reading comprehension", "spelling", "math computation",
                        "numerical operations", "written expression"]
        if any(subtest in name_lower for subtest in wiat_subtests):
            return "WIAT-IV"
        
        # BASC-3 scales
        basc_scales = ["hyperactivity", "aggression", "conduct problems", "anxiety", "depression",
                      "attention problems", "learning problems", "withdrawal"]
        if any(scale in name_lower for scale in basc_scales):
            return "BASC-3"
        
        return "Unknown"
    
    def _deduplicate_scores(self, scores: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate scores, keeping the one with highest confidence"""
        seen = {}
        
        for score in scores:
            key = (score["test_name"], score["subtest_name"], score["standard_score"])
            
            if key not in seen or score["extraction_confidence"] > seen[key]["extraction_confidence"]:
                seen[key] = score
        
        return list(seen.values())
    
    def _extract_scores_from_table(self, table: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract scores from table data"""
        scores = []
        
        for row in table.get("rows", []):
            # Look for rows with numeric scores
            if len(row) >= 2:
                for i, cell in enumerate(row):
                    # Check if cell contains a standard score (2-3 digits)
                    if cell.isdigit() and 40 <= int(cell) <= 160:
                        # Assume first column is subtest name
                        subtest_name = row[0] if row[0] else f"Subtest {i}"
                        
                        scores.append({
                            "test_name": "Unknown",  # Would need more context
                            "subtest_name": subtest_name,
                            "standard_score": int(cell),
                            "extraction_confidence": 0.65,  # Lower confidence for table extraction
                            "source": "table_extraction"
                        })
        
        return scores
    
    def _calculate_confidence(self, entities: List[Dict], scores: List[Dict]) -> float:
        """Calculate overall extraction confidence"""
        if not entities and not scores:
            return 0.0
        
        # Base confidence on number of extracted elements
        confidence = min(0.5 + (len(scores) * 0.1) + (len(entities) * 0.05), 0.95)
        return round(confidence, 2)
    
    def _get_mime_type(self, file_extension: str) -> str:
        """Get MIME type for file extension"""
        mime_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return mime_types.get(file_extension.lower(), 'application/pdf')

# Singleton instance
document_ai_service = DocumentAIService()