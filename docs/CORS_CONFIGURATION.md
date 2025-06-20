# CORS Configuration Guide

## Overview

Cross-Origin Resource Sharing (CORS) configuration has been enhanced to support multiple formats and provide better security controls.

## Environment Variables

### CORS_ORIGINS

Defines allowed origins for cross-origin requests. Supports multiple formats:

**Comma-separated string (recommended):**
```bash
CORS_ORIGINS=http://localhost:3000,https://myapp.com,https://admin.myapp.com
```

**JSON array format:**
```bash
CORS_ORIGINS='["http://localhost:3000", "https://myapp.com", "https://admin.myapp.com"]'
```

### CORS_ALLOW_CREDENTIALS

Controls whether credentials (cookies, authorization headers) are allowed:
```bash
CORS_ALLOW_CREDENTIALS=true  # Default: true
```

### CORS_ALLOW_METHODS

Defines allowed HTTP methods:
```bash
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH,OPTIONS  # Default
```

### CORS_ALLOW_HEADERS

Defines allowed request headers:
```bash
CORS_ALLOW_HEADERS=*  # Allow all headers (default)
# Or specify specific headers:
CORS_ALLOW_HEADERS=Content-Type,Authorization,X-Requested-With
```

## Configuration Examples

### Development Environment
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH,OPTIONS
CORS_ALLOW_HEADERS=*
```

### Production Environment
```bash
CORS_ORIGINS=https://your-app.com,https://admin.your-app.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH
CORS_ALLOW_HEADERS=Content-Type,Authorization,X-Requested-With
```

### Testing Environment
```bash
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,PATCH,OPTIONS
CORS_ALLOW_HEADERS=*
```

## Security Considerations

1. **Never use `*` for origins in production** - Always specify exact domains
2. **Be specific with allowed headers** in production environments
3. **Use HTTPS origins** in production
4. **Validate origin domains** before adding them to the configuration

## Usage in Code

The configuration automatically parses different formats and provides helper properties:

```python
from common.src.config import get_settings

settings = get_settings()

# Get origins as list (regardless of input format)
origins = settings.cors_origins_list

# Get methods as list
methods = settings.cors_methods_list

# Get headers as list
headers = settings.cors_headers_list
```

## FastAPI Integration

The CORS configuration integrates seamlessly with FastAPI's CORS middleware:

```python
from fastapi.middleware.cors import CORSMiddleware
from common.src.config import get_settings

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
)
```

## Troubleshooting

### Common Issues

1. **CORS errors in browser console:**
   - Check that your frontend domain is included in `CORS_ORIGINS`
   - Ensure the protocol (http/https) matches exactly

2. **Credentials not working:**
   - Set `CORS_ALLOW_CREDENTIALS=true`
   - Ensure frontend sends credentials with requests

3. **Custom headers blocked:**
   - Add specific headers to `CORS_ALLOW_HEADERS`
   - Or use `*` for development (not recommended for production)

### Testing CORS Configuration

```bash
# Test with curl
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8003/auth/login

# Should return CORS headers in response
```