"""Production-ready Gemini client for IEP generation"""

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pybreaker import CircuitBreaker
import json
import logging
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime
import os
import hashlib
import gzip
import base64

logger = logging.getLogger(__name__)


class GeminiClient:
    """Production-ready Gemini client for IEP generation"""
    
    def __init__(self):
        # Real Gemini API authentication only - no mock mode
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if self.api_key:
            logger.info("🔑 Using GEMINI_API_KEY for authentication")
            genai.configure(api_key=self.api_key)
        else:
            # Try Application Default Credentials (ADC)
            try:
                import google.auth
                from google.auth import default
                
                # Check if ADC is available
                credentials, project = default()
                logger.info(f"🔐 Using Application Default Credentials for project: {project}")
                genai.configure(credentials=credentials)
                
            except Exception as adc_error:
                logger.error(f"❌ No authentication method available:")
                logger.error(f"   - GEMINI_API_KEY not set")
                logger.error(f"   - Application Default Credentials failed: {adc_error}")
                raise ValueError("GEMINI_API_KEY required for operation. Get API key from: https://aistudio.google.com/app/apikey")
        
        # Circuit breaker configuration
        self.circuit_breaker = CircuitBreaker(
            fail_max=5,
            reset_timeout=60,
            exclude=[ValueError, json.JSONDecodeError]  # Don't trip on validation errors
        )
        
        # Model configuration for Gemini 2.5 Flash
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 32768,  # INCREASED from 8192 to 32768 for comprehensive IEP content
                "response_mime_type": "application/json",
            },
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
        )
        
        # Response size limits - INCREASED for comprehensive IEP content
        self.max_response_size = 500000  # 500KB uncompressed (increased from 100KB)
        self.compress_threshold = 200000  # Compress if > 200KB (increased from 50KB)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def generate_iep_content(
        self, 
        student_data: Dict[str, Any],
        template_data: Dict[str, Any],
        previous_ieps: Optional[List[Dict]] = None,
        previous_assessments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Generate IEP content with Gemini"""
        
        # Build structured prompt
        prompt = self._build_iep_prompt(
            student_data, 
            template_data, 
            previous_ieps, 
            previous_assessments
        )
        
        # Generate request ID for tracking
        request_id = hashlib.md5(
            f"{student_data.get('student_id')}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()
        
        # Call Gemini with circuit breaker or test mode
        @self.circuit_breaker
        async def _generate():
            start_time = datetime.utcnow()
            
            # Real Gemini API call
            try:
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                
                response = await loop.run_in_executor(
                    None,
                    self.model.generate_content,
                    prompt
                )
                
                # Extract text and clean it
                raw_text = response.text
                
                # Remove any markdown code blocks if present
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                
                raw_text = raw_text.strip()
                
                # Check response size
                response_size = len(raw_text.encode('utf-8'))
                if response_size > self.max_response_size:
                    logger.warning(f"Gemini response too large ({response_size} bytes), truncating")
                    # Truncate at JSON boundary if possible
                    raw_text = self._truncate_json_safely(raw_text, self.max_response_size)
                
                # Validate it's valid JSON
                try:
                    json.loads(raw_text)
                except json.JSONDecodeError as e:
                    logger.error(f"Gemini returned invalid JSON: {e}")
                    logger.error(f"Raw response (first 500 chars): {raw_text[:500]}")
                    raise ValueError(f"Invalid JSON from Gemini: {e}")
                
                # Compress if needed
                compressed = False
                if response_size > self.compress_threshold:
                    compressed_data = gzip.compress(raw_text.encode('utf-8'))
                    if len(compressed_data) < response_size * 0.8:  # Only if significant savings
                        raw_text = base64.b64encode(compressed_data).decode('ascii')
                        compressed = True
                        logger.info(f"Compressed response from {response_size} to {len(compressed_data)} bytes")
                
                # Get usage metadata
                usage = None
                if hasattr(response, 'usage_metadata'):
                    usage = {
                        "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', None),
                        "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', None),
                        "total_tokens": getattr(response.usage_metadata, 'total_token_count', None),
                    }
                
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                return {
                    "request_id": request_id,
                    "raw_text": raw_text,
                    "compressed": compressed,
                    "usage": usage or {"total_tokens": len(raw_text) // 4},  # Rough estimate
                    "duration_seconds": duration
                }
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                logger.error(f"Gemini API error after {duration:.2f}s: {e}")
                raise
        
        result = await _generate()
        
        logger.info(
            f"Gemini generation completed - Request: {request_id}, "
            f"Duration: {result['duration_seconds']:.2f}s, "
            f"Tokens: {result['usage']['total_tokens']}, "
            f"Compressed: {result['compressed']}"
        )
        
        return result
    
    def _truncate_json_safely(self, json_str: str, max_bytes: int) -> str:
        """Truncate JSON string at a safe boundary"""
        # Simple approach: truncate and try to close open structures
        truncated = json_str[:max_bytes]
        
        # Count open braces/brackets
        open_braces = truncated.count('{') - truncated.count('}')
        open_brackets = truncated.count('[') - truncated.count(']')
        
        # Close them
        truncated += ']' * open_brackets + '}' * open_braces
        
        return truncated
    
    def _build_iep_prompt(
        self,
        student_data: Dict[str, Any],
        template_data: Dict[str, Any],
        previous_ieps: Optional[List[Dict]] = None,
        previous_assessments: Optional[List[Dict]] = None
    ) -> str:
        """Build structured prompt for IEP generation"""
        
        # Import schema for validation
        from ..schemas.gemini_schemas import GeminiIEPResponse
        
        schema_json = GeminiIEPResponse.model_json_schema()
        
        # Create example for better compliance
        example_response = {
            "student_info": {
                "name": "John Doe",
                "dob": "2015-03-15",
                "class": "Grade 5",
                "date_of_iep": "2025-01-15"
            },
            "long_term_goal": "Student will demonstrate grade-level proficiency in reading comprehension and mathematical reasoning by the end of the academic year.",
            "short_term_goals": "By June 2025, student will accurately decode multisyllabic words with 85% accuracy. By December 2025, student will solve two-step word problems with 80% accuracy.",
            "oral_language": {
                "receptive": "Student will follow multi-step directions with 90% accuracy",
                "expressive": "Student will use complete sentences to express ideas clearly",
                "recommendations": "Provide visual cues and allow extra processing time for complex instructions"
            },
            "reading": {
                "familiar": "Student will read familiar grade-level texts with 95% accuracy",
                "unfamiliar": "Student will apply decoding strategies to read unfamiliar words",
                "comprehension": "Student will identify main ideas and supporting details in texts"
            },
            "spelling": {
                "goals": "Student will spell grade-level words correctly in writing assignments with 80% accuracy"
            },
            "writing": {
                "recommendations": "Use graphic organizers for pre-writing, provide sentence starters, allow verbal rehearsal before writing"
            },
            "concept": {
                "recommendations": "Use concrete manipulatives and visual models to support abstract concept development"
            },
            "math": {
                "goals": "Student will solve grade-appropriate math problems with 85% accuracy",
                "recommendations": "Provide step-by-step problem-solving templates and allow use of calculator for computation"
            },
            "services": {
                "special_education": "Resource room support 5 hours per week for reading and math",
                "related_services": ["Speech therapy 30 minutes weekly", "Occupational therapy consultation monthly"],
                "accommodations": [
                    "Extended time (1.5x) for tests",
                    "Preferential seating near instruction",
                    "Break tasks into smaller segments",
                    "Provide written and verbal instructions",
                    "Use of graphic organizers"
                ],
                "frequency": "Daily special education support during core academic periods"
            },
            "generation_metadata": {
                "generated_at": "2025-01-15T10:30:00Z",
                "schema_version": "1.0",
                "model": "gemini-2.5-flash"
            }
        }
        
        prompt = f"""You are an expert special education specialist creating an IEP (Individualized Education Program).

