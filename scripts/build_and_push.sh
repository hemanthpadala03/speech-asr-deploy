#!/usr/bin/env bash
# Builds the container and pushes to the ECR repo created by infra/terraform/ecr.tf.
# Usage: ./scripts/build_and_push.sh <ecr-repo-url> <tag>
set -euo pipefail
cd "$(dirname "$0")/.."

REPO_URL="${1:?Usage: build_and_push.sh <ecr-repo-url> <tag>}"
TAG="${2:?Usage: build_and_push.sh <ecr-repo-url> <tag>}"

aws ecr get-login-password | docker login --username AWS --password-stdin "${REPO_URL%%/*}"
docker build -f docker/Dockerfile -t "${REPO_URL}:${TAG}" .
docker push "${REPO_URL}:${TAG}"

echo "Pushed ${REPO_URL}:${TAG}"
