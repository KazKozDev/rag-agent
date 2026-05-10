# RAG Agent v2 — Setup Guide

## Prerequisites

- Docker + Docker Compose
- OpenAI API key (or compatible endpoint)

## Quick Start

1. **Clone and configure:**
   ```bash
   cp .env.example .env
   # Edit .env with your API key
   ```

2. **Deploy:**
   ```bash
   docker compose up -d
   ```

3. **Add documents:**
   ```bash
   mkdir -p data/documents
   cp /path/to/your/pdfs/*.pdf data/documents/
   ```

4. **Ingest documents:**
   ```bash
   ./scripts/ingest.sh
   ```

5. **Open UI:**
   http://localhost:8501

## Endpoints

| Method | Path              | Description          |
|--------|-------------------|----------------------|
| POST   | /api/query        | Ask a question       |
| POST   | /api/ingest       | Ingest documents     |
| POST   | /api/feedback     | Record feedback      |
| GET    | /api/feedback/stats | Feedback statistics  |
| GET    | /api/health       | Health check         |

## Running Tests

```bash
docker compose run --rm api pytest tests/ -v
```
