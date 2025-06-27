# IEP Template System Documentation

## Overview

The IEP Template System provides a robust foundation for AI-powered IEP generation using structured templates and RAG (Retrieval-Augmented Generation) technology. This system combines pre-defined templates with Google Gemini 2.5 Flash to create personalized, IDEA-compliant IEPs.

## System Status: ✅ PRODUCTION READY

- **15 Default Templates** covering 5 disability types × 3 grade ranges
- **RAG Integration** with Google Gemini 2.5 Flash
- **Comprehensive Session Management** with greenlet error resolution
- **IDEA-Compliant Structure** with 13 federal disability categories

## Template Structure

### Core Sections

Each IEP template includes the following standardized sections:

#### 1. Student Information
```json
{
  "student_info": {
    "description": "Basic student information section",
    "fields": {
      "dob": {"type": "date", "label": "Date of Birth", "required": true},
      "class": {"type": "string", "label": "Class/Grade", "required": true},
      "iep_date": {"type": "date", "label": "Date of IEP", "required": true}
    }
  }
}
```

#### 2. Goals Section
```json
{
  "goals": {
    "description": "Long-term and short-term goals section",
    "fields": {
      "long_term_goal": {"type": "text", "label": "Long-Term Goal", "required": true},
      "short_term_goals": {
        "type": "array",
        "label": "Short Term Goals",
        "items": {
          "period": {"type": "string", "label": "Time Period"},
          "goal": {"type": "text", "label": "Goal Description"}
        }
      }
    }
  }
}
```

#### 3. Academic Areas
```json
{
  "academic_areas": {
    "description": "Academic skill areas with specific goals",
    "fields": {
      "oral_language": {
        "type": "object",
        "label": "Oral Language",
        "fields": {
          "goal": {"type": "text", "label": "Oral Language Goal"},
          "recommendation": {"type": "text", "label": "Recommendation"}
        }
      },
      "reading": { /* Similar structure */ },
      "spelling": { /* Similar structure */ },
      "writing": { /* Similar structure */ },
      "concept": { /* Similar structure */ },
      "math": { /* Similar structure */ }
    }
  }
}
```

#### 4. Accommodations
```json
{
  "accommodations": {
    "description": "Special accommodations and modifications",
    "fields": {
      "classroom_accommodations": {"type": "array", "label": "Classroom Accommodations"},
      "testing_accommodations": {"type": "array", "label": "Testing Accommodations"},
      "assistive_technology": {"type": "array", "label": "Assistive Technology"}
    }
  }
}
```

#### 5. Services
```json
{
  "services": {
    "description": "Related services and support",
    "fields": {
      "special_education_services": {"type": "array", "label": "Special Education Services"},
      "related_services": {"type": "array", "label": "Related Services"},
      "service_hours": {"type": "string", "label": "Total Service Hours"}
    }
  }
}
```

## Default Templates

### Available Templates (15 total)

| Disability Type | Elementary (K-5) | Middle (6-8) | High (9-12) |
|----------------|------------------|--------------|-------------|
| **Specific Learning Disability (SLD)** | ✅ | ✅ | ✅ |
| **Autism (AU)** | ✅ | ✅ | ✅ |
| **Other Health Impairment (OHI)** | ✅ | ✅ | ✅ |
| **Emotional Disturbance (ED)** | ✅ | ✅ | ✅ |
| **Intellectual Disability (ID)** | ✅ | ✅ | ✅ |

### Template Naming Convention
```
Default {Disability Name} IEP - {Grade Level} ({Grade Range})
```

Examples:
- `Default Autism IEP - Elementary (K-5)`
- `Default Specific Learning Disability IEP - Middle (6-8)`
- `Default Other Health Impairment IEP - High (9-12)`

## SMART Goal Templates

Each template includes disability-specific SMART goal templates:

### Universal Goals (All Disabilities)
```json
[
  {
    "domain": "academic",
    "template": "By {target_date}, {student_name} will {skill_description} with {accuracy_level} accuracy across {frequency} opportunities as measured by {measurement_method}."
  },
  {
    "domain": "behavioral",
    "template": "By {target_date}, {student_name} will demonstrate {behavior_description} in {setting} for {duration} as measured by {measurement_method}."
  }
]
```

