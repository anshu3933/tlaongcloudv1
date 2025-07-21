"""
PLOP (Present Levels of Performance) specific schemas
for generating output in the exact format requested by the user.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict

class PLOPSectionWithGrade(BaseModel):
    """PLOP section with current grade (for academic domains)"""
    current_grade: str = Field(..., description="Current performance grade level for this domain from assessment data")
    present_level: str = Field(..., description="Detailed present level of performance description")
    goals: str = Field(..., description="Specific measurable goals for improvement")
    recommendations: str = Field(..., description="Evidence-based recommendations for instruction")

class PLOPSectionWithoutGrade(BaseModel):
    """PLOP section without current grade (for skills like handwriting, grammar, behavior)"""
    present_level: str = Field(..., description="Detailed present level of performance description")
    goals: str = Field(..., description="Specific measurable goals for improvement")
    recommendations: str = Field(..., description="Evidence-based recommendations for instruction")

class PLOPStudentInfo(BaseModel):
    """Student information for PLOP format"""
    name: str = Field(..., description="Student name")
    dob: str = Field(..., description="Date of birth in YYYY-MM-DD format")
    class_: str = Field(..., alias="class", min_length=1, max_length=20, description="Current grade level from assessment")
    date_of_iep: str = Field(..., description="IEP date in YYYY-MM-DD format")

class PLOPIEPResponse(BaseModel):
    """
    PLOP (Present Levels of Performance) IEP Response Schema
    
    This schema generates content in the exact format:
    
    Section Name
    Current Grade: Grade X (where applicable)
    Present Level of Performance: [detailed description]
    Goals: [specific goals]
    Recommendations: [evidence-based recommendations]
    """
    
    # Student information (required)
    student_info: PLOPStudentInfo = Field(..., description="Student demographic information")
    
    # Academic domains with grade levels
    oral_language: PLOPSectionWithGrade = Field(..., description="Oral Language – Receptive and Expressive")
    reading_familiar: PLOPSectionWithGrade = Field(..., description="Reading – Familiar")
    reading_unfamiliar: PLOPSectionWithGrade = Field(..., description="Reading - Unfamiliar")
    reading_comprehension: PLOPSectionWithGrade = Field(..., description="Reading Comprehension")
    spelling: PLOPSectionWithGrade = Field(..., description="Spelling")
    writing: PLOPSectionWithGrade = Field(..., description="Writing")
    concept: PLOPSectionWithGrade = Field(..., description="Concept")
    math: PLOPSectionWithGrade = Field(..., description="Math")
    
    # Skills without grade levels
    handwriting: PLOPSectionWithoutGrade = Field(..., description="Handwriting")
    grammar: PLOPSectionWithoutGrade = Field(..., description="Grammar")
    behaviour: PLOPSectionWithoutGrade = Field(..., description="Behaviour")
    
    # Optional grounding metadata (if Google Search is enabled)
    grounding_metadata: Optional[dict] = Field(None, description="Google Search grounding metadata")
    
    class Config:
        extra = 'allow'  # Allow additional fields for flexibility
        
    @classmethod
    def get_example(cls):
        """Get an example of the expected PLOP format"""
        return {
            "student_info": {
                "name": "Student Name",
                "dob": "2015-01-01",
                "class": "Grade X",  # X from assessment
                "date_of_iep": "2025-01-21"
            },
            "oral_language": {
                "current_grade": "Grade X",  # X from assessment
                "present_level": "Has age-appropriate vocabulary and can speak in complete sentences. Commits grammatical mistakes during sentence construction. Can understand 2-step instructions, but follows one-step and task-based instructions with reminders. Can convey needs/wants and answer questions on personal information in sentences, though sometimes in phrases. Has adequate general and concept vocabulary, but struggles with English vocabulary. Cannot frame grammatically correct sentences for general conversation. Answers in phrases with prompts for factual and inferential questions from curriculum lessons. Can frame sentences with 3-4 words for familiar keywords. Can narrate 2 sentences with prompts and help on a given topic and picture. Can name classifications (animals/birds/fruits/vehicles etc.).",
                "goals": "Student E will improve grammatical accuracy in sentence construction and general conversation. Student E will consistently follow multi-step instructions without frequent reminders. Student E will improve the ability to answer questions from curriculum lessons in complete sentences independently.",
                "recommendations": "Focus on structured grammar exercises, practice following multi-step instructions, and encourage verbal expression in complete sentences."
            },
            "reading_familiar": {
                "current_grade": "Grade X",  # X from assessment
                "present_level": "Able to read Grade 4 level text with 90% accuracy.",
                "goals": "Student E will maintain 90% accuracy in reading Grade 4 level familiar texts.",
                "recommendations": "Continue providing Grade 4 level familiar texts for practice to maintain current reading proficiency."
            },
            "reading_unfamiliar": {
                "current_grade": "Grade Y",  # Y from assessment if different
                "present_level": "Shows difficulty reading multisyllabic words. Can do sound-letter association for most consonants (80% accuracy). Can identify initial/final sounds of words (80% accuracy). Can identify short vowel sounds (80% accuracy). Can read CVC words, sight words (90% accuracy till List 6, 50% accuracy for 7-11), and words from classification. Can read teacher-made passages with CVC words, sight words, and classification words. Can read initial and final blends with 50% accuracy. Reads keywords from lessons with 50% accuracy and sentences with keywords with 80% accuracy, both with practice. Can read at an independent level. Can read and understand instructions in worksheets but needs reminders to focus. Lacks word attack skills like syllabication and context clues.",
                "goals": "Student E will improve reading accuracy for multisyllabic words. Student E will develop word attack skills, including syllabication and using context clues. Student E will improve reading accuracy for sight words List 7-11 to 90%.",
                "recommendations": "Provide targeted instruction and practice on decoding multisyllabic words, explicitly teach syllabication and context clues, and continue practicing sight words."
            },
            "handwriting": {
                "present_level": "Handwriting is illegible. While letter formation, conforming to lines, and spacing between letters are generally good, Student E joins words. Can perform far point and near point copying.",
                "goals": "Student E will improve the legibility of handwriting. Student E will increase spacing between words to improve overall readability.",
                "recommendations": "Provide regular handwriting practice focusing on appropriate spacing between words."
            }
        }

def get_plop_schema_json():
    """Get the JSON schema for PLOP format"""
    return PLOPIEPResponse.model_json_schema()

def convert_plop_to_standard_format(plop_response: 'PLOPIEPResponse') -> dict:
    """
    Convert PLOP format to standard IEP format for backward compatibility
    with existing service layer code.
    """
    
    # Convert PLOP response to dictionary if needed
    if hasattr(plop_response, 'model_dump'):
        plop_data = plop_response.model_dump()
    else:
        plop_data = plop_response
    
    # Create a standard format response
    # Extract student_info from PLOP data
    student_info_data = plop_data.get('student_info', {})
    standard_response = {
        "student_info": {
            "name": student_info_data.get('name', 'Student'),
            "dob": student_info_data.get('dob', '2015-01-01'),
            "class": student_info_data.get('class', 'Grade TBD'),  # Now comes from actual PLOP response
            "date_of_iep": student_info_data.get('date_of_iep', '2025-01-21')
        },
        "long_term_goal": "Student will demonstrate improvement across all academic domains including oral language, reading, writing, spelling, and mathematics as measured by curriculum-based assessments and standardized evaluations.",
        "short_term_goals": "By June 2025, student will improve performance in identified areas of need as outlined in the domain-specific goals below. Student will achieve 80% accuracy on grade-level tasks across academic domains with appropriate supports and accommodations.",
        "oral_language": {
            "receptive": plop_data.get('oral_language', {}).get('present_level', ''),
            "expressive": plop_data.get('oral_language', {}).get('goals', ''),
            "recommendations": plop_data.get('oral_language', {}).get('recommendations', '')
        },
        "reading": {
            "familiar": plop_data.get('reading_familiar', {}).get('present_level', ''),
            "unfamiliar": plop_data.get('reading_unfamiliar', {}).get('present_level', ''),
            "comprehension": plop_data.get('reading_comprehension', {}).get('present_level', ''),
            "recommendations": plop_data.get('reading_familiar', {}).get('recommendations', '')
        },
        "spelling": {
            "goals": plop_data.get('spelling', {}).get('goals', '')
        },
        "writing": {
            "recommendations": plop_data.get('writing', {}).get('recommendations', '')
        },
        "concept": {
            "recommendations": plop_data.get('concept', {}).get('recommendations', '')
        },
        "math": {
            "goals": plop_data.get('math', {}).get('goals', ''),
            "recommendations": plop_data.get('math', {}).get('recommendations', '')
        },
        "services": {
            "special_education": "Resource room support for identified academic domains based on assessment needs",
            "related_services": ["Speech therapy consultation as needed", "Occupational therapy consultation as needed"],
            "accommodations": [
                "Extended time for assessments",
                "Preferential seating near instruction",
                "Break tasks into smaller segments",
                "Provide written and verbal instructions",
                "Use of graphic organizers and visual supports"
            ],
            "frequency": "Special education support determined by IEP team based on identified needs"
        },
        "generation_metadata": {
            "generated_at": "2025-01-21T10:30:00Z",
            "schema_version": "PLOP-1.0",
            "model": "gemini-2.5-flash",
            "format": "PLOP"
        }
    }
    
    # Add grounding metadata if present
    if 'grounding_metadata' in plop_data:
        standard_response['grounding_metadata'] = plop_data['grounding_metadata']
    
    # Store original PLOP data for display
    standard_response['plop_sections'] = plop_data
    
    return standard_response

def format_plop_output(plop_data: dict) -> str:
    """
    Format PLOP data into the user's requested display format
    
    Input: PLOP data from AI generation
    Output: Formatted string in the exact format requested
    """
    
    output_lines = []
    
    # Define section mappings
    sections = {
        'oral_language': 'Oral Language – Receptive and Expressive',
        'reading_familiar': 'Reading – Familiar', 
        'reading_unfamiliar': 'Reading - Unfamiliar',
        'reading_comprehension': 'Reading Comprehension',
        'spelling': 'Spelling',
        'writing': 'Writing',
        'handwriting': 'Handwriting',
        'grammar': 'Grammar',
        'concept': 'Concept',
        'math': 'Math',
        'behaviour': 'Behaviour'
    }
    
    for section_key, section_title in sections.items():
        if section_key in plop_data:
            section_data = plop_data[section_key]
            
            # Add section title
            output_lines.append(section_title)
            
            # Add current grade if present
            if 'current_grade' in section_data:
                output_lines.append(f"Current Grade: {section_data['current_grade']}")
            
            # Add present level
            output_lines.append(f"Present Level of Performance: {section_data.get('present_level', '')}")
            
            # Add goals
            output_lines.append(f"Goals:")
            output_lines.append(section_data.get('goals', ''))
            
            # Add recommendations
            output_lines.append(f"Recommendations: {section_data.get('recommendations', '')}")
            
            # Add spacing between sections
            output_lines.append("")
    
    return "\n".join(output_lines)