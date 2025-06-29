# LLM Configuration for Special Education Service

## Overview
The Special Education Service integrates with Google Gemini LLM for AI-powered IEP generation. This document explains how to configure and enable/disable the LLM functionality.

## Current Status
The backend has full Google Gemini integration implemented, but the `/api/v1/ieps/advanced/create-with-rag` endpoint can be configured to return mock data or use the real LLM.

## Configuration

### Environment Variables

The following environment variables are already configured in `.env`:

```bash
# Google Cloud AI Configuration
GCP_PROJECT_ID=thela002
GCP_REGION=us-central1
GEMINI_MODEL=gemini-2.5-flash
```

### Enabling/Disabling LLM

To control whether the service uses real LLM or mock data, use the `USE_MOCK_LLM` environment variable:

1. **To use REAL Google Gemini LLM (default):**
   ```bash
   # Don't set USE_MOCK_LLM, or set it to false
   USE_MOCK_LLM=false
   ```

2. **To use MOCK data (for testing/demo):**
   ```bash
   USE_MOCK_LLM=true
   ```

Add this to your `.env` file:
```bash
# LLM Configuration
USE_MOCK_LLM=false  # Set to true for mock data, false for real LLM
```

## Implementation Details

### Files Involved

1. **`src/routers/advanced_iep_router.py`**
   - Contains the `/api/v1/ieps/advanced/create-with-rag` endpoint
   - Now checks `USE_MOCK_LLM` environment variable
   - Returns mock data when `USE_MOCK_LLM=true`
   - Calls real LLM via `iep_service.create_iep_with_rag()` when `USE_MOCK_LLM=false`

2. **`src/rag/iep_generator.py`**
   - Contains the `IEPGenerator` class
   - Implements Google Gemini integration
   - Uses `google.genai` client with Vertex AI
   - Generates IEP content using RAG and templates

3. **`src/services/iep_service.py`**
   - Contains `create_iep_with_rag()` method
   - Orchestrates the IEP creation process
   - Handles database operations and versioning

## API Usage

### Request Example
```bash
POST /api/v1/ieps/advanced/create-with-rag?current_user_id=1&current_user_role=teacher

{
  "student_id": "123e4567-e89b-12d3-a456-426614174000",
  "template_id": "456e4567-e89b-12d3-a456-426614174000",
  "academic_year": "2024-2025",
  "content": {
    "student_info": {
      "name": "John Doe",
      "grade": "5th Grade",
      "disability_type": "Learning Disability"
    }
  },
  "meeting_date": "2024-09-15",
  "effective_date": "2024-09-20",
  "review_date": "2025-03-15"
}
```

### Response (Real LLM)
When `USE_MOCK_LLM=false`, the response will contain AI-generated content from Google Gemini based on:
- Student profile
- Previous IEPs
- Assessment data
- Similar IEPs from vector store

### Response (Mock Data)
When `USE_MOCK_LLM=true`, the response will contain predefined demo data for testing purposes.

## Troubleshooting

### Common Issues

1. **"Failed to create IEP with RAG" error**
   - Check if Google Cloud credentials are properly configured
   - Verify `GCP_PROJECT_ID` is correct
   - Ensure Gemini API is enabled in your GCP project

2. **JSON Serialization Errors**
   - The code now includes UUID to string conversion
   - All responses are made JSON serializable before returning

3. **Empty LLM Responses**
   - The generator includes fallback mechanisms
   - Check logs for specific Gemini API errors

### Logs
Enable debug logging to see detailed LLM interactions:
```python
# Check logs for:
- "Creating IEP with RAG/LLM for student..."
- "Using mock response for IEP creation..."
- "RAG generation completed..."
```

## Next Steps

1. Test with `USE_MOCK_LLM=false` to verify real LLM integration
2. Monitor logs for any Google Gemini API errors
3. Adjust temperature and token limits in `iep_generator.py` if needed
4. Consider implementing caching for similar IEP retrieval