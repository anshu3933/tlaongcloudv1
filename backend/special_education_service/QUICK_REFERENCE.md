# Quick Reference - Assessment Pipeline (July 17, 2025)

## 🚨 FIRST STEP: Check for Port Conflicts
```bash
lsof -i :8005
# If multiple services listed, stop Docker container:
docker ps | grep 8005 && docker stop [container-id]
```

## 🚀 Start Development Service
```bash
GEMINI_API_KEY="AIzaSyDEmol7oGNgPose137dLA8MWtI1pyOAoVs" \
python -m uvicorn src.main:app --reload --port 8005 --log-level debug
```

## ✅ Verify Service Health
```bash
curl http://localhost:8005/health
# Expected: {"status":"healthy","service":"special-education","version":"1.0.0"...}
```

## 🧪 Test Assessment Upload
```bash
curl -X POST "http://localhost:8005/api/v1/assessments/documents/upload" \
  -F "file=@test.pdf" \
  -F "student_id=35fb859c-23bf-4eec-9c53-ea24e37bc4b9" \
  -F "assessment_type=wisc_v" \
  -F "assessor_name=Dr. Test"
```

## 📊 Monitor Background Processing
```bash
# Watch for background task execution
tail -f server_final.log | grep "🚀🚀🚀 BACKGROUND TASK STARTED"

# Check document status
curl "http://localhost:8005/api/v1/assessments/documents/[id]" | jq '.processing_status'

# View extracted scores
curl "http://localhost:8005/api/v1/assessments/scores/document/[id]"
```

## 🔧 Key Technical Solutions
- **Event Loop Conflicts**: Fixed with thread executor in `process_uploaded_document_background_sync()`
- **Port Conflicts**: Docker container was intercepting requests
- **Background Tasks**: Working via FastAPI BackgroundTasks
- **Document AI**: Processing PDFs in ~3 seconds with 95% confidence

## 📈 Expected Performance
- **Upload Response**: < 500ms
- **Background Queue**: < 100ms  
- **Document AI**: 2-5 seconds
- **Score Extraction**: 4+ scores with 85%+ confidence
- **Total Pipeline**: < 10 seconds for typical PDF

## 🎯 Status Progression
```
uploaded → processing → extracting → completed
```

## 📁 Critical Files
- `src/routers/assessment_router.py` - Main upload and processing logic
- `src/services/document_ai_service.py` - Google Document AI integration
- `ASSESSMENT_PIPELINE_SUCCESS.md` - Complete session documentation