CRITICAL INSTRUCTIONS:
1. You MUST respond with ONLY valid JSON that exactly matches the provided schema
2. Do NOT include ANY explanatory text, markdown formatting, code blocks, or comments
3. Output ONLY the JSON object - nothing before or after it
4. Ensure all quotes and special characters are properly escaped
5. Follow the exact structure shown in the example

ASSESSMENT DATA FOR EDUCATIONAL ANALYSIS:
Current Performance: {student_data.get('current_achievement', 'Not provided')}
Identified Strengths: {student_data.get('strengths', 'Not provided')}
Areas Needing Support: {student_data.get('areas_for_growth', 'Not provided')}
Learning Profile: {student_data.get('learning_profile', 'Not provided')}

🔥 REAL ASSESSMENT DATA (Use this specific data to create evidence-based IEP content):
{self._format_assessment_data_for_prompt(student_data)}

STUDENT PROFILE (USE EXACTLY AS PROVIDED - DO NOT CHANGE):
Name: {student_data.get('student_name', 'Student')}
Grade: {student_data.get('grade_level', 'Not specified')} (CRITICAL: Use this exact grade level)
Disability: {student_data.get('disability_type', 'Not specified')}
Case Manager: {student_data.get('case_manager_name', 'Not specified')}

CRITICAL INSTRUCTION: The student is in grade {student_data.get('grade_level', 'Not specified')}. 
DO NOT change this grade level. All content must be appropriate for grade {student_data.get('grade_level', 'Not specified')} standards and expectations.