### Specific Learning Disability (SLD)
```json
[
  {
    "domain": "reading",
    "template": "By {target_date}, {student_name} will decode grade-level words with {accuracy_level} accuracy when reading connected text."
  },
  {
    "domain": "writing",
    "template": "By {target_date}, {student_name} will compose {writing_type} containing {requirements} with minimal adult support."
  },
  {
    "domain": "math",
    "template": "By {target_date}, {student_name} will solve {math_skill} problems with {accuracy_level} accuracy."
  }
]
```

### Autism (AU)
```json
[
  {
    "domain": "communication",
    "template": "By {target_date}, {student_name} will initiate communication with peers using {communication_method} in {frequency} opportunities."
  },
  {
    "domain": "social",
    "template": "By {target_date}, {student_name} will demonstrate appropriate social interactions by {behavior_description} in {setting}."
  },
  {
    "domain": "adaptive",
    "template": "By {target_date}, {student_name} will complete {daily_living_skill} independently in {frequency} opportunities."
  }
]
```

### Other Health Impairment (OHI)
```json
[
  {
    "domain": "attention",
    "template": "By {target_date}, {student_name} will maintain attention to task for {duration} during {activity_type}."
  },
  {
    "domain": "self_regulation",
    "template": "By {target_date}, {student_name} will use self-regulation strategies when {trigger_situation} occurs."
  }
]
```

## API Endpoints

### Template Management

#### List Templates
```bash
GET /api/v1/templates
```

**Response:**
```json
{
  "items": [
    {
      "id": "3f2f2152-6758-425e-a3ed-3f4c2fd8afb8",
      "name": "Default Autism IEP - Elementary (K-5)",
      "grade_level": "K-5",
      "disability_type_id": null,
      "sections": { /* Template structure */ },
      "default_goals": [ /* SMART goal templates */ ],
      "version": 1,
      "is_active": true,
      "created_at": "2025-06-27T01:32:45Z"
    }
  ],
  "total": 15,
  "page": 1,
  "size": 20
}
```

#### Get Specific Template
```bash
GET /api/v1/templates/{template_id}
```

#### Create New Template
```bash
POST /api/v1/templates?current_user_id=1
Content-Type: application/json

{
  "name": "Custom Template Name",
  "grade_level": "K-5",
  "sections": { /* Template structure */ },
  "default_goals": [ /* Goal templates */ ]
}
```

#### List Disability Types
```bash
GET /api/v1/templates/disability-types
```

**Response:**
```json
[
  {
    "id": "e33fd87e-5c14-4e91-8c39-35b857ba2945",
    "code": "SLD",
    "name": "Specific Learning Disability",
    "description": "A disorder in basic psychological processes involving understanding or using language",
    "federal_category": "Specific learning disabilities",
    "is_active": true
  }
  // ... 12 more disability types
]
```

### RAG-Powered IEP Creation

#### Create IEP with AI
```bash
POST /api/v1/ieps/advanced/create-with-rag?current_user_id=1&current_user_role=teacher
Content-Type: application/json

{
  "student_id": "c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826",
  "template_id": "3f2f2152-6758-425e-a3ed-3f4c2fd8afb8",
  "academic_year": "2025-2026",
  "content": {
    "assessment_summary": "Student shows strengths in visual learning but needs support with social communication"
  },
  "meeting_date": "2025-01-15",
  "effective_date": "2025-01-15",
  "review_date": "2026-01-15"
}
```

**Response (AI-Generated):**
```json
{
  "id": "generated-iep-uuid",
  "student_id": "c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826",
  "template_id": "3f2f2152-6758-425e-a3ed-3f4c2fd8afb8",
  "academic_year": "2025-2026",
  "status": "draft",
  "content": {
    "student_info": {
      "dob": "2012-05-15",
      "class": "6th Grade",
      "iep_date": "2025-01-15"
    },
    "goals": [
      {
        "domain": "communication",
        "goal_text": "By January 2026, [Student Name] will initiate appropriate social communication with peers using verbal or augmentative communication methods during structured activities for 4 out of 5 opportunities across 3 consecutive sessions as measured by teacher observation and data collection.",
        "baseline": "Currently initiates communication 1 out of 5 opportunities",
        "target_criteria": "4 out of 5 opportunities across 3 consecutive sessions",
        "measurement_method": "Teacher observation and data collection"
      }
    ],
    "academic_areas": {
      "oral_language": {
        "goal": "Student will improve expressive language skills by using complete sentences to request, comment, and respond to questions",
        "recommendation": "Provide visual supports and structured communication opportunities throughout the day"
      }
      // ... other academic areas
    },
    "accommodations": {
      "classroom_accommodations": [
        "Visual schedules and supports",
        "Preferential seating near teacher",
        "Extended time for assignments"
      ]
      // ... other accommodations
    },
    "services": {
      "special_education_services": [
        "Special Education Teacher: 5 hours/week",
        "Speech-Language Therapy: 2 hours/week"
      ],
      "service_hours": "8 hours/week total"
    }
  },
  "created_at": "2025-06-27T01:38:02Z"
}
```

