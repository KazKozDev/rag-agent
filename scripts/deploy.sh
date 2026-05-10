#!/bin/bash
set -e

echo "=== RAG Agent v2 — Deploy ==="

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "WARNING: Edit .env with your actual API keys before deploying."
fi

docker compose up -d --build

echo ""
echo "Deploy complete!"
echo "  API:       http://localhost:8000"
echo "  Streamlit:  http://localhost:8501"
echo ""
echo "To ingest documents:"
echo "  ./scripts/ingest.sh ./data/documents"