TEMPLATE STRUCTURE:
{json.dumps(template_data, indent=2)}

{f"PREVIOUS IEPS (for context): {json.dumps(previous_ieps, indent=2)}" if previous_ieps else ""}
{f"RECENT ASSESSMENTS: {json.dumps(previous_assessments, indent=2)}" if previous_assessments else ""}

REQUIRED JSON SCHEMA:
{json.dumps(schema_json, indent=2)}

EXAMPLE OF VALID RESPONSE:
{json.dumps(example_response, indent=2)}

Generate a comprehensive, individualized IEP that:
- Uses SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound)
- Includes specific, actionable accommodations
- Is appropriate for the student's grade level and disability
- Uses professional educational language
- Fills ALL required fields with meaningful content

CRITICAL CONTENT REQUIREMENTS:
- NEVER use placeholder text like "To be determined", "Not specified", "Student", or generic descriptions
- USE THE ACTUAL STUDENT NAME, GRADE, AND SPECIFIC DETAILS provided in the student information
- Generate 2000-5000 characters of detailed content for each major section
- Include specific examples, strategies, and measurable criteria
- Create comprehensive, professional IEP content that would be used in real educational settings
- Each section should be detailed enough to guide actual instruction and support

CRITICAL EDUCATIONAL DOMAIN CONSTRAINTS:
- DO NOT generate, modify, or confabulate any personal details about the student (name, interests, background)
- USE PROVIDED student data exactly as given - do not expand or embellish personal information
- FOCUS EXCLUSIVELY on educational domain transformations: assessment data → educational objectives
- TRANSFORM assessment data into professional educational language and measurable goals
- CONNECT provided strengths/needs to evidence-based instructional strategies and accommodations
- REFERENCE grade-level standards and educational frameworks appropriate to the student's grade
- ANALYZE educational implications of assessment data without adding personal details
- SYNTHESIZE assessment information into professional present levels and educational recommendations
- LINK assessment findings to specific, measurable IEP goals and objectives
- PROVIDE educational analysis and professional recommendations, not personal storytelling

CONTENT DEPTH EXPECTATIONS:
- Long-term goals: 1500+ characters with detailed measurable outcomes based on grade-level standards
- Short-term goals: 2500+ characters with multiple specific objectives that build toward annual goals
- Oral language: 3000+ characters covering receptive, expressive, and evidence-based recommendations
- Reading sections: 2000+ characters each analyzing reading skills with grade-level benchmarks
- Math goals: 2000+ characters connecting math skills to grade-level curriculum standards
- Services: 2000+ characters detailing evidence-based interventions, frequency, and progress monitoring

