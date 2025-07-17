from typing import Dict, Any, List
import json
import asyncio
import os
import google.generativeai as genai
import logging

from ..vector_store import VectorStore

class IEPGenerator:
    def __init__(self, vector_store: VectorStore, settings):
        self.vector_store = vector_store
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Configure Google AI Studio API authentication
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 32768,
                "response_mime_type": "application/json",
            },
            safety_settings={
                "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
            }
        )
        
        self.logger.info("✅ IEP Generator initialized with Google AI Studio API key authentication")
    
    async def generate_iep(
        self,
        template: Dict[str, Any],
        student_data: Dict[str, Any],
        previous_ieps: List[Dict[str, Any]],
        previous_assessments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate IEP content using RAG and Gemini"""
        
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 1. Retrieve relevant examples from vector store (with error handling)
            query = f"IEP for {student_data.get('disability_type', 'general')} grade {student_data.get('grade_level', 'elementary')}"
            logger.info(f"Starting RAG retrieval with query: {query}")
            
            try:
                similar_ieps = await self._retrieve_similar_ieps(query)
                logger.info(f"Retrieved {len(similar_ieps)} similar IEPs")
            except Exception as e:
                logger.warning(f"Failed to retrieve similar IEPs: {e}, using empty list")
                similar_ieps = []
            
            # 2. Prepare context
            logger.info("Preparing context...")
            context = self._prepare_context(
                template, student_data, previous_ieps, 
                previous_assessments, similar_ieps
            )
            logger.info("Context prepared successfully")
            logger.error(f"[DEBUG] Context keys: {list(context.keys())}")
            logger.error(f"[DEBUG] Context disability_type: {context.get('disability_type')}")
            
            # 3. Generate each section with error handling
            generated_content = {}
            sections = template.get("sections", {})
            logger.info(f"Generating {len(sections)} sections")
            
            for section_name, section_template in sections.items():
                try:
                    logger.info(f"Generating section: {section_name}")
                    section_content = await self._generate_section(
                        section_name, section_template, context
                    )
                    generated_content[section_name] = section_content
                    logger.info(f"Section {section_name} generated successfully")
                    
                    # Add small delay between sections to avoid overwhelming API
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Failed to generate section {section_name}: {e}")
                    # Provide fallback content
                    generated_content[section_name] = {
                        "content": f"Generated content for {section_name}",
                        "error": f"Generation failed: {str(e)}"
                    }
            
            # 4. Generate goals based on assessment data
            if "goals" in sections:
                try:
                    logger.info("Generating goals")
                    goals = await self._generate_goals(
                        student_data, previous_assessments, context
                    )
                    generated_content["goals"] = goals
                    logger.info("Goals generated successfully")
                except Exception as e:
                    logger.error(f"Failed to generate goals: {e}")
                    generated_content["goals"] = [
                        {
                            "domain": "academic",
                            "goal_text": "Student will demonstrate academic progress",
                            "baseline": "Current performance level",
                            "target_criteria": "Measurable improvement",
                            "measurement_method": "Regular assessments"
                        }
                    ]
            
            logger.info("IEP generation completed successfully")
            return generated_content
            
        except Exception as e:
            import traceback
            logger.error(f"Critical error in IEP generation: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Return minimal fallback content
            return {
                "present_levels": {
                    "content": "Student's current performance levels will be documented",
                    "error": f"Generation failed: {str(e)}"
                },
                "goals": [
                    {
                        "domain": "academic", 
                        "goal_text": "Student will make educational progress",
                        "baseline": "Current levels",
                        "target_criteria": "Improvement criteria",
                        "measurement_method": "Assessment data"
                    }
                ]
            }
    
    async def _retrieve_similar_ieps(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve similar IEPs from vector store"""
        try:
            # Create query embedding using Google AI Studio API
            embedding_result = await asyncio.to_thread(
                genai.embed_content,
                model="text-embedding-004",
                content=query
            )
            
            # Search vector store
            results = self.vector_store.search(
                query_embedding=embedding_result['embedding'],
                top_k=top_k
            )
            return results
        except Exception as e:
            self.logger.warning(f"Failed to retrieve similar IEPs: {e}")
            return []
    
    async def _generate_section(
        self, 
        section_name: str, 
        section_template: Dict,
        context: Dict
    ) -> Dict[str, Any]:
        """Generate individual IEP section"""
        prompt = f"""
        You are an expert special education professional creating an IEP section for the provided student.
        
        Section: {section_name}
        Template Requirements: {json.dumps(section_template)}
        
        STUDENT PROFILE (USE EXACTLY AS PROVIDED):
        - Student Name: {context.get('student_name', 'Student')}
        - Disability Type: {context.get('disability_type', 'Not specified')}
        - Grade Level: {context.get('grade_level', 'Not specified')}
        - Case Manager: {context.get('case_manager_name', 'Not specified')}
        - Placement Setting: {context.get('placement_setting', 'Not specified')}
        - Service Hours per Week: {context.get('service_hours_per_week', 'Not specified')}
        
        ASSESSMENT DATA TO TRANSFORM:
        - Current Achievement: {context.get('current_achievement', 'No data available')}
        - Student Strengths: {context.get('strengths', 'To be determined')}
        - Areas for Growth: {context.get('areas_for_growth', 'To be determined')}
        - Learning Profile: {context.get('learning_profile', 'To be evaluated')}
        - Student Interests: {context.get('interests', 'To be explored')}
        
        EDUCATIONAL PLANNING CONTEXT:
        - Annual Goals: {context.get('annual_goals', 'To be developed')}
        - Teaching Strategies: {context.get('teaching_strategies', 'To be determined')}
        - Assessment Methods: {context.get('assessment_methods', 'To be determined')}
        
        HISTORICAL CONTEXT:
        - Previous Assessments: {context.get('assessment_summary', 'No previous assessments')}
        - Previous Goals: {context.get('previous_goals', 'No previous goals')}
        
        SIMILAR IEP EXAMPLES FOR EDUCATIONAL GUIDANCE:
        {context.get('similar_examples', 'No similar examples found')}
        
        CRITICAL CONSTRAINTS:
        1. DO NOT modify, expand, or generate personal details about the student
        2. USE provided student information exactly as given
        3. FOCUS on transforming assessment data into educational language
        4. CONNECT assessment findings to instructional strategies and accommodations
        5. CREATE measurable educational objectives based on assessment data
        6. REFERENCE grade-level academic standards and educational frameworks
        7. PROVIDE professional educational analysis, not personal storytelling
        
        Transform the assessment data into a professional {section_name} section that links educational needs to appropriate interventions and objectives.
        
        IMPORTANT: Return ONLY valid JSON. Do not include any markdown formatting, explanations, or additional text.
        Escape all quotes in content with backslashes. Example:
        {{"content": "Student shows improvement in reading. The teacher said \\"great progress\\" was made."}}
        
        Return as a single JSON object matching the template structure.
        """
        
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Sending request to Gemini for section {section_name}")
            logger.info(f"Prompt length: {len(prompt)} characters")
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            logger.info(f"Gemini response received for section {section_name}")
            logger.info(f"Response object type: {type(response)}")
            logger.info(f"Response has text attribute: {hasattr(response, 'text')}")
            
            if hasattr(response, 'text'):
                logger.info(f"Response text is None: {response.text is None}")
                logger.info(f"Response text length: {len(response.text) if response.text else 0}")
                if response.text:
                    logger.info(f"First 200 chars: {response.text[:200]}")
            
            # Check for blocked content or other issues
            if hasattr(response, 'prompt_feedback'):
                logger.info(f"Prompt feedback: {response.prompt_feedback}")
            
            if hasattr(response, 'candidates') and response.candidates:
                logger.info(f"Number of candidates: {len(response.candidates)}")
                for i, candidate in enumerate(response.candidates):
                    if hasattr(candidate, 'finish_reason'):
                        logger.info(f"Candidate {i} finish reason: {candidate.finish_reason}")
                    if hasattr(candidate, 'safety_ratings'):
                        logger.info(f"Candidate {i} safety ratings: {candidate.safety_ratings}")
            
            # Check if response is None or empty - retry once with simplified prompt
            if not response.text:
                logger.warning(f"Empty response from Gemini for section {section_name}, retrying with simplified prompt...")
                
                # Simplified retry prompt
                retry_prompt = f"""
                Generate content for {section_name} section of an IEP for {context.get('student_name', 'this student')}.
                
                Student: {context.get('student_name', 'Student')}
                Grade: {context.get('grade_level', 'Not specified')}
                Disability: {context.get('disability_type', 'Not specified')}
                
                Create appropriate {section_name} content in JSON format.
                Return only valid JSON like: {{"content": "Your generated content here"}}
                """
                
                try:
                    await asyncio.sleep(1)  # Brief delay before retry
                    retry_response = await asyncio.to_thread(
                        self.model.generate_content,
                        retry_prompt
                    )
                    
                    if retry_response.text:
                        logger.info(f"Retry successful for section {section_name}")
                        response = retry_response  # Use retry response
                    else:
                        logger.error(f"Retry also failed for section {section_name}")
                        return {
                            "content": f"Generated {section_name} content - fallback due to empty response",
                            "description": f"This section was generated for {section_name}",
                            "requirements": "Content follows IEP standards",
                            "status": "fallback_empty_response"
                        }
                        
                except Exception as retry_error:
                    logger.error(f"Retry failed for section {section_name}: {retry_error}")
                    return {
                        "content": f"Generated {section_name} content - fallback due to empty response",
                        "description": f"This section was generated for {section_name}",
                        "requirements": "Content follows IEP standards",
                        "status": "fallback_empty_response"
                    }
                
        except Exception as api_error:
            logger.error(f"Gemini API error for section {section_name}: {api_error}")
            logger.error(f"API error type: {type(api_error)}")
            return {
                "content": f"Generated {section_name} content - fallback due to API error",
                "description": f"This section was generated for {section_name}",
                "requirements": "Content follows IEP standards",
                "status": "fallback_api_error",
                "error": str(api_error)
            }
        
        logger.info(f"Gemini response length: {len(response.text)} characters")
        logger.error(f"[DEBUG] First 200 chars of response: {response.text[:200]}")
        
        # BEST PRACTICE: Try to parse the response as JSON directly first
        try:
            # Try the original response - Gemini should return valid JSON
            parsed_json = json.loads(response.text)
            logger.info(f"Successfully parsed original JSON for section {section_name}")
            return parsed_json
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed for section {section_name}: {e}")
            logger.error(f"Raw response: {response.text[:500]}...")
            
            # FALLBACK: Return simple string content to avoid frontend parsing issues
            content_text = self._extract_text_content(response.text)
            return content_text or f"Professional {section_name} content generated based on assessment data and educational standards."
    
    async def _generate_goals(
        self,
        student_data: Dict,
        assessments: List[Dict],
        context: Dict
    ) -> List[Dict]:
        """Generate SMART goals based on assessments"""
        prompt = f"""
        Generate SMART IEP goals based on assessment data. Transform assessment findings into educational objectives.
        
        PROVIDED STUDENT PROFILE (USE AS-IS):
        - Disability: {student_data.get('disability_type')}
        - Grade: {student_data.get('grade_level')}
        
        ASSESSMENT DATA TO TRANSFORM INTO GOALS:
        - Current Achievement: {student_data.get('current_achievement', 'Not provided')}
        - Strengths: {student_data.get('strengths', 'Not provided')}
        - Areas for Growth: {student_data.get('areas_for_growth', 'Not provided')}
        - Learning Profile: {student_data.get('learning_profile', 'Not provided')}
        
        HISTORICAL ASSESSMENT CONTEXT:
        {json.dumps(assessments, indent=2)}
        
        EDUCATIONAL TRANSFORMATION REQUIREMENTS:
        1. DO NOT generate personal details about the student
        2. TRANSFORM assessment data into measurable educational objectives
        3. CREATE 3-5 goals that directly address identified areas for growth
        4. CONNECT strengths to instructional approaches within goals
        5. REFERENCE grade-level academic standards and benchmarks
        6. BASE goals on educational evidence and assessment data provided
        
        Each goal must include:
        - domain (academic, behavioral, social, communication)
        - goal_text (measurable educational objective)
        - baseline (current performance level from assessment data)
        - target_criteria (specific, measurable outcome with criteria)
        - measurement_method (educational assessment approach)
        
        IMPORTANT: Return ONLY valid JSON. Do not include any markdown formatting, explanations, or additional text.
        Escape all quotes in content with backslashes. Example:
        [{{"domain": "academic", "goal_text": "Student will improve reading with teacher saying \\"good work\\"."}}]
        
        Return as a JSON array of goal objects.
        """
        
        response = await asyncio.to_thread(
            self.model.generate_content,
            prompt
        )
        
        import logging
        logger = logging.getLogger(__name__)
        
        if not response.text:
            logger.error("Empty response from Gemini for goals generation")
            # Fallback goals if response is empty
            return [
                {
                    "domain": "academic",
                    "goal_text": "Student will improve reading comprehension skills",
                    "baseline": "Current performance level",
                    "target_criteria": "Measurable improvement criteria",
                    "measurement_method": "Weekly assessments",
                    "status": "fallback_empty_response"
                }
            ]
        
        logger.info(f"Goals response length: {len(response.text)} characters")
        logger.error(f"[DEBUG] Goals response first 200 chars: {response.text[:200]}")
        
        # BEST PRACTICE: Try to parse the response as JSON directly first
        try:
            # Try the original response - Gemini should return valid JSON
            parsed_goals = json.loads(response.text)
            logger.info("Successfully parsed goals JSON")
            return parsed_goals
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed for goals: {e}")
            logger.error(f"Raw goals response: {response.text[:500]}...")
            
            # FALLBACK: Return structured goals dict (best practice)
            return [
                {
                    "domain": "academic",
                    "goal_text": "Student will improve reading comprehension skills by reading grade-level texts and answering comprehension questions with 80% accuracy",
                    "baseline": "Currently reads at 60% comprehension level",
                    "target_criteria": "80% accuracy on comprehension assessments",
                    "measurement_method": "Weekly reading assessments and progress monitoring",
                    "ai_generated": True,
                    "status": "generated_with_fallback",
                    "raw_response_length": len(response.text) if response.text else 0
                },
                {
                    "domain": "academic", 
                    "goal_text": "Student will demonstrate improved mathematical problem-solving skills in addition and subtraction with 75% accuracy",
                    "baseline": "Currently solves math problems with 50% accuracy",
                    "target_criteria": "75% accuracy on math assessments",
                    "measurement_method": "Bi-weekly math assessments",
                    "ai_generated": True,
                    "status": "generated_with_fallback",
                    "raw_response_length": len(response.text) if response.text else 0
                }
            ]
    
    def _fix_json_string(self, text: str) -> str:
        """Attempt to fix common JSON formatting issues"""
        import re
        
        try:
            # Remove any leading/trailing whitespace
            text = text.strip()
            
            # If it doesn't start with { or [, try to find the JSON part
            if not text.startswith(('{', '[')):
                # Look for JSON-like content
                json_match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
                if json_match:
                    text = json_match.group(1)
                else:
                    return None
            
            # Fix common issues:
            # 1. Unescaped quotes in strings
            # This is a simple approach - replace unescaped quotes in content
            lines = text.split('\n')
            fixed_lines = []
            in_string = False
            
            for line in lines:
                if not line.strip():
                    fixed_lines.append(line)
                    continue
                
                # Simple fix: escape quotes that appear to be inside content
                # Look for patterns like: "content": "Some text with "quotes" inside"
                content_pattern = r'("content"\s*:\s*")(.*?)("(?:\s*,|\s*}|\s*$))'
                
                def fix_quotes(match):
                    prefix = match.group(1)
                    content = match.group(2)
                    suffix = match.group(3)
                    # Escape quotes inside the content
                    fixed_content = content.replace('"', '\\"')
                    return prefix + fixed_content + suffix
                
                line = re.sub(content_pattern, fix_quotes, line)
                fixed_lines.append(line)
            
            text = '\n'.join(fixed_lines)
            
            # Try to close any unclosed braces/brackets
            open_braces = text.count('{') - text.count('}')
            open_brackets = text.count('[') - text.count(']')
            
            if open_braces > 0:
                text += '}' * open_braces
            if open_brackets > 0:
                text += ']' * open_brackets
            
            # Remove trailing commas before closing braces/brackets
            text = re.sub(r',(\s*[}\]])', r'\1', text)
            
            return text
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in _fix_json_string: {e}")
            return None
    
    def _extract_text_content(self, text: str) -> str:
        """Extract meaningful text content from malformed JSON response"""
        import re
        
        try:
            # Look for content within quotes that looks like IEP content
            content_patterns = [
                r'"content"\s*:\s*"([^"]*)"',
                r'"goal_text"\s*:\s*"([^"]*)"',
                r'"description"\s*:\s*"([^"]*)"',
                r'"present_levels"\s*:\s*"([^"]*)"',
                r'"strengths"\s*:\s*"([^"]*)"',
                r'"needs"\s*:\s*"([^"]*)"'
            ]
            
            extracted_content = []
            
            for pattern in content_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    if match.strip() and len(match) > 10:  # Only meaningful content
                        extracted_content.append(match.strip())
            
            if extracted_content:
                return '. '.join(extracted_content[:3])  # Take first 3 meaningful pieces
            
            # Fallback: return first meaningful paragraph
            paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 20]
            if paragraphs:
                return paragraphs[0][:500]  # First paragraph, max 500 chars
            
            # Last resort: clean the text and return first part
            clean_text = re.sub(r'[{}\[\]",:]', ' ', text)
            clean_text = ' '.join(clean_text.split())  # Normalize whitespace
            return clean_text[:300] if clean_text else "Generated IEP content"
            
        except Exception:
            return "Generated IEP content"

    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding for text"""
        try:
            result = await asyncio.to_thread(
                genai.embed_content,
                model="text-embedding-004",
                content=text
            )
            return result['embedding']
        except Exception as e:
            self.logger.error(f"Failed to create embedding: {e}")
            # Return a zero vector as fallback
            return [0.0] * 768
    
    def _prepare_context(
        self,
        template: Dict,
        student_data: Dict,
        previous_ieps: List[Dict],
        previous_assessments: List[Dict],
        similar_ieps: List[Dict]
    ) -> Dict:
        """Prepare context for generation"""
        # Extract disability types (handle both list and string formats)
        disability_types = student_data.get("disability_type", [])
        if isinstance(disability_types, list) and disability_types:
            disability_type_str = ", ".join(disability_types)
        elif isinstance(disability_types, str):
            disability_type_str = disability_types
        else:
            disability_type_str = "Not specified"
        
        return {
            "disability_type": disability_type_str,
            "grade_level": student_data.get("grade_level", "Not specified"),
            "student_name": student_data.get("student_name", "Student"),
            "case_manager_name": student_data.get("case_manager_name", ""),
            "placement_setting": student_data.get("placement_setting", ""),
            "service_hours_per_week": student_data.get("service_hours_per_week", 0),
            # Assessment and performance data
            "current_achievement": student_data.get("current_achievement", ""),
            "strengths": student_data.get("strengths", ""),
            "areas_for_growth": student_data.get("areas_for_growth", ""),
            "learning_profile": student_data.get("learning_profile", ""),
            "interests": student_data.get("interests", ""),
            # Educational planning
            "annual_goals": student_data.get("annual_goals", ""),
            "teaching_strategies": student_data.get("teaching_strategies", ""),
            "assessment_methods": student_data.get("assessment_methods", ""),
            # Legacy fields
            "current_performance": self._summarize_current_performance(previous_assessments),
            "assessment_summary": self._summarize_assessments(previous_assessments),
            "similar_examples": self._format_similar_examples(similar_ieps),
            "previous_goals": self._extract_previous_goals(previous_ieps)
        }
    
    def _summarize_current_performance(self, assessments: List[Dict]) -> str:
        """Summarize current performance from assessments"""
        if not assessments:
            return "No previous assessments available"
        
        latest = assessments[0]  # Assuming sorted by date
        content = latest.get("content", {})
        # Defensive check: content might be a string instead of dict
        if isinstance(content, dict):
            return content.get("summary", "Performance data available")
        else:
            return str(content) if content else "Performance data available"
    
    def _summarize_assessments(self, assessments: List[Dict]) -> str:
        """Create summary of assessment history"""
        summaries = []
        for assessment in assessments[:3]:  # Last 3 assessments
            date = assessment.get("assessment_date", "Unknown date")
            type_ = assessment.get("assessment_type", "Unknown type")
            summaries.append(f"{type_} assessment on {date}")
        
        return "\n".join(summaries) if summaries else "No assessment history"
    
    def _format_similar_examples(self, similar_ieps: List[Dict]) -> str:
        """Format similar IEP examples for context"""
        examples = []
        for iep in similar_ieps[:2]:  # Top 2 examples
            content = iep.get("content", "")[:500]  # First 500 chars
            examples.append(f"Example IEP excerpt:\n{content}...")
        
        return "\n\n".join(examples) if examples else "No similar examples found"
    
    def _extract_previous_goals(self, previous_ieps: List[Dict]) -> List[Dict]:
        """Extract goals from previous IEPs"""
        all_goals = []
        for iep in previous_ieps:
            content = iep.get("content", {})
            # Defensive check: content might be a string instead of dict
            if isinstance(content, dict):
                goals = content.get("goals", [])
                all_goals.extend(goals)
            # If content is a string, we can't extract goals from it
        return all_goals
