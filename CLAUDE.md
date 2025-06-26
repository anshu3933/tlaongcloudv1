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

## Architecture
```
Next.js Frontend (:3000) → ADK Host (:8002) → MCP Server (:8001) → ChromaDB + GCS → Gemini 2.5
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

## Troubleshooting
- If chat returns empty responses: Reprocess documents with `curl -X POST http://localhost:8001/documents/process`
- If Gemini errors occur: Restart services with `docker-compose down && docker-compose up -d`
- If environment variables don't update: Use full restart instead of just restart

See STARTUP_CONFIG.md for detailed troubleshooting guide.