Output ONLY the JSON object following the exact schema and format shown in the example."""
        
        return prompt
    
    def _format_assessment_data_for_prompt(self, student_data: Dict[str, Any]) -> str:
        """
        🔥 ASSESSMENT DATA BRIDGE: Format real assessment data for LLM prompt
        
        This creates a detailed, structured section with actual test scores,
        composite scores, and educational findings for evidence-based IEP generation.
        """
        
        # Check if we have real assessment data
        test_scores = student_data.get('test_scores', [])
        composite_scores = student_data.get('composite_scores', {})
        educational_objectives = student_data.get('educational_objectives', [])
        recommendations = student_data.get('recommendations', [])
        confidence = student_data.get('assessment_confidence', 0.0)
        
        if not any([test_scores, composite_scores, educational_objectives, recommendations]):
            return "No specific assessment data available. Use general educational analysis."
        
        formatted_sections = []
        
        # Add header with confidence information
        if confidence > 0:
            formatted_sections.append(f"Assessment Data Extraction Confidence: {confidence:.1%}")
        
        # Format individual test scores
        if test_scores:
            formatted_sections.append("\n📊 INDIVIDUAL TEST SCORES:")
            for score in test_scores[:10]:  # Limit to prevent prompt overflow
                score_line = f"  • {score.get('test_name', 'Unknown Test')} - {score.get('subtest_name', 'Unknown Subtest')}: "
                if score.get('standard_score'):
                    score_line += f"Standard Score {score['standard_score']}"
                    if score.get('percentile_rank'):
                        score_line += f" ({score['percentile_rank']}th percentile)"
                    if score.get('score_interpretation'):
                        score_line += f" - {score['score_interpretation']}"
                else:
                    score_line += "Score not available"
                formatted_sections.append(score_line)
        
        # Format composite scores
        if composite_scores:
            formatted_sections.append("\n🧮 COMPOSITE PERFORMANCE AREAS:")
            for area, data in composite_scores.items():
                if isinstance(data, dict):
                    composite_line = f"  • {area}: {data.get('score', 'N/A')}/100"
                    if data.get('interpretation'):
                        composite_line += f" ({data['interpretation']})"
                    if data.get('percentile_equivalent'):
                        composite_line += f" - {data['percentile_equivalent']}th percentile"
                    formatted_sections.append(composite_line)
        
        # Format educational objectives from Document AI
        if educational_objectives:
            formatted_sections.append("\n🎯 EXTRACTED EDUCATIONAL OBJECTIVES:")
            for obj in educational_objectives[:5]:  # Limit to prevent overflow
                if isinstance(obj, dict):
                    obj_line = f"  • Area: {obj.get('area', 'Unknown')}"
                    if obj.get('current_performance'):
                        obj_line += f" | Current: {obj['current_performance'][:100]}..."
                    if obj.get('goal'):
                        obj_line += f" | Goal: {obj['goal'][:100]}..."
                    formatted_sections.append(obj_line)
                elif isinstance(obj, str):
                    formatted_sections.append(f"  • {obj[:150]}...")
        
        # Format recommendations
        if recommendations:
            formatted_sections.append("\n💡 ASSESSMENT RECOMMENDATIONS:")
            for rec in recommendations[:5]:  # Limit recommendations
                if isinstance(rec, str):
                    formatted_sections.append(f"  • {rec[:200]}...")
                elif isinstance(rec, dict) and rec.get('text'):
                    formatted_sections.append(f"  • {rec['text'][:200]}...")
        
        # Add instruction for using this data
        formatted_sections.append("""
🚨 CRITICAL INSTRUCTION: Use the above REAL assessment data to create specific, evidence-based IEP content.
- Reference actual test scores in present levels
- Base goals on identified performance areas and scores
- Use specific recommendations for accommodations and services
- Connect composite scores to appropriate educational objectives
- DO NOT ignore this data - it represents actual student assessment results""")
        
        return "\n".join(formatted_sections)

