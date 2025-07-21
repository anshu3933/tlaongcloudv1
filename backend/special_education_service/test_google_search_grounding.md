# Google Search Grounding for IEP Generation - Testing Guide

## Feature Overview

Google Search grounding has been successfully implemented for IEP generation, providing access to current research, best practices, and up-to-date compliance information during AI-powered IEP creation.

## Implementation Status ✅ COMPLETED

### Core Components Updated:
1. **Pydantic Schemas** (`iep_schemas.py`) - Added `enable_google_search_grounding` parameter
2. **Gemini Client** (`gemini_client.py`) - Added Google Search tools integration
3. **IEP Generator** (`iep_generator.py`) - Added grounding support for section generation
4. **Enhanced IEP Generator** (`metadata_aware_iep_generator.py`) - Added grounding support
5. **IEP Service** (`iep_service.py`) - Updated both RAG paths and section generation
6. **API Router** (`advanced_iep_router.py`) - Updated endpoints and added status endpoint

### API Endpoints Enhanced:
- `POST /api/v1/ieps/advanced/create-with-rag` - Full IEP creation with grounding
- `POST /api/v1/ieps/advanced/{id}/generate-section` - Individual section generation with grounding
- `GET /api/v1/ieps/advanced/google-search-grounding/status` - Feature status and documentation

## Testing Commands

### 1. Check Feature Status
```bash
curl -X GET "http://localhost:8005/api/v1/ieps/advanced/google-search-grounding/status" | jq .
```

Expected response:
```json
{
  "feature": "Google Search Grounding for IEP Generation",
  "status": "available",
  "description": "Enables current research and best practices grounding through Google Search",
  "usage": "Add 'enable_google_search_grounding: true' to IEP creation requests",
  "endpoints_supported": [
    "POST /api/v1/ieps/advanced/create-with-rag",
    "POST /api/v1/ieps/advanced/{id}/generate-section"
  ],
  "benefits": [
    "Access to current research and evidence-based practices",
    "Up-to-date academic standards and compliance requirements",
    "Latest developments in special education interventions",
    "Current best practices for IEP goal writing and SMART goals"
  ]
}
```

### 2. Test IEP Creation with Google Search Grounding
```bash
curl -X POST "http://localhost:8005/api/v1/ieps/advanced/create-with-rag?current_user_id=1&current_user_role=teacher" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826",
    "template_id": "3f2f2152-6758-425e-a3ed-3f4c2fd8afb8",
    "academic_year": "2025-2026",
    "content": {
      "student_name": "Test Student",
      "grade_level": "5",
      "disability_type": "Specific Learning Disability",
      "assessment_summary": {
        "current_achievement": "Reading below grade level",
        "strengths": "Visual learning, strong math reasoning",
        "areas_for_growth": "Reading comprehension, written expression"
      }
    },
    "meeting_date": "2025-01-15",
    "effective_date": "2025-01-15",
    "review_date": "2026-01-15",
    "enable_google_search_grounding": true
  }' | jq .
```

### 3. Test Section Generation with Grounding
```bash
# First, get an existing IEP ID
IEP_ID=$(curl -s "http://localhost:8005/api/v1/ieps/student/c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826" | jq -r '.items[0].id')

# Then generate a section with grounding
curl -X POST "http://localhost:8005/api/v1/ieps/advanced/${IEP_ID}/generate-section?current_user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "section_name": "reading_comprehension",
    "additional_context": {
      "focus_area": "evidence-based reading interventions",
      "grade_level": "5"
    },
    "enable_google_search_grounding": true
  }' | jq .
```

### 4. Compare Results: With vs Without Grounding

#### Without Grounding (baseline):
```bash
curl -X POST "http://localhost:8005/api/v1/ieps/advanced/create-with-rag?current_user_id=1&current_user_role=teacher" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826",
    "template_id": "3f2f2152-6758-425e-a3ed-3f4c2fd8afb8",
    "academic_year": "2025-2026",
    "content": {"student_name": "Test Student", "grade_level": "5"},
    "meeting_date": "2025-01-15",
    "effective_date": "2025-01-15",
    "review_date": "2026-01-15",
    "enable_google_search_grounding": false
  }' > /tmp/iep_without_grounding.json
```

#### With Grounding (enhanced):
```bash
curl -X POST "http://localhost:8005/api/v1/ieps/advanced/create-with-rag?current_user_id=1&current_user_role=teacher" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826",
    "template_id": "3f2f2152-6758-425e-a3ed-3f4c2fd8afb8",
    "academic_year": "2025-2026",
    "content": {"student_name": "Test Student", "grade_level": "5"},
    "meeting_date": "2025-01-15",
    "effective_date": "2025-01-15",
    "review_date": "2026-01-15",
    "enable_google_search_grounding": true
  }' > /tmp/iep_with_grounding.json
```

#### Compare Results:
```bash
echo "=== WITHOUT GROUNDING ==="
jq '.content.reading.recommendations' /tmp/iep_without_grounding.json

echo "=== WITH GROUNDING ==="
jq '.content.reading.recommendations' /tmp/iep_with_grounding.json
```

## Expected Enhancements with Grounding

When `enable_google_search_grounding: true` is set, the generated IEPs should include:

1. **Current Research References**: More up-to-date evidence-based practices
2. **Recent Legal Requirements**: Latest IDEA compliance and state regulations
3. **Modern Interventions**: Current special education methodologies and tools
4. **Updated Standards**: Current grade-level academic standards and benchmarks
5. **Best Practices**: Latest IEP writing guidelines and SMART goal frameworks

## Monitoring and Logs

Look for these log messages to confirm grounding is working:

```
🌐 Enabling Google Search grounding for IEP generation
🌐 [BACKEND-ROUTER] Google Search grounding enabled for this request
🌐 Enabling Google Search grounding for section {section_name}
```

## Performance Considerations

- **Response Time**: Grounding may add 10-30 seconds to generation time due to search queries
- **Token Usage**: May increase token consumption due to additional context from search results
- **Quality**: Should provide more current and comprehensive content

## Troubleshooting

### Common Issues:
1. **API Key**: Ensure GEMINI_API_KEY is properly configured for Google Search
2. **Permissions**: Verify API key has access to Google Search grounding features
3. **Rate Limits**: Google Search grounding may have additional rate limits

### Debug Commands:
```bash
# Check service health
curl http://localhost:8005/health

# Check logs for grounding messages
tail -f server_final.log | grep "🌐"

# Verify API key is configured
curl -X GET "http://localhost:8005/api/v1/ieps/advanced/google-search-grounding/status"
```

## Integration with Frontend

To integrate with the frontend, add a toggle/checkbox to the IEP generation form:

```jsx
<input
  type="checkbox"
  id="enableGrounding"
  checked={enableGoogleSearchGrounding}
  onChange={(e) => setEnableGoogleSearchGrounding(e.target.checked)}
/>
<label htmlFor="enableGrounding">
  Enable Google Search Grounding for current research and best practices
</label>
```

Then include in the API request:
```javascript
const response = await fetch('/api/v1/ieps/advanced/create-with-rag', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ...iepData,
    enable_google_search_grounding: enableGoogleSearchGrounding
  })
});
```

## Feature Status: ✅ PRODUCTION READY

The Google Search grounding feature is fully implemented and ready for production use. All endpoints support the grounding parameter, and both enhanced and legacy RAG systems have been updated to support this functionality.