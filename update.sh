#!/bin/bash
set -euo pipefail

log() {
  echo "[$(date +%H:%M:%S)] $*"
}

log "Running genome metrics..."
npm run genome-metrics

log "Building print-and-play PDF..."
npm run build-pdf

log "Building Next.js app..."
npm run build

if git diff --quiet && git diff --cached --quiet; then
  log "No changes to commit."
  exit 0
fi

log "Staging changes..."
git add -u

if git diff --cached --quiet; then
  log "No staged changes."
  exit 0
fi

log "Committing..."
git commit -m "Update genome metrics and PDF"

log "Pushing to origin/main..."
git push origin main
