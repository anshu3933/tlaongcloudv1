"""Production-ready Gemini client for IEP generation"""

import google.generativeai as genai
import google.ai.generativelanguage as glm
from google import genai as new_genai
from google.genai import types
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
                "temperature": 0.8,  # INCREASED from 0.7 to 0.8 for more creative grounding
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
        
        # New GenAI client for grounding support
        try:
            self.new_genai_client = new_genai.Client()
            logger.info("🔧 New GenAI client initialized for Google Search grounding")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize new GenAI client: {e}")
            self.new_genai_client = None
        
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
        previous_assessments: Optional[List[Dict]] = None,
        enable_google_search_grounding: bool = False
    ) -> Dict[str, Any]:
        """Generate IEP content with Gemini"""
        
        # Build structured prompt
        prompt = self._build_iep_prompt(
            student_data, 
            template_data, 
            previous_ieps, 
            previous_assessments,
            enable_google_search_grounding
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
                
                # Prepare generation arguments
                generation_args = [prompt]
                generation_kwargs = {}
                
                # Generate content with or without grounding - HERMETICALLY SEPARATED PATHS
                if enable_google_search_grounding and self.new_genai_client:
                    logger.info("🌐 Using new GenAI client for Google Search grounding")
                    
                    # Use the new GenAI API for proper grounding
                    grounding_tool = types.Tool(
                        google_search=types.GoogleSearch()
                    )
                    
                    config = types.GenerateContentConfig(
                        tools=[grounding_tool],
                        temperature=0.8,  # INCREASED from 0.7 to 0.8 for more creative grounding
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=32768
                        # Note: response_mime_type="application/json" is not supported with tools
                    )
                    
                    def generate_with_grounding():
                        return self.new_genai_client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt,
                            config=config
                        )
                    
                    response = await loop.run_in_executor(None, generate_with_grounding)
                    
                elif enable_google_search_grounding:
                    logger.warning("⚠️ Google Search grounding requested but new GenAI client not available, falling back to standard generation")
                    # Use old model with original settings for consistency
                    response = await loop.run_in_executor(
                        None,
                        self.model.generate_content,
                        prompt
                    )
                else:
                    # HERMETICALLY SEALED: Standard generation without grounding - use original model
                    logger.info("📝 Using standard GenerativeAI client (no grounding)")
                    response = await loop.run_in_executor(
                        None,
                        self.model.generate_content,
                        prompt
                    )
                
                # Extract text and clean it
                raw_text = response.text
                
                # Extract grounding metadata if available (for new GenAI client responses)
                grounding_metadata = None
                if enable_google_search_grounding:
                    try:
                        if hasattr(response, 'candidates') and response.candidates:
                            candidate = response.candidates[0]
                            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                                gm = candidate.grounding_metadata
                                grounding_metadata = {
                                    "web_search_queries": getattr(gm, 'web_search_queries', []) or [],
                                    "grounding_chunks": [],
                                    "grounding_supports": []
                                }
                                
                                # Safely extract grounding chunks
                                if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                                    for chunk in gm.grounding_chunks:
                                        if hasattr(chunk, 'web') and chunk.web:
                                            grounding_metadata["grounding_chunks"].append({
                                                "uri": getattr(chunk.web, 'uri', ''),
                                                "title": getattr(chunk.web, 'title', 'Unknown')
                                            })
                                
                                # Safely extract grounding supports
                                if hasattr(gm, 'grounding_supports') and gm.grounding_supports:
                                    for support in gm.grounding_supports:
                                        if hasattr(support, 'segment') and support.segment:
                                            grounding_metadata["grounding_supports"].append({
                                                "segment_text": getattr(support.segment, 'text', ''),
                                                "start_index": getattr(support.segment, 'start_index', 0),
                                                "end_index": getattr(support.segment, 'end_index', 0),
                                                "chunk_indices": getattr(support, 'grounding_chunk_indices', []) or []
                                            })
                                
                                logger.info(f"🌐 Grounding metadata extracted: {len(grounding_metadata.get('grounding_chunks', []))} sources")
                    except Exception as e:
                        logger.warning(f"⚠️ Error extracting grounding metadata: {e}")
                        grounding_metadata = None
                
                # Enhanced JSON extraction for grounded responses
                raw_text = raw_text.strip()
                
                # Remove markdown code blocks if present
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                
                raw_text = raw_text.strip()
                
                # For grounded responses, try to extract JSON from within explanatory text
                if enable_google_search_grounding and self.new_genai_client:
                    json_start = raw_text.find('{')
                    json_end = raw_text.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        potential_json = raw_text[json_start:json_end]
                        try:
                            json.loads(potential_json)
                            raw_text = potential_json
                            logger.info("🌐 Extracted JSON from grounded response")
                        except json.JSONDecodeError:
                            logger.warning("⚠️ Could not extract clean JSON from grounded response, using full text")
                
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
                    
                    # For grounded responses, this might be expected - log but don't fail
                    if enable_google_search_grounding and self.new_genai_client:
                        logger.warning("⚠️ Grounded response contains non-JSON content, which may be expected with Google Search")
                        logger.error(f"Full grounded response: {raw_text}")
                    
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
                
                result = {
                    "request_id": request_id,
                    "raw_text": raw_text,
                    "compressed": compressed,
                    "usage": usage or {"total_tokens": len(raw_text) // 4},  # Rough estimate
                    "duration_seconds": duration
                }
                
                # Add grounding metadata if available
                if grounding_metadata:
                    result["grounding_metadata"] = grounding_metadata
                    logger.info(f"🌐 Google Search grounding successful: {len(grounding_metadata.get('web_search_queries', []))} queries, {len(grounding_metadata.get('grounding_chunks', []))} sources")
                
                return result
                
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
        previous_assessments: Optional[List[Dict]] = None,
        enable_google_search_grounding: bool = False
    ) -> str:
        """Build structured prompt for IEP generation"""
        
        # Check if this is the PLOP template first
        is_plop_template = template_data.get('name', '').startswith('PLOP and Goals')
        
        # Import schema for validation - use PLOP schema if PLOP template
        if is_plop_template:
            from ..schemas.plop_schemas import PLOPIEPResponse
            schema_json = PLOPIEPResponse.model_json_schema()
            
            # Update example response for PLOP format
            example_response = PLOPIEPResponse.get_example()
        else:
            from ..schemas.gemini_schemas import GeminiIEPResponse
            schema_json = GeminiIEPResponse.model_json_schema()
            
            # Create example for better compliance (standard IEP format)
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
                "comprehension": "Student will identify main ideas and supporting details in texts",
                "recommendations": "Implement guided reading strategies, provide pre-reading vocabulary support, use graphic organizers for comprehension"
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
            },
            "grounding_metadata": {
                "google_search_used": True,
                "search_queries_performed": [
                    "evidence-based reading interventions specific learning disability grade 5",
                    "IEP goal writing best practices 2025",
                    "grade 5 academic standards mathematics"
                ],
                "evidence_based_improvements": [
                    {
                        "section": "reading_recommendations",
                        "improvement": "Incorporated latest research on structured literacy approaches for SLD students",
                        "source_type": "research study"
                    },
                    {
                        "section": "accommodations",
                        "improvement": "Added current evidence-based accommodations aligned with Universal Design for Learning principles",
                        "source_type": "best practice"
                    }
                ],
                "current_research_applied": "Applied 2024-2025 research on multi-sensory instruction and evidence-based SLD interventions"
            }
            }
        
        # Add grounding instructions if enabled
        grounding_instructions = ""
        if enable_google_search_grounding:
            disability_type = student_data.get('disability_type', 'the identified disability')
            grade_level = student_data.get('grade_level', 'appropriate')
            grounding_instructions = f"""
🌐 GOOGLE SEARCH GROUNDING ENABLED:
You have access to current research and best practices through Google Search. Use this capability to:
- Research latest evidence-based interventions for {disability_type} (extracted from assessment)
- Find current Grade {grade_level} academic standards and expectations (based on student's assessed grade level)
- Identify recent developments in special education accommodations and services
- Search for current IEP goal writing best practices and SMART goal examples
- Look up evidence-based teaching strategies for identified areas of need
- Find current legal requirements and compliance guidelines for IEP development

🚨 GROUNDING ACKNOWLEDGMENT REQUIREMENTS:
When Google Search grounding is enabled, you MUST:
1. Add a "grounding_metadata" section to your JSON response with the following structure:
   "grounding_metadata": {{
     "google_search_used": true,
     "search_queries_performed": ["list of specific search queries you used"],
     "evidence_based_improvements": [
       {{
         "section": "section_name",
         "improvement": "description of how current research influenced this content",
         "source_type": "research study/best practice/current standard/legal requirement"
       }}
     ],
     "current_research_applied": "brief summary of how current research enhanced the IEP recommendations"
   }}

2. In your content generation, incorporate and acknowledge current research findings
3. Ensure recommendations reflect the most current evidence-based practices for {disability_type} in Grade {grade_level}

🚨 ENHANCED CONTENT REQUIREMENTS WITH GROUNDING:
When Google Search grounding is enabled, you MUST enrich the following sections with additional fields:
- For "reading" section: Add "current" field describing current reading performance based on latest research
- For "spelling" section: Add "current" field with current spelling abilities and "goals" with research-based targets
- For "writing" section: Add "current" field with current writing skills and "goals" with evidence-based objectives
- For "math" section: Add "current" field with current math performance and "goals" aligned with grade standards
- For "concept" section: Add "current" field with concept understanding and "goals" for development

These enriched fields should contain 200-500 characters each and incorporate insights from your Google Search findings.

IMPORTANT: Ground your recommendations in current research while maintaining the JSON response format.
The disability type and grade level above are extracted from the actual assessment data.
"""
        
        if is_plop_template:
            # Special PLOP format instructions
            plop_instructions = f"""
🎯 PLOP (Present Levels of Performance) FORMAT REQUIREMENTS:
This is a PLOP template that requires a SPECIFIC OUTPUT FORMAT. You MUST follow this exact structure:

For each section (oral_language, reading_familiar, reading_unfamiliar, reading_comprehension, spelling, writing, handwriting, grammar, concept, math, behaviour):

REQUIRED STRUCTURE:
{{
  "section_name": {{
    "current_grade": "Grade X" (where applicable),
    "present_level": "Detailed present level description...",
    "goals": "Specific goals for this area...",
    "recommendations": "Evidence-based recommendations..."
  }}
}}

EXAMPLE OUTPUT FORMAT (you MUST follow this exact pattern):
{{
  "oral_language": {{
    "current_grade": "Grade 4",
    "present_level": "Has age-appropriate vocabulary and can speak in complete sentences. Commits grammatical mistakes during sentence construction. Can understand 2-step instructions, but follows one-step and task-based instructions with reminders...",
    "goals": "Student E will improve grammatical accuracy in sentence construction and general conversation. Student E will consistently follow multi-step instructions without frequent reminders...",
    "recommendations": "Focus on structured grammar exercises, practice following multi-step instructions, and encourage verbal expression in complete sentences."
  }},
  "reading_familiar": {{
    "current_grade": "Grade 4",
    "present_level": "Able to read Grade 4 level text with 90% accuracy.",
    "goals": "Student E will maintain 90% accuracy in reading Grade 4 level familiar texts.",
    "recommendations": "Continue providing Grade 4 level familiar texts for practice to maintain current reading proficiency."
  }}
}}

⚠️ CRITICAL: Do NOT use the standard IEP format. Use ONLY the PLOP format shown above.
⚠️ Replace "Student E" with the actual student name: {student_data.get('student_name', 'Student')}
⚠️ Use actual grade levels appropriate to each domain based on assessment data
"""
            format_instructions = plop_instructions
        else:
            format_instructions = ""

        prompt = f"""You are an expert special education specialist creating comprehensive evidence-based IEP content.
{grounding_instructions}
{format_instructions}
CRITICAL INSTRUCTIONS:
1. You MUST respond with ONLY valid JSON that exactly matches the provided schema
2. Do NOT include ANY explanatory text, markdown formatting, code blocks, or comments
3. Output ONLY the JSON object - nothing before or after it
4. Ensure all quotes and special characters are properly escaped
5. Follow the exact structure shown in the example
6. {"INCLUDE grounding_metadata section ONLY if Google Search grounding is enabled above" if enable_google_search_grounding else "Do NOT include grounding_metadata section (Google Search grounding is disabled)"}

🔥 DOCUMENT AI EXTRACTED ASSESSMENT DATA (PRIMARY SOURCE FOR ALL IEP CONTENT):
{self._format_assessment_data_for_prompt(student_data)}

GENERATE evidence-based IEP content using the above Document AI extracted data for:

1. ELIGIBILITY DETERMINATION:
   - Use extracted test scores to justify {student_data.get('disability_type', 'Not specified')} eligibility
   - Reference specific standard scores below 85 or above 115 for cognitive discrepancies
   - Cite composite score patterns indicating educational need
   - Transform percentile ranks into educational impact statements

2. PRESENT LEVELS OF PERFORMANCE:
   - Convert standard scores to performance level descriptions (e.g., "Below Average", "Average", "Above Average")
   - Use grade-equivalent scores from extracted data (e.g., "performs at X.Y grade level")
   - Reference specific subtest results for strengths/weaknesses analysis
   - Include percentile comparisons to same-age peers

3. ANNUAL GOALS DEVELOPMENT:
   - Base measurable outcomes on extracted baseline scores
   - Target improvement using Document AI identified "areas for growth"
   - Incorporate assessment team recommendations into goal structure
   - Use extracted educational objectives as foundation for IEP goals

4. ACCOMMODATIONS JUSTIFICATION:
   - Link specific accommodations to extracted processing weaknesses
   - Reference standardized test conditions used during assessment
   - Connect recommended supports to identified cognitive patterns
   - Justify accommodation intensity based on score severity

5. SERVICES DETERMINATION:
   - Use composite score gaps to determine service minutes/frequency
   - Reference extracted recommendations for service types
   - Connect intervention intensity to assessment confidence levels
   - Base progress monitoring on extracted current performance data

DOCUMENT AI DATA TRANSFORMATION REQUIREMENTS:
- Convert WISC-V/WIAT-IV scores into educational performance statements
- Transform extracted strengths into instructional approach recommendations  
- Use identified concerns to develop targeted intervention strategies
- Reference specific test scores in all performance level descriptions
- Include actual percentile ranks and standard scores in baseline data
- Connect extracted objectives to measurable annual goals

🎯 EXTRACTED STUDENT PROFILE FROM ASSESSMENT DATA:
Name: {student_data.get('student_name', 'Student')}
Grade: {student_data.get('grade_level', 'Not specified')} (CRITICAL: Use this exact grade level from assessment)
Disability: {student_data.get('disability_type', 'Not specified')}
Case Manager: {student_data.get('case_manager_name', 'Not specified')}

CRITICAL GRADE-LEVEL CONSTRAINT: This student is in grade {student_data.get('grade_level', 'Not specified')} based on assessment data. 
ALL IEP content must be appropriate for grade {student_data.get('grade_level', 'Not specified')} academic standards and developmental expectations.

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
        🔥 ENHANCED DOCUMENT AI ASSESSMENT DATA BRIDGE
        
        Formats Document AI extracted assessment data with specific field mapping
        for comprehensive IEP content generation and educational transformation.
        """
        
        # Extract all Document AI processed fields
        test_scores = student_data.get('test_scores', [])
        composite_scores = student_data.get('composite_scores', {})
        educational_objectives = student_data.get('educational_objectives', [])
        recommendations = student_data.get('recommendations', [])
        performance_levels = student_data.get('performance_levels', {})
        areas_of_concern = student_data.get('areas_of_concern', [])
        strengths = student_data.get('strengths', [])
        confidence = student_data.get('assessment_confidence', 0.0)
        
        if not any([test_scores, composite_scores, educational_objectives, recommendations, performance_levels]):
            return "No Document AI assessment data available. Generate content based on student profile and grade-level standards."
        
        formatted_sections = []
        
        # Add Document AI extraction metadata
        formatted_sections.append("🤖 DOCUMENT AI EXTRACTION SUMMARY:")
        if confidence > 0:
            formatted_sections.append(f"  • Extraction Confidence: {confidence:.1%}")
        formatted_sections.append(f"  • Test Scores Identified: {len(test_scores)} scores")
        formatted_sections.append(f"  • Composite Areas: {len(composite_scores)} areas")
        formatted_sections.append(f"  • Educational Objectives: {len(educational_objectives)} objectives")
        formatted_sections.append(f"  • Performance Areas: {len(performance_levels)} areas")
        
        # Format individual test scores with IEP transformation guidance
        if test_scores:
            formatted_sections.append("\n📊 STANDARDIZED TEST SCORES (Transform to Present Levels):")
            for score in test_scores[:12]:  # Increased limit for comprehensive data
                score_line = f"  • {score.get('test_name', 'Unknown Test')} - {score.get('subtest_name', 'Unknown Subtest')}: "
                if score.get('standard_score'):
                    score_line += f"Standard Score {score['standard_score']}"
                    if score.get('percentile_rank'):
                        score_line += f" ({score['percentile_rank']}th percentile)"
                    # Add IEP interpretation guidance
                    std_score = int(score.get('standard_score', 100))
                    if std_score < 85:
                        score_line += " → BELOW AVERAGE (requires intervention)"
                    elif std_score < 115:
                        score_line += " → AVERAGE RANGE (monitor progress)"
                    else:
                        score_line += " → ABOVE AVERAGE (potential strength)"
                    if score.get('score_interpretation'):
                        score_line += f" | {score['score_interpretation']}"
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
        
        # Format performance levels by academic area
        if performance_levels:
            formatted_sections.append("\n📚 CURRENT PERFORMANCE LEVELS BY AREA (Use for Present Levels):")
            for area, level_data in performance_levels.items():
                if isinstance(level_data, dict):
                    level_line = f"  • {area.title()}: {level_data.get('current_level', 'Not specified')}"
                    if level_data.get('additional_notes'):
                        level_line += f" | Notes: {level_data['additional_notes'][0][:100] if level_data['additional_notes'] else ''}..."
                    formatted_sections.append(level_line)
                elif isinstance(level_data, str):
                    formatted_sections.append(f"  • {area.title()}: {level_data[:150]}...")
        
        # Format identified strengths
        if strengths:
            formatted_sections.append("\n💪 IDENTIFIED STRENGTHS (Use for IEP Strengths Section):")
            for strength in strengths[:6]:
                if isinstance(strength, str) and len(strength) > 10:
                    formatted_sections.append(f"  • {strength[:150]}...")
        
        # Format areas of concern
        if areas_of_concern:
            formatted_sections.append("\n⚠️ AREAS OF CONCERN (Target for Goals/Services):")
            for concern in areas_of_concern[:8]:
                if isinstance(concern, str) and len(concern) > 5:
                    formatted_sections.append(f"  • {concern[:150]}...")
        
        # Format assessment team recommendations
        if recommendations:
            formatted_sections.append("\n💡 ASSESSMENT TEAM RECOMMENDATIONS (Transform to Accommodations/Services):")
            for rec in recommendations[:8]:  # Increased limit for comprehensive data
                if isinstance(rec, str):
                    formatted_sections.append(f"  • {rec[:250]}...")
                elif isinstance(rec, dict) and rec.get('text'):
                    formatted_sections.append(f"  • {rec['text'][:250]}...")
        
        # Enhanced instruction for Document AI data transformation
        formatted_sections.append("""
🚨 DOCUMENT AI DATA TRANSFORMATION INSTRUCTIONS:

1. PRESENT LEVELS DEVELOPMENT:
   - Convert standard scores to descriptive performance levels
   - Use actual percentile ranks and grade equivalents 
   - Reference specific test names and subtests in performance descriptions
   - Include identified strengths and concerns in narrative format

2. ANNUAL GOALS CREATION:
   - Base measurable outcomes on current performance level data
   - Target areas showing "below average" performance (<85 standard score)
   - Incorporate extracted educational objectives into goal structure
   - Use composite score gaps to determine appropriate growth targets

3. ACCOMMODATIONS/SERVICES JUSTIFICATION:
   - Link specific accommodations to identified processing weaknesses
   - Reference assessment team recommendations for service types
   - Use score severity (how far below average) to determine service intensity
   - Connect cognitive patterns to instructional accommodation needs

4. EVIDENCE-BASED CONTENT REQUIREMENTS:
   - Include actual test scores, percentiles, and standard scores in all descriptions
   - Reference specific assessment instruments used (WISC-V, WIAT-IV, etc.)
   - Use extracted performance level descriptions verbatim where appropriate
   - Transform recommendations into specific IEP language and implementation details

CRITICAL: This Document AI extracted data represents actual student assessment results. 
All IEP content must be directly tied to and reference this specific assessment data.""")
        
        return "\n".join(formatted_sections)

