#!/usr/bin/env bash
# Builds (first run only, ~15-25 min) and starts the Plane stack in the background.
set -euo pipefail
cd "$(dirname "$0")/.."

nohup docker compose -f docker-compose.yml -f .devcontainer/docker-compose.codespaces.yml \
  up -d --build >/tmp/plane-up.log 2>&1 &
echo "Starting Plane in the background; follow progress with: tail -f /tmp/plane-up.log"
