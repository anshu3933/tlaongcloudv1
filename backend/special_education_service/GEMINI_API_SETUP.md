# Gemini API Setup - REAL API ONLY

## Required Configuration

The system now requires a **real Gemini API key** for operation. All mock/simulated logic has been removed.

### 1. Get Gemini API Key

1. Visit: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Create a new API key
4. Copy the key (starts with `AIzaSy...`)

### 2. Configure Environment

Add the API key to your environment:

```bash
# Option 1: Export in terminal
export GEMINI_API_KEY="AIzaSy...your-actual-api-key"

# Option 2: Add to .env file
echo "GEMINI_API_KEY=AIzaSy...your-actual-api-key" >> .env

# Option 3: Add to shell profile
echo 'export GEMINI_API_KEY="AIzaSy...your-actual-api-key"' >> ~/.bashrc
source ~/.bashrc
```

### 3. Verify Configuration

Test the setup:

```bash
python -c "
import os
key = os.getenv('GEMINI_API_KEY')
if key:
    print(f'✅ API key configured: {key[:10]}...')
else:
    print('❌ GEMINI_API_KEY not set')
"
```

### 4. Start Service

```bash
# Start the enhanced RAG service
python start_test_service.py

# The service should show:
# 🔑 Using GEMINI_API_KEY for authentication
# ✅ Enhanced vector store initialized successfully  
# ✅ Metadata-aware IEP generator initialized successfully
```

## Alternative: Application Default Credentials

If you prefer to use GCP Application Default Credentials:

```bash
# Configure GCP credentials
gcloud auth application-default login --scopes=https://www.googleapis.com/auth/generative-language

# The service will automatically detect and use ADC
```

## No Fallbacks

The system no longer supports:
- ❌ Mock mode (`USE_MOCK_LLM`)
- ❌ Simulated responses
- ❌ Fake AI generation
- ❌ Test content generation

**Real Gemini API is required for all IEP generation.**