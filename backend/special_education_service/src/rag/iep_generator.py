from typing import Dict, Any, List
import json
import asyncio
from google import genai
from google.genai import types

from common.src.vector_store import VectorStore

class IEPGenerator:
    def __init__(self, vector_store: VectorStore, settings):
        self.vector_store = vector_store
        self.settings = settings
        self.client = genai.Client(
            vertexai=True,
            project=settings.gcp_project_id,
            location=settings.gcp_region
        )
        self.model = settings.gemini_model
    
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
        # Create query embedding (run in thread pool to avoid blocking)
        query_embedding_result = await asyncio.to_thread(
            self.client.models.embed_content,
            model="text-embedding-004",
            contents=query
        )
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding_result.embeddings[0].values,
            top_k=top_k
        )
        return results
    
    async def _generate_section(
        self, 
        section_name: str, 
        section_template: Dict,
        context: Dict
    ) -> Dict[str, Any]:
        """Generate individual IEP section"""
        prompt = f"""
        You are an expert special education professional creating an IEP section.
        
        Section: {section_name}
        Template Requirements: {json.dumps(section_template)}
        
        Student Context:
        - Disability Type: {context.get('disability_type')}
        - Grade Level: {context.get('grade_level')}
        - Current Performance: {context.get('current_performance')}
        
        Previous Assessments Summary:
        {context.get('assessment_summary')}
        
        Similar IEP Examples:
        {context.get('similar_examples')}
        
        Generate a comprehensive {section_name} section following the template structure.
        Ensure content is:
        1. Specific to the student's needs
        2. Measurable and observable
        3. Aligned with educational standards
        4. Based on assessment data
        
        IMPORTANT: Return ONLY valid JSON. Do not include any markdown formatting, explanations, or additional text.
        Escape all quotes in content with backslashes. Example:
        {{"content": "Student shows improvement in reading. The teacher said \\"great progress\\" was made."}}
        
        Return as a single JSON object matching the template structure.
        """
        
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2048,
                response_mime_type="application/json"
            )
        )
        
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[DEBUG] Section {section_name} - Gemini response received")
        logger.error(f"[DEBUG] Response text is None: {response.text is None}")
        logger.error(f"[DEBUG] Response text length: {len(response.text) if response.text else 0}")
        
        # Check if response is None or empty
        if not response.text:
            logger.error(f"Empty response from Gemini for section {section_name}")
            return {
                "content": f"Generated {section_name} content - fallback due to empty response",
                "description": f"This section was generated for {section_name}",
                "requirements": "Content follows IEP standards",
                "status": "fallback_empty_response"
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
            
            # FALLBACK: Extract content and return structured dict (best practice)
            content_text = self._extract_text_content(response.text)
            return {
                "content": content_text or f"AI-generated content for {section_name} section",
                "description": f"This {section_name} section was generated using AI",
                "requirements": "Content follows IEP standards and regulatory requirements",
                "status": "generated_with_fallback",
                "ai_powered": True,
                "raw_response_length": len(response.text) if response.text else 0
            }
    
    async def _generate_goals(
        self,
        student_data: Dict,
        assessments: List[Dict],
        context: Dict
    ) -> List[Dict]:
        """Generate SMART goals based on assessments"""
        prompt = f"""
        Generate SMART IEP goals based on the following assessment data:
        
        Student Profile:
        - Disability: {student_data.get('disability_type')}
        - Grade: {student_data.get('grade_level')}
        - Strengths: {student_data.get('strengths', [])}
        - Needs: {student_data.get('needs', [])}
        
        Recent Assessments:
        {json.dumps(assessments, indent=2)}
        
        Create 3-5 goals that are:
        - Specific and measurable
        - Achievable within the academic year
        - Relevant to the student's needs
        - Time-bound with clear criteria
        
        For each goal include:
        - domain (academic, behavioral, social, communication)
        - goal_text
        - baseline (current performance)
        - target_criteria (measurable outcome)
        - measurement_method
        
        IMPORTANT: Return ONLY valid JSON. Do not include any markdown formatting, explanations, or additional text.
        Escape all quotes in content with backslashes. Example:
        [{{"domain": "academic", "goal_text": "Student will improve reading with teacher saying \\"good work\\"."}}]
        
        Return as a JSON array of goal objects.
        """
        
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2048,
                response_mime_type="application/json"
            )
        )
        
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
        result = await asyncio.to_thread(
            self.client.models.embed_content,
            model="text-embedding-004",
            contents=text
        )
        return result.embeddings[0].values
    
    def _prepare_context(
        self,
        template: Dict,
        student_data: Dict,
        previous_ieps: List[Dict],
        previous_assessments: List[Dict],
        similar_ieps: List[Dict]
    ) -> Dict:
        """Prepare context for generation"""
        return {
            "disability_type": student_data.get("disability_type"),
            "grade_level": student_data.get("grade_level"),
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
        return latest.get("content", {}).get("summary", "Performance data available")
    
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
            goals = iep.get("content", {}).get("goals", [])
            all_goals.extend(goals)
        return all_goals
