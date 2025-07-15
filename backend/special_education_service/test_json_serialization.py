#!/usr/bin/env python3
"""
Test script to verify JSON serialization fix for Document AI responses
"""

import json
from typing import Any

def _make_serializable(data: Any) -> Any:
    """Convert Document AI objects to JSON-serializable format"""
    if hasattr(data, '__dict__'):
        # Handle Document AI objects with attributes
        if hasattr(data, 'text') and hasattr(data, 'confidence'):
            return {
                "text": str(data.text) if data.text else "",
                "confidence": float(data.confidence) if data.confidence else 0.0
            }
        elif hasattr(data, 'normalized_value') and data.normalized_value:
            # Handle NormalizedValue objects
            return {
                "text": str(data.text) if hasattr(data, 'text') and data.text else "",
                "normalized_value": _make_serializable(data.normalized_value)
            }
        else:
            # Generic object conversion
            return {key: _make_serializable(value) for key, value in data.__dict__.items()}
    elif isinstance(data, list):
        return [_make_serializable(item) for item in data]
    elif isinstance(data, dict):
        return {key: _make_serializable(value) for key, value in data.items()}
    elif hasattr(data, '__iter__') and not isinstance(data, (str, bytes)):
        return [_make_serializable(item) for item in data]
    else:
        # Handle primitive types and convert to JSON-serializable
        try:
            # Try to convert to basic types
            if isinstance(data, (int, float, str, bool, type(None))):
                return data
            else:
                return str(data)
        except Exception:
            return str(data)

# Mock Document AI objects for testing
class MockNormalizedValue:
    def __init__(self, text: str, confidence: float):
        self.text = text
        self.confidence = confidence

class MockEntity:
    def __init__(self, text: str, confidence: float, normalized_value: MockNormalizedValue = None):
        self.text = text
        self.confidence = confidence
        self.normalized_value = normalized_value

def test_json_serialization():
    """Test that Document AI objects can be serialized to JSON"""
    
    # Create mock Document AI response with NormalizedValue objects
    mock_response = {
        "text_content": "WISC-V Full Scale IQ: 95",
        "entities": [
            MockEntity("Full Scale IQ", 0.95, MockNormalizedValue("95", 0.98)),
            MockEntity("Verbal Comprehension", 0.85, MockNormalizedValue("92", 0.90))
        ],
        "extracted_scores": [
            {
                "test_name": "WISC-V",
                "subtest_name": "Full Scale IQ",
                "standard_score": 95,
                "extraction_confidence": 0.95,
                "source": "enhanced_pattern"
            }
        ]
    }
    
    print("🧪 Testing JSON serialization of Document AI response...")
    print(f"📊 Original response contains {len(mock_response['entities'])} entities")
    
    # Test serialization
    try:
        serializable_data = _make_serializable(mock_response)
        json_str = json.dumps(serializable_data, indent=2)
        print("✅ Serialization successful!")
        print(f"📄 JSON length: {len(json_str)} characters")
        
        # Test deserialization
        deserialized = json.loads(json_str)
        print("✅ Deserialization successful!")
        print(f"📊 Deserialized response contains {len(deserialized['entities'])} entities")
        
        # Verify specific fields
        first_entity = deserialized['entities'][0]
        print(f"📈 First entity: {first_entity['text']} (confidence: {first_entity['confidence']})")
        
        if 'normalized_value' in first_entity:
            print(f"🎯 Normalized value: {first_entity['normalized_value']['text']} (confidence: {first_entity['normalized_value']['confidence']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Serialization failed: {e}")
        return False

if __name__ == "__main__":
    success = test_json_serialization()
    if success:
        print("\n🎉 JSON serialization fix is working correctly!")
    else:
        print("\n💥 JSON serialization fix needs more work!")