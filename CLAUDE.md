# TLA Educational Platform - Project Information

## Directory Structure
- **Frontend Directory**: `/Users/anshu/Documents/GitHub/v0-tla-front-endv01`
- **Backend Directory**: `/Users/anshu/Documents/GitHub/tlaongcloudv1`

## Quick Start Commands
```bash
# Backend (from /Users/anshu/Documents/GitHub/tlaongcloudv1)
docker-compose down && docker-compose up -d
curl -X POST http://localhost:8001/documents/process

# Frontend (from /Users/anshu/Documents/GitHub/v0-tla-front-endv01)  
npm run dev
```

## System Status ✅ FULLY OPERATIONAL
- **All services operational** with real LLM integration
- **Student management system** fully functional with real-time data
- **18 documents processed** from GCS bucket (betrag-data-test-a)
- **Gemini 2.5 Flash** providing intelligent responses
- **Chat interface** working with document context at http://localhost:3000/chat
- **Dashboard** showing real student counts and statistics
- **6 active students** in the system with full CRUD operations
- **🎉 IEP Template System** - 15+ default templates for AI-powered IEP generation ✅ WORKING
- **🤖 RAG-Powered IEP Creation** - AI-generated personalized IEPs using templates ✅ WORKING
- **📋 Backend Templates Accessible** - Templates visible via direct API calls ✅ WORKING
- **🔧 Frontend Integration** - COMPLETED ✅ Templates integrated with selection UI and error handling

## Architecture
```
Next.js Frontend (:3000) → ADK Host (:8002) → MCP Server (:8001) → ChromaDB + GCS → Gemini 2.5
                        → Special Ed Service (:8005) → PostgreSQL + RAG Templates → Gemini 2.5
```

## Key Configuration
- **GCP Project**: thela002
- **GCS Bucket**: betrag-data-test-a  
- **Model**: gemini-2.5-flash
- **Token Limit**: 8192 (maximized for detailed responses)
- **Environment**: development (using ChromaDB)

## Test Commands
```bash
# Health check
curl http://localhost:8002/health

# Test chat query
curl -X POST http://localhost:8002/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What assessment reports are available?"}'

# Document library
curl http://localhost:8001/documents/list

# Student management
curl http://localhost:8005/api/v1/students  # List all students
curl -X POST http://localhost:8005/api/v1/students \
  -H "Content-Type: application/json" \
  -d '{"student_id": "TEST001", "first_name": "Test", "last_name": "Student", "date_of_birth": "2015-01-01", "grade_level": "5", "disability_codes": ["SLD"], "school_district": "Default District", "school_name": "Default School", "enrollment_date": "2025-06-26"}'

# IEP Template System
curl http://localhost:8005/api/v1/templates  # List all templates
curl http://localhost:8005/api/v1/templates/disability-types  # List disability types

# RAG-Powered IEP Creation
curl -X POST "http://localhost:8005/api/v1/ieps/advanced/create-with-rag?current_user_id=1&current_user_role=teacher" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826",
    "template_id": "3f2f2152-6758-425e-a3ed-3f4c2fd8afb8", 
    "academic_year": "2025-2026",
    "content": {"assessment_summary": "Student shows strengths in visual learning"},
    "meeting_date": "2025-01-15",
    "effective_date": "2025-01-15",
    "review_date": "2026-01-15"
  }'

# Template System Status Check
curl http://localhost:8005/api/v1/templates | jq '.items | length'  # Returns 15+ templates
curl "http://localhost:8005/api/v1/templates?grade_level=K-5&is_active=true" | jq '.items[0].name'  # Filter test
```

## Issues Resolved ✅
1. **Docker dependencies** - All Dockerfiles updated with required packages
2. **Vector store errors** - Environment detection fixed for development/production
3. **GCP authentication** - Credential mounting corrected in docker-compose.yml
4. **Gemini model compatibility** - Updated to 2.5-flash with proper token limits
5. **Document source paths** - Metadata properly shows document names
6. **Frontend routing conflicts** - Conflicting pages renamed to .disabled
7. **Service networking** - All internal service URLs properly configured
8. **Dashboard connection errors** - Fixed port mismatch in .env.local (8006→8005)
9. **Student profile endpoints** - Implemented composite data fetching from available APIs
10. **Dashboard mock data** - Integrated real student data with fallback to mock
11. **Student management flow** - Complete CRUD operations working end-to-end
12. **Real-time updates** - Dashboard widgets show live student counts
13. **🔧 SQLAlchemy Greenlet Errors** - Fixed async session management and object lifecycle
14. **📋 IEP Template System** - Created 15 default templates with comprehensive structure
15. **🤖 RAG Integration** - AI-powered IEP generation working with Gemini 2.5 Flash
16. **📋 Frontend-Backend Template Disconnect** - RESOLVED ✅ Templates now integrated with UI

## Troubleshooting
- If chat returns empty responses: Reprocess documents with `curl -X POST http://localhost:8001/documents/process`
- If Gemini errors occur: Restart services with `docker-compose down && docker-compose up -d`
- If environment variables don't update: Use full restart instead of just restart

### IEP Template System Integration
**Current Status**: Backend templates fully operational, frontend integration needed

**Backend Verification** (All working ✅):
```bash
# Verify templates accessible
curl http://localhost:8005/api/v1/templates | jq '.items | length'  # Returns 15+ templates

# Test template filtering
curl "http://localhost:8005/api/v1/templates?grade_level=K-5&is_active=true" | jq '.items[0].name'

# Verify students exist
curl http://localhost:8005/api/v1/students | jq '.items[0].id'  # Returns UUID

# Test RAG generation (using real IDs)
curl -X POST "http://localhost:8005/api/v1/ieps/advanced/create-with-rag?current_user_id=1" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826",
    "template_id": "3f2f2152-6758-425e-a3ed-3f4c2fd8afb8",
    "academic_year": "2025-2026",
    "content": {"assessment_summary": "Student shows strengths in visual learning"},
    "meeting_date": "2025-01-15",
    "effective_date": "2025-01-15",
    "review_date": "2026-01-15"
  }'
```

**Frontend Integration Issues**:
- Templates are accessible but not visible in UI dropdown
- IEP creation returns "Failed to create IEP: Not Found" error
- Frontend API client in `/lib/api/iep.ts` needs template UI integration

**Frontend Integration Completed** ✅:
1. **Template Selection Dropdown**: Added to IEP generation wizard in Step 1
2. **Enhanced Error Handling**: Improved error messages and validation in API client  
3. **Template Management Page**: Created at `/templates` with search and filtering
4. **RAG Connection**: AI generation now uses selected template for personalized IEPs

**How to Test**:
1. Navigate to http://localhost:3000/students/iep/generator
2. In Step 1, look for "IEP Template Selection" accordion section
3. Select a template based on student's needs
4. Complete the form and click "Generate IEP"
5. View all templates at http://localhost:3000/templates

See STARTUP_CONFIG.md for detailed troubleshooting guide.