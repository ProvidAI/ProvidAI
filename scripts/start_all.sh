#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"

cd "${ROOT_DIR}"

if [[ -f .env ]]; then
  set -o allexport
  # shellcheck disable=SC1091
  source .env
  set +o allexport
fi

export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

PIDS=()

cleanup() {
  for pid in "${PIDS[@]}"; do
    if kill -0 "${pid}" 2>/dev/null; then
      echo "Stopping PID ${pid}..."
      kill "${pid}" 2>/dev/null || true
      wait "${pid}" 2>/dev/null || true
    fi
  done
}

trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM
trap cleanup EXIT

start_service() {
  local name=$1
  shift
  echo "Starting ${name}..."
  "$@" &
  local pid=$!
  PIDS+=("${pid}")
  echo "  ${name} PID: ${pid}"
}

UVICORN_HOST="${API_HOST:-0.0.0.0}"
UVICORN_PORT="${API_PORT:-8000}"

start_service "Orchestrator API" python3 -m uvicorn api.main:app --host "${UVICORN_HOST}" --port "${UVICORN_PORT}" --reload

start_service "Negotiator A2A server" python3 -m agents.negotiator.server
start_service "Executor A2A server" python3 -m agents.executor.server
start_service "Verifier A2A server" python3 -m agents.verifier.server

if [[ -d "${FRONTEND_DIR}" ]]; then
  start_service "Frontend dev server" npm --prefix "${FRONTEND_DIR}" run dev
else
  echo "Frontend directory not found at ${FRONTEND_DIR}, skipping frontend dev server."
fi

echo "All services are running. Press Ctrl+C to stop."
wait
