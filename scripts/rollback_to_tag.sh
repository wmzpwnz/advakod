#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 <IMAGE_TAG> <REGISTRY_OR_BACKEND_IMAGE> <STACK_DIR> [FRONTEND_IMAGE] [ALEMBIC_TARGET_REV]"
  echo "Examples:"
  echo "  # Private registry namespace (script will form names /backend and /frontend)"
  echo "  $0 v1.0.1 registry.advacodex.com/advakod /opt/advakod"
  echo "  # GHCR explicit images (backend and frontend images passed explicitly)"
  echo "  $0 v1.0.1 ghcr.io/wmzpwnz/advakod-backend /opt/advakod ghcr.io/wmzpwnz/advakod-frontend a1b2c3d4"
  exit 1
fi

IMAGE_TAG="$1"
SECOND_ARG="$2"
STACK_DIR="$3"
FOURTH_ARG="${4:-}"
TARGET_REVISION="${5:-}"  # optional: specific Alembic revision

# Determine images: if 4th arg provided, use explicit backend/frontend images (GHCR mode)
# Otherwise treat SECOND_ARG as a registry namespace and compose /backend and /frontend images
if [ -n "$FOURTH_ARG" ]; then
  BACKEND_IMAGE="$SECOND_ARG"
  FRONTEND_IMAGE="$FOURTH_ARG"
else
  BACKEND_IMAGE="${SECOND_ARG}/backend"
  FRONTEND_IMAGE="${SECOND_ARG}/frontend"
fi

export IMAGE_TAG
export BACKEND_IMAGE
export FRONTEND_IMAGE

cd "$STACK_DIR"

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

echo "Rolling back to image tag ${IMAGE_TAG}"
docker compose -f docker-compose.release.yml pull backend frontend || true

docker compose -f docker-compose.release.yml up -d

# Downgrade database schema
if [ -n "$TARGET_REVISION" ]; then
  echo "Downgrading Alembic to revision ${TARGET_REVISION}"
  docker compose -f docker-compose.release.yml run --rm backend alembic downgrade "$TARGET_REVISION"
else
  echo "Downgrading Alembic one step (-1)"
  docker compose -f docker-compose.release.yml run --rm backend alembic downgrade -1 || echo "No previous migration or downgrade failed"
fi

echo "Rollback finished. Current images:"
docker ps --format '{{.Names}}\t{{.Image}}' | grep -E 'advakod_(backend|frontend|nginx)'
