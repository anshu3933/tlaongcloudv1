from typing import Dict, Any, List, Optional
import json
from google import genai
from google.genai import types

from common.src.config import get_settings
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
        
        # 1. Retrieve relevant examples from vector store
        query = f"IEP for {student_data.get('disability_type')} grade {student_data.get('grade_level')}"
        similar_ieps = await self._retrieve_similar_ieps(query)
        
        # 2. Prepare context
        context = self._prepare_context(
            template, student_data, previous_ieps, 
            previous_assessments, similar_ieps
        )
        
        # 3. Generate each section
        generated_content = {}
        for section_name, section_template in template["sections"].items():
            section_content = await self._generate_section(
                section_name, section_template, context
            )
            generated_content[section_name] = section_content
        
        # 4. Generate goals based on assessment data
        if "goals" in template["sections"]:
            goals = await self._generate_goals(
                student_data, previous_assessments, context
            )
            generated_content["goals"] = goals
        
        return generated_content
    
    async def _retrieve_similar_ieps(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve similar IEPs from vector store"""
        # Create query embedding
        embedding_model = self.client.models.get_model("text-embedding-004")
        query_embedding = await embedding_model.embed_content(query)
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding.embedding,
            top_k=top_k,
            filters={"type": "iep"}
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
        
        Return as JSON matching the template structure.
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2048,
                response_mime_type="application/json"
            )
        )
        
        return json.loads(response.text)
    
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
        
        Return as JSON array.
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=2048,
                response_mime_type="application/json"
            )
        )
        
        return json.loads(response.text)
    
    async def create_embedding(self, text: str) -> List[float]:
        """Create embedding for text"""
        embedding_model = self.client.models.get_model("text-embedding-004")
        result = await embedding_model.embed_content(text)
        return result.embedding
    
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
