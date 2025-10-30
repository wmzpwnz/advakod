#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 <IMAGE_TAG> <REGISTRY_OR_BACKEND_IMAGE> <STACK_DIR> [FRONTEND_IMAGE]"
  echo "Examples:"
  echo "  # Private registry namespace (script will form names /backend and /frontend)"
  echo "  $0 v1.0.0 registry.advacodex.com/advakod /opt/advakod"
  echo "  # GHCR explicit images (backend and frontend images passed explicitly)"
  echo "  $0 v1.0.0 ghcr.io/wmzpwnz/advakod-backend /opt/advakod ghcr.io/wmzpwnz/advakod-frontend"
  exit 1
fi

IMAGE_TAG="$1"
SECOND_ARG="$2"
STACK_DIR="$3"
FOURTH_ARG="${4:-}"

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

echo "Pulling images ${BACKEND_IMAGE}:${IMAGE_TAG} and ${FRONTEND_IMAGE}:${IMAGE_TAG}"
docker compose -f docker-compose.release.yml pull backend frontend || true

echo "Deploying stack with tag ${IMAGE_TAG}"
docker compose -f docker-compose.release.yml up -d

# Apply database migrations (Alembic)
echo "Running Alembic upgrade to head"
docker compose -f docker-compose.release.yml run --rm backend alembic upgrade head || {
  echo "Alembic upgrade failed, stopping." >&2
  exit 2
}

echo "Deployment finished. Current images:"
docker ps --format '{{.Names}}\t{{.Image}}' | grep -E 'advakod_(backend|frontend|nginx)'
