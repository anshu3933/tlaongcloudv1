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
            from google import genai as new_genai
            from google.genai import types as new_genai_types
            
            # Initialize with API key if available
            if self.api_key:
                self.new_genai_client = new_genai.Client(api_key=self.api_key)
                self.new_genai_types = new_genai_types
                logger.info("🔧 New GenAI client initialized with API key for Google Search grounding")
            else:
                # Try with default credentials
                self.new_genai_client = new_genai.Client()
                self.new_genai_types = new_genai_types
                logger.info("🔧 New GenAI client initialized with default credentials for Google Search grounding")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize new GenAI client: {e}")
            self.new_genai_client = None
            self.new_genai_types = None
        
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
                    
                    # Use the correct new GenAI API for grounding (following Google's recommendations)
                    grounding_tool = self.new_genai_types.Tool(
                        google_search=self.new_genai_types.GoogleSearch()
                    )
                    
                    # Configure tool usage to encourage Google Search ONLY when user enables grounding
                    tool_config = None
                    try:
                        # Only force tool usage when user explicitly enables grounding via frontend toggle
                        if hasattr(self.new_genai_types, 'ToolConfig'):
                            tool_config = self.new_genai_types.ToolConfig(
                                function_calling_config=self.new_genai_types.FunctionCallingConfig(
                                    mode='ANY'  # Encourage tool usage when grounding is enabled
                                ) if hasattr(self.new_genai_types, 'FunctionCallingConfig') else None
                            )
                    except Exception as e:
                        logger.warning(f"⚠️ Could not create ToolConfig (SDK may not support it): {e}")
                    
                    # CRITICAL: NO response_mime_type for grounded path due to API constraint
                    # Google Search grounding conflicts with JSON format requirements
                    config = self.new_genai_types.GenerateContentConfig(
                        tools=[grounding_tool],
                        tool_config=tool_config,
                        temperature=1.0,  # Google recommends 1.0 for ideal grounding results when enabled
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=32768
                        # NO response_mime_type - grounding generates text that we'll parse to JSON
                    )
                    
                    # For grounded path, enhance prompt to ensure JSON structure in response
                    grounded_prompt = f"""
{prompt}

CRITICAL INSTRUCTION FOR GROUNDED RESPONSES:
You must provide your response in valid JSON format, surrounded by ```json and ``` markers.
Use Google Search when needed to ground your response with current information.
Structure your JSON response exactly as requested in the original prompt.

Example format:
```json
{{
  "field1": "value1",
  "field2": "value2"
}}
```
"""
                    
                    def generate_with_grounding():
                        return self.new_genai_client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=grounded_prompt,
                            config=config
                        )
                    
                    response = await loop.run_in_executor(None, generate_with_grounding)
                    
                    # Extract grounding metadata from new GenAI client response
                    logger.info("🔍 Extracting grounding metadata from new GenAI response...")
                    
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
                    grounding_metadata = None
                
                # Extract text and clean it
                raw_text = response.text
                
                # Extract grounding metadata if available
                grounding_metadata = None
                if enable_google_search_grounding and self.new_genai_client:
                    try:
                        # For new GenAI client, check if response has candidates with grounding_metadata
                        if hasattr(response, 'candidates') and response.candidates:
                            candidate = response.candidates[0]
                            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                                # Convert to dict using model_dump() method
                                gm = candidate.grounding_metadata
                                gm_dict = gm.model_dump() if hasattr(gm, 'model_dump') else dict(gm)
                                
                                if gm_dict:
                                    grounding_metadata = {
                                        "web_search_queries": gm_dict.get('web_search_queries', []),
                                        "grounding_chunks": [],
                                        "grounding_supports": []
                                    }
                                    
                                    # Extract web search results
                                    if 'grounding_chunks' in gm_dict and gm_dict['grounding_chunks']:
                                        for chunk in gm_dict['grounding_chunks']:
                                            if isinstance(chunk, dict) and 'web' in chunk and chunk['web']:
                                                web_info = chunk['web']
                                                grounding_metadata["grounding_chunks"].append({
                                                    "uri": web_info.get('uri', ''),
                                                    "title": web_info.get('title', '') or web_info.get('domain', 'Unknown')
                                                })
                                    
                                    # Extract grounding supports
                                    if 'grounding_supports' in gm_dict and gm_dict['grounding_supports']:
                                        for support in gm_dict['grounding_supports']:
                                            if isinstance(support, dict) and 'segment' in support:
                                                grounding_metadata["grounding_supports"].append({
                                                    "segment_text": support['segment'].get('text', ''),
                                                    "start_index": support['segment'].get('start_index', 0),
                                                    "end_index": support['segment'].get('end_index', 0),
                                                    "chunk_indices": support.get('grounding_chunk_indices', [])
                                                })
                                    
                                    # Log successful grounding or graceful fallback
                                    query_count = len(grounding_metadata.get('web_search_queries', []))
                                    source_count = len(grounding_metadata.get('grounding_chunks', []))
                                    
                                    if query_count > 0 or source_count > 0:
                                        logger.info(f"🌐 Grounding metadata extracted from new GenAI: {query_count} queries, {source_count} sources")
                                    else:
                                        logger.info("📝 Google Search grounding enabled but model chose not to search (answering from knowledge)")
                                        grounding_metadata = None  # Clear empty metadata
                            else:
                                logger.info("📝 Google Search grounding enabled but no metadata returned (model answered from knowledge)")
                        else:
                            logger.info("📝 Google Search grounding enabled but no candidates returned")
                    except Exception as e:
                        logger.warning(f"⚠️ Error extracting grounding metadata from new GenAI: {e}")
                        import traceback
                        traceback.print_exc()
                        grounding_metadata = None
                
                # Two-Path JSON Processing: Enhanced extraction for grounded responses
                raw_text = raw_text.strip()
                
                if enable_google_search_grounding and self.new_genai_client:
                    # GROUNDED PATH: Parse text response to extract JSON
                    logger.info("🌐 Processing grounded text response for JSON extraction")
                    
                    # Step 1: Remove markdown code blocks
                    if "```json" in raw_text and "```" in raw_text:
                        json_start_marker = raw_text.find("```json")
                        if json_start_marker != -1:
                            json_start = json_start_marker + 7  # Skip "```json"
                            json_end_marker = raw_text.find("```", json_start)
                            if json_end_marker != -1:
                                raw_text = raw_text[json_start:json_end_marker].strip()
                                logger.info("🌐 Extracted JSON from markdown code block")
                    
                    # Step 2: Extract JSON from within explanatory text
                    if not raw_text.startswith('{'):
                        json_start = raw_text.find('{')
                        json_end = raw_text.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            potential_json = raw_text[json_start:json_end]
                            try:
                                # Validate the extracted JSON
                                json.loads(potential_json)
                                raw_text = potential_json
                                logger.info("🌐 Successfully extracted JSON from grounded response text")
                            except json.JSONDecodeError as e:
                                logger.warning(f"⚠️ JSON extraction failed from grounded response: {e}")
                                # Keep original text and try parsing anyway
                    
                else:
                    # NON-GROUNDED PATH: Standard JSON processing (already in JSON format)
                    logger.info("📝 Processing standard JSON response (non-grounded)")
                    
                    # Remove markdown code blocks if present (defensive)
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
                
                # Parse and enhance JSON with grounding metadata
                try:
                    parsed_json = json.loads(raw_text)
                    
                    # Inject grounding metadata into the parsed JSON if available
                    if grounding_metadata and isinstance(parsed_json, dict):
                        parsed_json["google_search_grounding"] = grounding_metadata
                        logger.info(f"🌐 Injected grounding metadata into JSON response with {len(grounding_metadata.get('grounding_chunks', []))} sources")
                        # Convert back to string for the response
                        raw_text = json.dumps(parsed_json, ensure_ascii=False, indent=2)
                    
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
                "class": "{student_grade}",  # Will be replaced with actual grade from assessment
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
                    "evidence-based reading interventions specific learning disability {student_grade}",
                    "IEP goal writing best practices 2025",
                    "{student_grade} academic standards mathematics"
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
        
        # Note: When Google Search grounding is enabled, the native tool will automatically
        # search for relevant information and provide grounding metadata. No manual instructions needed.
        grounding_instructions = ""
        
        if is_plop_template:
            # Special PLOP format instructions
            plop_instructions = f"""
🎯 PLOP (Present Levels of Performance) FORMAT REQUIREMENTS:
This is a PLOP template that generates COMPREHENSIVE, DETAILED content for each domain. You MUST:

1. Generate 500-1500 characters per field (present_level, goals, recommendations)
2. Use specific assessment data, test scores, and percentile information when available
3. Include precise performance metrics and educational terminology
4. Reference specific grade levels, curriculum standards, and intervention strategies
5. Create individualized content that reflects the unique student profile
6. 🆕 PRIORITIZE ENHANCED GOALS BY SUBJECT: Use the "ENHANCED EDUCATIONAL GOALS BY SUBJECT" data from Document AI to derive goals for each PLOP section

REQUIRED STRUCTURE for each section:
{{
  "section_name": {{
    "current_grade": "Grade N where N is the actual performance level from assessment (e.g., 'Grade 2', 'Grade 3')",
    "present_level": "DETAILED description including specific strengths, weaknesses, current performance levels, assessment results, percentiles, observable behaviors, and educational impact...",
    "goals": "SPECIFIC, MEASURABLE goals with timelines, criteria, conditions, and methods of assessment. Include percentage targets, time frames, and observable behaviors...",
    "recommendations": "EVIDENCE-BASED strategies, accommodations, instructional methods, materials, frequency of interventions, and specific approaches tailored to this student's needs..."
  }}
}}

🚨 PLOP GRADE-LEVEL RULES:
- current_grade MUST come from assessment data, NOT student's chronological grade
- If assessment shows "Grade 2 performance in reading", use "Grade 2" for reading sections
- If assessment shows different grades for different skills, use the EXACT grades mentioned
- NEVER assume or generate grade levels not in the assessment

CONTENT QUALITY REQUIREMENTS:
- Present Level: Include specific percentiles, grade equivalents, standard scores when available
- Goals: Must be SMART goals with specific measurement criteria and timelines
- Recommendations: Must include specific instructional strategies, materials, frequency, and research-based interventions
- Use actual student data from assessments rather than generic descriptions
- Reference specific curriculum, teaching methods, and educational frameworks
- Include performance metrics (percentages, time measures, accuracy rates)

🆕 ENHANCED GOALS & GRADE INTEGRATION FOR PLOP:
When enhanced_goals_by_subject data is available, you MUST:
1. 📊 USE EXTRACTED GRADE LEVELS: Use "EXTRACTED GRADE LEVELS FROM ASSESSMENT" for all current_grade fields in PLOP sections
   - If subject-specific grades available (e.g., Reading: Grade 3, Math: Grade 2), use those exact grades for respective sections
   - If only overall grade available, use that for all sections requiring current_grade
   - If no grades extracted, use "Grade TBD" and note in present_level that grade level needs assessment
2. Map extracted goals to appropriate PLOP sections (oral_language, reading_familiar, reading_unfamiliar, etc.)
3. Transform extracted goal text into formal PLOP goals format with specific criteria
4. Use extracted performance indicators as basis for present_level descriptions
5. Incorporate subject-specific recommendations from Document AI into PLOP recommendations fields
6. Reference specific assessment text that supports each goal when available
7. Maintain the comprehensive, detailed format while using actual assessment-derived content

EXAMPLE HIGH-QUALITY OUTPUT (grades from assessment):
{{
  "oral_language": {{
    "current_grade": "Grade X",  # X = actual grade from assessment
    "present_level": "{student_data.get('student_name', 'Student')} demonstrates mixed performance in oral language skills. Receptively, {student_data.get('student_name', 'Student')} can understand and follow 1-2 step directions with 85% accuracy in structured settings, but requires visual cues and repetition for multi-step instructions (3+ steps), achieving only 60% accuracy. Vocabulary knowledge is below grade-level expectations based on curriculum assessments, with strong performance in concrete nouns and action verbs but significant difficulty with abstract concepts, temporal concepts, and inferential language. Expressively, {student_data.get('student_name', 'Student')} uses primarily simple sentence structures with occasional compound sentences, demonstrating grammatical errors in verb tense consistency (40% error rate), subject-verb agreement (30% error rate), and pronoun usage (25% error rate) during informal conversation samples...",
    "goals": "By [specific date], {student_data.get('student_name', 'Student')} will independently follow 3-step oral directions in academic settings with 80% accuracy across 5 consecutive data collection sessions. {student_data.get('student_name', 'Student')} will use grammatically correct sentences (including proper verb tense and subject-verb agreement) in 90% of observed utterances during structured academic discussions over 3 consecutive weeks. {student_data.get('student_name', 'Student')} will demonstrate comprehension of grade-level vocabulary by accurately defining and using 15 new abstract vocabulary words per month with 75% accuracy in multiple contexts...",
    "recommendations": "Implement explicit vocabulary instruction using semantic mapping and visual supports. Provide systematic grammar instruction focusing on verb tense consistency through structured practice activities 3x weekly. Use visual direction cards and checklist strategies to support multi-step direction following. Incorporate oral language practice through structured peer discussions and presentation opportunities. Utilize graphic organizers for expressive language tasks and provide sentence starters for complex responses. Implement daily 10-minute vocabulary review sessions using researched-based techniques such as..."
  }}
}}

⚠️ CRITICAL REQUIREMENTS:
- Use ONLY the PLOP format shown above, NOT standard IEP format
- Replace generic references with actual student name: {student_data.get('student_name', 'Student')}
- Generate 11 comprehensive sections: oral_language, reading_familiar, reading_unfamiliar, reading_comprehension, spelling, writing, handwriting, grammar, concept, math, behaviour
- Each section must contain detailed, individualized content based on assessment data
- Include specific performance data, percentiles, and grade equivalents when available
"""
            format_instructions = plop_instructions
        else:
            format_instructions = ""

        prompt = f"""You are an expert special education specialist creating comprehensive evidence-based IEP content.

🚨 ABSOLUTE GRADE-LEVEL CONSTRAINT 🚨
ALL grade levels in this IEP MUST come EXCLUSIVELY from the assessment data provided.
- DO NOT use any grade levels not explicitly mentioned in the assessment
- If assessment shows different performance levels (e.g., Grade 4 reading, Grade 2 math), use those EXACT levels
- NEVER assume, generate, or impose grade levels beyond what's documented
- All curriculum standards, interventions, and goals must match assessment-specified grades

{grounding_instructions}
{format_instructions}
CRITICAL INSTRUCTIONS:
1. You MUST respond with ONLY valid JSON that exactly matches the provided schema
2. Do NOT include ANY explanatory text, markdown formatting, code blocks, or comments
3. Output ONLY the JSON object - nothing before or after it
4. Ensure all quotes and special characters are properly escaped
5. Follow the exact structure shown in the example

🚨 FIELD LENGTH REQUIREMENTS:
- "class" field in student_info: MAXIMUM 100 characters, use concise grade format (e.g., "Grade 5", "K", "Grade 3-4 Level")
- If grade unknown, use "TBD" or "Grade TBD" - DO NOT use long explanatory text
- All name fields: MAXIMUM 100 characters
- Keep field values concise and professional

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
Date of Birth: {student_data.get('date_of_birth', 'To be provided')}
Grade: TO BE DETERMINED FROM ASSESSMENT DATA ONLY (no default grade level provided)
Disability: {student_data.get('disability_type', 'Not specified')}
Case Manager: {student_data.get('case_manager_name', 'Not specified')}

⚠️ CRITICAL DATE FORMATTING:
- For date_of_birth (dob): Use the ACTUAL date provided above (e.g., "2015-03-15"), NOT the format pattern
- If no date is provided, use "To be provided" exactly as shown
- For date_of_iep: Use today's actual date in YYYY-MM-DD format (e.g., "2025-01-21")

🚨 CRITICAL GRADE-LEVEL CONSTRAINTS - MUST READ 🚨
1. The student's grade level(s) come EXCLUSIVELY from the assessment data provided above
2. DO NOT assume or impose any grade levels not explicitly mentioned in the assessment
3. If the assessment shows different performance levels across domains (e.g., Grade 4 in reading, Grade 2 in math), respect and use those EXACT levels
4. ALL curriculum recommendations must match the grade levels from the assessment data
5. NEVER generate content for grade levels not documented in the assessment
6. When searching for interventions or standards, use ONLY the grade levels from the assessment

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
        
        # Format extracted grade levels (NEW - Grade extraction from assessment)
        enhanced_goals_data = student_data.get('enhanced_goals_by_subject', {})
        if enhanced_goals_data and enhanced_goals_data.get('grade_levels_extracted'):
            grade_data = enhanced_goals_data['grade_levels_extracted']
            formatted_sections.append("\n📊 EXTRACTED GRADE LEVELS FROM ASSESSMENT (Use for PLOP current_grade fields):")
            
            # Overall grade
            if grade_data.get('overall_grade'):
                formatted_sections.append(f"  🎯 Overall Performance Level: Grade {grade_data['overall_grade']}")
            
            # Subject-specific grades
            subject_grades = grade_data.get('subject_specific_grades', {})
            if subject_grades:
                formatted_sections.append(f"  📚 Subject-Specific Grade Levels:")
                for subject, grade_list in subject_grades.items():
                    if grade_list:
                        grades = [g['grade'] for g in grade_list]
                        unique_grades = list(set(grades))
                        formatted_sections.append(f"    • {subject.title()}: Grade {', Grade '.join(unique_grades)}")
            
            # Grade equivalents
            grade_equivalents = grade_data.get('grade_equivalents', [])
            if grade_equivalents:
                formatted_sections.append(f"  📈 Grade Equivalents:")
                for equiv in grade_equivalents[:3]:
                    formatted_sections.append(f"    • {equiv['context']}")
            
            # Confidence
            confidence = grade_data.get('extraction_confidence', 0)
            formatted_sections.append(f"  🔍 Grade Extraction Confidence: {confidence:.1%}")
        
        # 🆕 SIMPLE GRADE EXTRACTION from assessment summary (for direct content)
        # Debug: Check what fields are available
        available_fields = list(student_data.keys())
        formatted_sections.append(f"\n🔍 DEBUG: Available student_data fields: {available_fields}")
        
        assessment_summary = student_data.get('assessment_summary', '') or student_data.get('current_achievement', '')
        formatted_sections.append(f"🔍 DEBUG: Assessment summary: '{assessment_summary[:100] if assessment_summary else 'None found'}...'")
        
        if assessment_summary and not enhanced_goals_data.get('grade_levels_extracted'):
            # Simple grade extraction for assessment summaries provided directly
            simple_grades = self._extract_simple_grades_from_text(assessment_summary)
            if simple_grades:
                formatted_sections.append("\n📊 EXTRACTED GRADE LEVELS FROM ASSESSMENT SUMMARY:")
                for subject, grade in simple_grades.items():
                    formatted_sections.append(f"  • {subject.title()}: Grade {grade}")
                formatted_sections.append("  🔍 Use these grades for appropriate PLOP current_grade fields")
            else:
                # Debug: show what assessment summary was found
                formatted_sections.append(f"\n⚠️ DEBUG: Assessment summary found but no grades extracted from: '{assessment_summary[:100]}...'")
        
        # Format enhanced goals by subject (NEW - Document AI enhancement)  
        if enhanced_goals_data and enhanced_goals_data.get('goals_by_subject'):
            formatted_sections.append("\n🎯 ENHANCED EDUCATIONAL GOALS BY SUBJECT (Use for PLOP Goals):")
            goals_by_subject = enhanced_goals_data['goals_by_subject']
            total_subjects = enhanced_goals_data.get('total_subjects_with_goals', 0)
            formatted_sections.append(f"📊 Total subjects with extracted goals: {total_subjects}")
            
            for subject_key, subject_data in goals_by_subject.items():
                if isinstance(subject_data, dict):
                    subject_name = subject_data.get('subject_name', subject_key.title())
                    total_items = subject_data.get('total_items', 0)
                    formatted_sections.append(f"  • {subject_name}: {total_items} items extracted")
                    
                    # Format goals from text
                    goals_from_text = subject_data.get('goals_from_text', [])
                    if goals_from_text:
                        formatted_sections.append(f"    🎯 Goals ({len(goals_from_text)}):")
                        for goal in goals_from_text[:2]:  # Limit to prevent overflow
                            if isinstance(goal, dict) and goal.get('text'):
                                formatted_sections.append(f"      - {goal['text'][:150]}...")
                    
                    # Format recommendations
                    recommendations = subject_data.get('recommendations', [])
                    if recommendations:
                        formatted_sections.append(f"    💡 Recommendations ({len(recommendations)}):")
                        for rec in recommendations[:2]:  # Limit to prevent overflow
                            if isinstance(rec, dict) and rec.get('text'):
                                formatted_sections.append(f"      - {rec['text'][:150]}...")
                    
                    # Format performance indicators
                    performance_indicators = subject_data.get('performance_indicators', [])
                    if performance_indicators:
                        formatted_sections.append(f"    📊 Performance ({len(performance_indicators)}):")
                        for perf in performance_indicators[:2]:  # Limit to prevent overflow
                            if isinstance(perf, dict) and perf.get('text'):
                                formatted_sections.append(f"      - {perf['text'][:150]}...")
            
            # Format general goals if available
            general_goals = enhanced_goals_data.get('general_goals', [])
            if general_goals:
                formatted_sections.append(f"  📝 General Goals ({len(general_goals)}):")
                for goal in general_goals[:3]:  # Limit to prevent overflow
                    if isinstance(goal, dict) and goal.get('text'):
                        formatted_sections.append(f"    - {goal['text'][:150]}...")
        elif enhanced_goals_data:
            formatted_sections.append(f"\n⚠️ Enhanced goals data present but no goals_by_subject found: {list(enhanced_goals_data.keys())}")
        
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
All IEP content must be directly tied to and reference this specific assessment data.

🆕 ENHANCED GOALS BY SUBJECT UTILIZATION:
If "ENHANCED EDUCATIONAL GOALS BY SUBJECT" data is provided above, you MUST prioritize using this subject-specific goal extraction to inform your IEP content generation. This data represents sophisticated Document AI parsing of educational objectives organized by academic domain, and should be the PRIMARY source for goal development in all relevant IEP sections.""")
        
        return "\n".join(formatted_sections)
    

    def _extract_simple_grades_from_text(self, text: str) -> Dict[str, str]:
        """
        Simple grade extraction from assessment summary text.
        Used when assessment data is provided directly instead of through Document AI.
        """
        import re
        
        if not text:
            return {}
        
        grades = {}
        
        # Simple grade patterns for assessment summaries
        patterns = [
            # Subject-specific patterns
            (r"(?:Grade|grade)\s+([0-9K])\s+reading", "reading"),
            (r"reading\s+(?:at\s+)?(?:Grade|grade)\s+([0-9K])", "reading"),
            (r"(?:Grade|grade)\s+([0-9K])\s+math", "math"),
            (r"math\s+(?:at\s+)?(?:Grade|grade)\s+([0-9K])", "math"),
            (r"(?:Grade|grade)\s+([0-9K])\s+writing", "writing"),
            (r"writing\s+(?:at\s+)?(?:Grade|grade)\s+([0-9K])", "writing"),
            
            # General patterns
            (r"(?:performing|functioning)\s+at\s+(?:Grade|grade)\s+([0-9K])", "overall"),
            (r"(?:demonstrates|shows)\s+(?:Grade|grade)\s+([0-9K])\s+(?:level|performance)", "overall"),
        ]
        
        for pattern, subject in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                grade_num = match.group(1).strip()
                if grade_num.upper() == 'K':
                    grades[subject] = 'K'
                elif grade_num.isdigit():
                    grades[subject] = grade_num
        
        return grades

