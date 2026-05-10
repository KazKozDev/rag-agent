#!/bin/bash
# Double-click this in Finder to (re)start rag-agent-v2 and open it in the browser.
# Pressing Ctrl+C in the Terminal window stops the containers cleanly.

set -e

# Resolve repo root regardless of where Finder launches us from.
# This script lives at the project root, so SCRIPT_DIR == project root.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "▸ rag-agent-v2  (project: $(pwd))"
echo

# 1. Make sure Docker is up. Start Docker Desktop and wait for the daemon.
if ! docker info >/dev/null 2>&1; then
    echo "▸ Docker is not running — launching Docker Desktop…"
    open -a Docker
    until docker info >/dev/null 2>&1; do
        printf "."
        sleep 2
    done
    echo
    echo "▸ Docker is up."
fi

# 2. Kill anything already running for this project (idempotent).
echo "▸ Stopping any existing containers…"
docker compose down --remove-orphans 2>/dev/null || true

# 3. Rebuild + start. --build picks up code/.env changes since last run.
echo "▸ Building and starting containers…"
docker compose up -d --build

# 4. Wait for the API to report healthy.
echo -n "▸ Waiting for API to be ready"
for i in {1..60}; do
    if curl -fs http://localhost:8000/api/health >/dev/null 2>&1; then
        echo " ✓"
        break
    fi
    printf "."
    sleep 1
    if [ "$i" = 60 ]; then
        echo
        echo "✗ API did not become healthy in 60s. Check 'docker compose logs api'."
        echo "Press any key to close this window…"
        read -n 1
        exit 1
    fi
done

# 5. Open the UI in the default browser.
echo "▸ Opening http://localhost:8501 in your browser…"
open "http://localhost:8501"

echo
echo "──────────────────────────────────────────────"
echo "  API:  http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo "  UI:   http://localhost:8501"
echo "──────────────────────────────────────────────"
echo
echo "Streaming logs. Press Ctrl+C to stop the containers and exit."
echo

# 6. Tail logs in the foreground; trap Ctrl+C to bring containers down.
trap 'echo; echo "▸ Stopping containers…"; docker compose down; exit 0' INT
docker compose logs -f
