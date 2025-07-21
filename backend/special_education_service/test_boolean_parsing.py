#!/usr/bin/env python3
"""
Test boolean parsing for Google Search grounding parameter
"""

import json
from src.schemas.iep_schemas import IEPCreateWithRAG
from uuid import UUID

# Test different ways the frontend might send the boolean
test_payloads = [
    {
        "name": "Boolean true",
        "payload": {
            "student_id": "123e4567-e89b-12d3-a456-426614174000",
            "template_id": "123e4567-e89b-12d3-a456-426614174001",
            "academic_year": "2025-2026",
            "content": {"test": "data"},
            "enable_google_search_grounding": True
        }
    },
    {
        "name": "Boolean false",
        "payload": {
            "student_id": "123e4567-e89b-12d3-a456-426614174000",
            "template_id": "123e4567-e89b-12d3-a456-426614174001",
            "academic_year": "2025-2026",
            "content": {"test": "data"},
            "enable_google_search_grounding": False
        }
    },
    {
        "name": "String 'true'",
        "payload": {
            "student_id": "123e4567-e89b-12d3-a456-426614174000",
            "template_id": "123e4567-e89b-12d3-a456-426614174001",
            "academic_year": "2025-2026",
            "content": {"test": "data"},
            "enable_google_search_grounding": "true"
        }
    },
    {
        "name": "String 'false'",
        "payload": {
            "student_id": "123e4567-e89b-12d3-a456-426614174000",
            "template_id": "123e4567-e89b-12d3-a456-426614174001",
            "academic_year": "2025-2026",
            "content": {"test": "data"},
            "enable_google_search_grounding": "false"
        }
    },
    {
        "name": "Missing field (should default to False)",
        "payload": {
            "student_id": "123e4567-e89b-12d3-a456-426614174000",
            "template_id": "123e4567-e89b-12d3-a456-426614174001",
            "academic_year": "2025-2026",
            "content": {"test": "data"}
        }
    }
]

print("Testing IEPCreateWithRAG schema parsing for enable_google_search_grounding")
print("=" * 70)

for test in test_payloads:
    print(f"\nTest: {test['name']}")
    print(f"Payload: {json.dumps(test['payload'], indent=2)}")
    
    try:
        iep_data = IEPCreateWithRAG(**test['payload'])
        print(f"✅ SUCCESS: enable_google_search_grounding = {iep_data.enable_google_search_grounding}")
        print(f"   Type: {type(iep_data.enable_google_search_grounding)}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("-" * 50)