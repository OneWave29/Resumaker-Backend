#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/resumaker-backend}"
IMAGE_TAG="${1:-${IMAGE_TAG:-latest}}"

cd "${APP_DIR}"

export IMAGE_TAG

if [[ -n "${GCP_SA_KEY:-}" ]]; then
  echo "${GCP_SA_KEY}" | docker login -u _json_key --password-stdin https://gcr.io
fi

docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