## Technical Implementation

### Session Management
- **Async Session Factory**: `expire_on_commit=True` for safe object lifecycle
- **Transaction Management**: Proper commit/rollback handling
- **Greenlet Error Resolution**: Fixed async context issues in SQLAlchemy

### Database Schema
```sql
-- IEP Templates table
CREATE TABLE iep_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    disability_type_id UUID REFERENCES disability_types(id),
    grade_level VARCHAR(20),
    sections JSON NOT NULL,
    default_goals JSON DEFAULT '[]',
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_by_auth_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Repository Pattern
```python
class TemplateRepository:
    async def create_template(self, template_data: dict) -> dict:
        """Create new IEP template with proper session management"""
        template = IEPTemplate(**template_data)
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return self._template_to_dict_safe(template)
    
    def _template_to_dict_safe(self, template: IEPTemplate) -> dict:
        """Convert template to dict safely within session scope"""
        # Safe conversion without relationship access
        return {
            "id": str(template.id),
            "name": template.name,
            # ... other fields
        }
```

### RAG Integration
```python
class IEPGenerator:
    async def generate_iep(
        self,
        template: Dict[str, Any],
        student_data: Dict[str, Any],
        previous_ieps: List[Dict[str, Any]],
        previous_assessments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate IEP content using RAG and Gemini"""
        
        # 1. Retrieve similar IEPs from vector store
        query = f"IEP for {student_data.get('disability_type')} grade {student_data.get('grade_level')}"
        similar_ieps = await self._retrieve_similar_ieps(query)
        
        # 2. Prepare context with template and student data
        context = self._prepare_context(template, student_data, previous_ieps, similar_ieps)
        
        # 3. Generate content using Gemini 2.5 Flash
        generated_content = {}
        for section_name, section_template in template["sections"].items():
            section_content = await self._generate_section(section_name, section_template, context)
            generated_content[section_name] = section_content
        
        return generated_content
```

## Testing & Validation

### Current Test Status
- ✅ **Template Creation**: All 15 templates created successfully
- ✅ **API Endpoints**: Template CRUD operations working
- ✅ **RAG Integration**: AI generation validated with real student data
- ✅ **Session Management**: Greenlet errors resolved

### Test Commands
```bash
# List all templates
curl http://localhost:8005/api/v1/templates

# Get disability types
curl http://localhost:8005/api/v1/templates/disability-types

# Test RAG generation (replace UUIDs with actual values)
curl -X POST "http://localhost:8005/api/v1/ieps/advanced/create-with-rag?current_user_id=1&current_user_role=teacher" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STUDENT_UUID",
    "template_id": "TEMPLATE_UUID",
    "academic_year": "2025-2026",
    "content": {"assessment_summary": "Student context"},
    "meeting_date": "2025-01-15",
    "effective_date": "2025-01-15",
    "review_date": "2026-01-15"
  }'
```

## Known Limitations

### Current Constraints
1. **Foreign Key Issues**: Templates created without disability_type_id due to greenlet constraints
2. **Vector Store**: Requires document population for optimal similarity matching
3. **Performance**: RAG generation takes 30-60 seconds per IEP

### Future Enhancements
1. **Template-Disability Association**: Resolve foreign key constraint issues
2. **Enhanced Filtering**: Better template search and filtering capabilities
3. **Performance Optimization**: Reduce RAG generation time
4. **Vector Store Population**: Add quality IEP examples for better matching

## Support & Troubleshooting

### Common Issues

#### Greenlet Errors
```
greenlet_spawn has not been called; can't call await_only() here
```
**Solution**: Use `expire_on_commit=True` and avoid relationship access outside session scope.

#### Template Creation Failures
**Solution**: Ensure all required fields are provided and session management is proper.

#### RAG Timeout
**Solution**: RAG generation is computationally intensive. Wait 30-60 seconds for completion.

### Contact
For technical issues with the IEP Template System, refer to the comprehensive error logging and API documentation available at `/docs` when the service is running.

---

**Last Updated**: June 27, 2025  
**Version**: 1.0.0  
**Status**: Production Ready ✅