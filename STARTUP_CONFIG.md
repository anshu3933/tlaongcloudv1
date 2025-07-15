# TLA Educational Platform Startup Configuration

## Directory Paths
- Backend Directory: `/Users/anshu/Documents/GitHub/tlaongcloudv1`
- Frontend Directory: `/Users/anshu/Documents/GitHub/v0-tla-front-endv01`

## 🔥 BULLETPROOF STARTUP PROCEDURE (Updated July 2025)

### Prerequisites
1. **Docker Desktop must be running**
2. **Google Cloud SDK installed and authenticated**
3. **Node.js and npm installed**
4. **Python 3.12 environment with required packages**

### Step 1: GCP Authentication
```bash
gcloud auth application-default login
```

### Step 2: Backend Services Startup
```bash
cd /Users/anshu/Documents/GitHub/tlaongcloudv1

# Clean restart (recommended for consistent state)
docker-compose down
docker-compose up -d

# Wait for services to initialize (about 30 seconds)
sleep 30

# Verify all services are healthy
curl http://localhost:8002/health  # ADK Host
curl http://localhost:8005/health  # Special Ed Service (CRITICAL - Main service)
```

### Step 3: MCP Server Startup (RESTORED)
```bash
cd /Users/anshu/Documents/GitHub/tlaongcloudv1/backend/mcp_server

# Start MCP server with proper configuration
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload &

# Wait for startup
sleep 10

# Verify MCP server is running (may have HTTP response issues but process should be active)
ps aux | grep -E "uvicorn.*8001" | grep -v grep
```

### Step 4: Vector Store Population (COMPLETED)
```bash
cd /Users/anshu/Documents/GitHub/tlaongcloudv1/backend/special_education_service

# Run document processing script (42 documents already populated)
python process_local_ieps.py

# Verify vector store status
python -c "
import chromadb
client = chromadb.PersistentClient(path='./chroma_db')
collection = client.get_collection('rag_documents')
print(f'Vector store contains {collection.count()} documents')
"
```

### Step 5: Frontend Startup
```bash
cd /Users/anshu/Documents/GitHub/v0-tla-front-endv01
npm run dev
```

### Step 5: Verification
- Backend Health: http://localhost:8002/health
- Frontend: http://localhost:3000
- Chat Interface: http://localhost:3000/chat

## 🚨 CRITICAL CONFIGURATION

### GCP Configuration
- **GCP_PROJECT_ID**: `thela002`
- **GCS_BUCKET_NAME**: `betrag-data-test-a`
- **GEMINI_MODEL**: `gemini-2.5-flash` ⚠️ **UPDATED - Use 2.5, not 2.0**
- **GOOGLE_APPLICATION_CREDENTIALS**: Uses Application Default Credentials

### Model Configuration
- **gemini_max_tokens**: `8192` (maximized for detailed responses)
- **gemini_temperature**: `0.4`

### Service Architecture
```
Frontend (Next.js :3000) 
    ↓
ADK Host (:8002) 
    ↓
MCP Server (:8001) ←→ Vector Store (ChromaDB) ←→ GCS Bucket
    ↓
Gemini 2.5 Flash
```

## 🔧 TROUBLESHOOTING GUIDE

### Problem: Chat Returns Mock/Empty Responses
**Root Cause**: Vector store is empty or documents not processed

**Solution**:
```bash
# 1. Clear vector store (if needed)
docker exec tlaongcloudv1-mcp-server-1 rm -rf /app/chroma_db

# 2. Restart MCP server
docker-compose restart mcp-server

# 3. Reprocess documents
curl -X POST http://localhost:8001/documents/process

# 4. Verify documents are loaded
curl -X POST http://localhost:8001/mcp -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": "test", "method": "tools/call", "params": {"name": "retrieve_documents", "arguments": {"query": "assessment", "top_k": 2}}}'
```

### Problem: Gemini Token Limit Errors
**Root Cause**: Max tokens set incorrectly for model version

**Solution**:
1. Verify `gemini_max_tokens: 8192` in `backend/common/src/config/settings.py`
2. Restart services: `docker-compose down && docker-compose up -d`
3. **Note**: Gemini 2.5 Flash supports up to 8192 tokens (vs 8193 for some older versions)

### Problem: Environment Variables Not Updated
**Root Cause**: Docker containers cache environment variables

**Solution**:
```bash
# Full clean restart
docker-compose down
docker-compose up -d

# Verify new environment
docker exec tlaongcloudv1-adk-host-1 env | grep GEMINI
```

### Problem: Source Paths Show Temp Files
**Root Cause**: Document processor uses temp paths, but metadata contains correct names

**Status**: ✅ **RESOLVED** - Frontend shows proper document names in metadata

## 📊 CURRENT SERVICE STATUS

### Backend Services
- ✅ **Auth Service**: http://localhost:8003 (API docs: /docs)
- ✅ **Workflow Service**: http://localhost:8004 (API docs: /docs)  
- ✅ **Special Education Service**: http://localhost:8005 (API docs: /docs)
- ✅ **MCP Server**: http://localhost:8001 (Vector store + document processing)
- ✅ **ADK Host**: http://localhost:8002 (LLM integration layer)
- ✅ **PostgreSQL**: localhost:5432
- ✅ **Redis**: localhost:6379

### Frontend
- ✅ **Next.js App**: http://localhost:3000
- ✅ **Dashboard**: http://localhost:3000/dashboard (real-time student data)
- ✅ **Student Management**: http://localhost:3000/students/list (create, view, manage)
- ✅ **Student Profiles**: http://localhost:3000/students/[id] (detailed views with mock data)
- ✅ **Chat Interface**: http://localhost:3000/chat
- ✅ **Document Library**: Integrated in chat interface
- ✅ **Real LLM Responses**: Gemini 2.5 Flash working
- ✅ **Real-time Data**: Student counts and lists update automatically

