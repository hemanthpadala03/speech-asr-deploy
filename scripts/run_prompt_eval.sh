#!/usr/bin/env bash
# Runs the prompt A/B harness (asrserve.agents.eval) against the seeded
# sample transcripts in tests/fixtures/transcripts, comparing
# meeting_summary_v1 against meeting_summary_v2. Requires a working
# OPENAI_API_KEY or ANTHROPIC_API_KEY in .env (real LLM calls, not mocked).
set -euo pipefail
cd "$(dirname "$0")/.."

set -a
source .env
set +a

PYTHONPATH=src python -m asrserve.agents.eval
