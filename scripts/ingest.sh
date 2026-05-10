#!/bin/bash
set -euo pipefail

# Drop existing indexes and restart the API container so it rebuilds from data/docs/.
docker compose stop api >/dev/null 2>&1 || true
rm -rf data/chroma data/bm25
mkdir -p data/chroma data/bm25
docker compose up -d api

echo "Indexes will be rebuilt on next API startup. Tail logs with:"
echo "  docker compose logs -f api"
