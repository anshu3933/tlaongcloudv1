# RAG MCP Backend

A backend service for RAG (Retrieval-Augmented Generation) using MCP (Model Control Protocol) with Gemini integration.

## Features

- FastAPI-based REST API
- Gemini model integration for text generation
- Document retrieval and processing
- Docker containerization
- Redis caching

## Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Google Cloud credentials (for Gemini API)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd rag-mcp-backend
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Build and start the services:
```bash
docker-compose up -d --build
```

## API Endpoints

### Query Endpoint
- **URL**: `/api/v1/query`
- **Method**: `POST`
- **Body**:
```json
{
    "query": "Your question here",
    "options": {
        "top_k": 5
    }
}
```

## Project Structure

```
.
├── backend/
│   ├── adk_host/         # API layer
│   ├── common/           # Shared utilities
│   └── mcp_server/       # MCP server implementation
├── scripts/              # Utility scripts
├── docker-compose.yml    # Docker configuration
└── README.md            # This file
```

## Development

1. Install development dependencies:
```bash
pip install -r backend/requirements.txt
```

2. Run tests:
```bash
pytest
```

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here] 