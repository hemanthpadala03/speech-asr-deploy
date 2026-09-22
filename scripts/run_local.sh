#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No .env found -- copy env.example to .env and fill in an API key first." >&2
  exit 1
fi

set -a
source .env
set +a

uvicorn asrserve.api.main:app --reload --host 0.0.0.0 --port 8000
