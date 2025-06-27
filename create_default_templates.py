#!/usr/bin/env python3
"""Script to create default IEP templates for common disability types"""

import asyncio
import json
import httpx
from typing import Dict, Any

# Base URL for the Special Education Service
BASE_URL = "http://localhost:8005/api/v1/templates"

def create_template_structure() -> Dict[str, Any]:
    """Create the standard IEP template structure based on user's example"""
    return {
        "student_info": {
            "description": "Basic student information section",
            "fields": {
                "dob": {"type": "date", "label": "Date of Birth", "required": True},
                "class": {"type": "string", "label": "Class/Grade", "required": True},
                "iep_date": {"type": "date", "label": "Date of IEP", "required": True}
            }
        },
        "goals": {
            "description": "Long-term and short-term goals section",
            "fields": {
                "long_term_goal": {"type": "text", "label": "Long-Term Goal", "required": True},
                "short_term_goals": {
                    "type": "array",
                    "label": "Short Term Goals",
                    "items": {
                        "period": {"type": "string", "label": "Time Period (e.g., June – December 2025)"},
                        "goal": {"type": "text", "label": "Goal Description"}
                    }
                }
            }
        },
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
                "reading": {
                    "type": "object", 
                    "label": "Reading",
                    "fields": {
                        "goal": {"type": "text", "label": "Reading Goal"},
                        "recommendation": {"type": "text", "label": "Recommendation"}
                    }
                },
                "spelling": {
                    "type": "object",
                    "label": "Spelling", 
                    "fields": {
                        "goal": {"type": "text", "label": "Spelling Goal"},
                        "recommendation": {"type": "text", "label": "Recommendation"}
                    }
                },
                "writing": {
                    "type": "object",
                    "label": "Writing",
                    "fields": {
                        "goal": {"type": "text", "label": "Writing Goal"},
                        "recommendation": {"type": "text", "label": "Recommendation"}
                    }
                },
                "concept": {
                    "type": "object",
                    "label": "Concept Development",
                    "fields": {
                        "goal": {"type": "text", "label": "Concept Goal"},
                        "recommendation": {"type": "text", "label": "Recommendation"}
                    }
                },
                "math": {
                    "type": "object",
                    "label": "Mathematics",
                    "fields": {
                        "goal": {"type": "text", "label": "Math Goal"},
                        "recommendation": {"type": "text", "label": "Recommendation"}
                    }
                }
            }
        },
        "accommodations": {
            "description": "Special accommodations and modifications",
            "fields": {
                "classroom_accommodations": {"type": "array", "label": "Classroom Accommodations"},
                "testing_accommodations": {"type": "array", "label": "Testing Accommodations"},
                "assistive_technology": {"type": "array", "label": "Assistive Technology"}
            }
        },
        "services": {
            "description": "Related services and support",
            "fields": {
                "special_education_services": {"type": "array", "label": "Special Education Services"},
                "related_services": {"type": "array", "label": "Related Services"},
                "service_hours": {"type": "string", "label": "Total Service Hours"}
            }
        }
    }

def create_default_goals_for_disability(disability_code: str) -> list:
    """Create default goals based on disability type"""
    base_goals = [
        {
            "domain": "academic",
            "template": "By {target_date}, {student_name} will {skill_description} with {accuracy_level} accuracy across {frequency} opportunities as measured by {measurement_method}."
        },
        {
            "domain": "behavioral", 
            "template": "By {target_date}, {student_name} will demonstrate {behavior_description} in {setting} for {duration} as measured by {measurement_method}."
        }
    ]
    
    # Add disability-specific goals
    if disability_code == "SLD":
        base_goals.extend([
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
        ])
    elif disability_code == "AU":
        base_goals.extend([
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
        ])
    elif disability_code == "OHI":
        base_goals.extend([
            {
                "domain": "attention",
                "template": "By {target_date}, {student_name} will maintain attention to task for {duration} during {activity_type}."
            },
            {
                "domain": "self_regulation",
                "template": "By {target_date}, {student_name} will use self-regulation strategies when {trigger_situation} occurs."
            }
        ])
    
    return base_goals

async def get_disability_types():
    """Fetch available disability types"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/disability-types")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch disability types: {response.status_code}")
            return []

async def create_template(template_data: Dict[str, Any], current_user_id: int = 1):
    """Create a single template via API"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}?current_user_id={current_user_id}",
            json=template_data,
            timeout=30.0
        )
        if response.status_code == 201:
            print(f"✅ Created template: {template_data['name']}")
            return response.json()
        else:
            print(f"❌ Failed to create template {template_data['name']}: {response.status_code}")
            print(f"Response: {response.text}")
            return None

async def main():
    """Main function to create default templates"""
    print("🚀 Creating default IEP templates...")
    
    # Get disability types
    disability_types = await get_disability_types()
    if not disability_types:
        print("❌ No disability types found. Exiting.")
        return
    
    # Create disability lookup
    disability_lookup = {dt["code"]: dt for dt in disability_types}
    
    # Target disability types for default templates
    target_disabilities = ["SLD", "AU", "OHI", "ED", "ID"]
    
    # Create templates for common grade level ranges
    grade_ranges = [
        {"level": "Elementary", "grades": "K-5"},
        {"level": "Middle", "grades": "6-8"}, 
        {"level": "High", "grades": "9-12"}
    ]
    
    template_structure = create_template_structure()
    
    created_count = 0
    
    for disability_code in target_disabilities:
        if disability_code not in disability_lookup:
            print(f"⚠️  Disability type {disability_code} not found, skipping...")
            continue
            
        disability = disability_lookup[disability_code]
        
        for grade_range in grade_ranges:
            template_name = f"Default {disability['name']} IEP - {grade_range['level']} ({grade_range['grades']})"
            
            template_data = {
                "name": template_name,
                # Skip disability_type_id for now due to greenlet issue with foreign key validation
                "grade_level": grade_range["grades"],
                "sections": template_structure,
                "default_goals": create_default_goals_for_disability(disability_code)
            }
            
            result = await create_template(template_data)
            if result:
                created_count += 1
    
    print(f"\n🎉 Successfully created {created_count} default IEP templates!")
    print("Templates are now available for RAG-powered IEP generation.")

if __name__ == "__main__":
    asyncio.run(main())