## 📋 DEPENDENCIES FIXED

### Docker Dependencies
All Dockerfiles updated with:
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir email-validator==2.1.0.post1 \
    sqlalchemy==2.0.25 asyncpg==0.29.0 backoff==2.2.1 \
    "numpy<2.0" chromadb==0.4.22
```

### Vector Store Configuration
- **Development**: ChromaDB (persistent local storage)
- **Production**: VertexVectorStore (with fallback to ChromaDB)
- **Environment Detection**: `ENVIRONMENT=development` in docker-compose.yml

## 🗂️ DOCUMENT LIBRARY

### Available Documents (18 total)
- **Assessment Reports**: AR1.pdf, AR2.pdf, AR3.pdf, AR3(1).pdf, AR5.pdf
- **Lesson Plans**: lesson_plan_Math_weekly_1.pdf, lesson_plan_Maths_daily_1.pdf
- **Synthetic Reports**: Synthetic_Assessment_Report_2-10.docx
- **Test File**: test.txt

### Document Processing Status
- ✅ **Processed**: 18 documents → 30 chunks
- ✅ **Embeddings**: Created with text-embedding-004
- ✅ **Vector Store**: ChromaDB with cosine similarity
- ✅ **Search**: Working with proper document name resolution

## 👥 STUDENT MANAGEMENT SYSTEM

### Core Features
- ✅ **Student CRUD**: Create, read, update students via API and UI
- ✅ **Real-time Dashboard**: Live student counts and statistics
- ✅ **Student Lists**: Searchable, filterable student directory
- ✅ **Student Profiles**: Detailed views with goals, IEPs, and activities
- ✅ **IEP Integration**: Basic IEP creation and association
- ✅ **IDEA Compliance**: Federal disability categories and proper data structure

### API Endpoints
```bash
# Student Management
GET    /api/v1/students                     # List all students
POST   /api/v1/students                     # Create new student
GET    /api/v1/students/{id}                # Get student details
PUT    /api/v1/students/{id}                # Update student
GET    /api/v1/students/search              # Search students

# IEP Management
GET    /api/v1/ieps/student/{student_id}    # Get student's IEPs
POST   /api/v1/ieps                         # Create IEP
GET    /api/v1/ieps/{id}                    # Get IEP details

# Dashboard Data (Mock + Real hybrid)
GET    /api/v1/dashboard/teacher/{user_id}  # Teacher dashboard (mock)
```

### Frontend Pages
- **Dashboard**: `/dashboard` - Real-time overview with student counts
- **Student List**: `/students/list` - Searchable student directory
- **Add Student**: `/students/new` - Student creation form
- **Student Profile**: `/students/[id]` - Individual student details
- **Chat Interface**: `/chat` - AI-powered document queries

### Data Flow
```
Student Creation Form → POST /api/v1/students → Database
                                              ↓
Dashboard Widgets ← useStudents() hook ← GET /api/v1/students
Student Lists ← useStudents() hook ← GET /api/v1/students
```

### Current Database State
- **6 Students**: Active in PostgreSQL database
- **0 Active IEPs**: No IEPs created yet
- **Real Counts**: Dashboard shows live student statistics
- **Auto-refresh**: Data updates every 30 seconds

## 🎯 KNOWN ISSUES RESOLVED

1. ✅ **Frontend routing conflict** - Resolved by renaming conflicting page.tsx
2. ✅ **Missing Python dependencies** - Added to all Dockerfiles
3. ✅ **Vector store initialization errors** - Fixed environment detection
4. ✅ **GCP authentication failures** - Fixed credential mounting
5. ✅ **Service networking issues** - Updated service URLs in .env
6. ✅ **Gemini model incompatibility** - Updated to gemini-2.5-flash
7. ✅ **Token limit errors** - Adjusted max_output_tokens to 4096
8. ✅ **Document source path issues** - Source names properly resolved in metadata
9. ✅ **Dashboard connection errors** - Fixed port mismatch in .env.local (8006→8005)
10. ✅ **Student profile endpoint missing** - Implemented composite endpoint using available APIs
11. ✅ **Dashboard showing mock data** - Integrated real student data with fallback to mock
12. ✅ **Student creation not propagating** - Fixed data flow from backend to frontend widgets
13. ✅ **Dashboard widget counts incorrect** - Updated to use real-time student counts

## 🔄 MAINTENANCE COMMANDS

### Daily Startup
```bash
# Quick start (if services were stopped)
cd /Users/anshu/Documents/GitHub/tlaongcloudv1
docker-compose up -d
cd /Users/anshu/Documents/GitHub/v0-tla-front-endv01
npm run dev
```

### Clean Restart (when issues occur)
```bash
# Full reset
cd /Users/anshu/Documents/GitHub/tlaongcloudv1
docker-compose down
docker-compose up -d
sleep 30
curl -X POST http://localhost:8001/documents/process
```

### Monitor Services
```bash
# Check all service health
curl http://localhost:8002/health | jq
docker-compose logs adk-host | tail -10
docker-compose logs mcp-server | tail -10
```

---

**Last Updated**: 2025-06-26  
**System Status**: ✅ All services operational with real LLM integration and student management  
**Documents Processed**: 18 → 30 chunks in vector store  
**Model**: Gemini 2.5 Flash (stable configuration)  
**Student System**: ✅ Full CRUD operations with real-time dashboard updates  
**Current Students**: 6 active students in system