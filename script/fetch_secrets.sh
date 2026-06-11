#!/bin/bash
# Pull StatFacts secrets from GCP Secret Manager (project starful-258005).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${GCP_PROJECT_ID:-starful-258005}"
ENV_FILE="$ROOT/.env"
SECRET_ID="${GEMINI_API_KEY_SECRET_ID:-GEMINI_API_KEY}"

GEMINI="$(gcloud secrets versions access latest --secret="$SECRET_ID" --project="$PROJECT" 2>/dev/null || true)"

if [[ -z "$GEMINI" ]]; then
  echo "ERROR: could not read secret $SECRET_ID from project $PROJECT" >&2
  exit 1
fi

if [[ -f "$ENV_FILE" ]] && grep -q '^GEMINI_API_KEY=' "$ENV_FILE"; then
  if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=${GEMINI}|" "$ENV_FILE"
  else
    sed -i "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=${GEMINI}|" "$ENV_FILE"
  fi
else
  cat >>"$ENV_FILE" <<EOF

# GEMINI_API_KEY from Secret Manager — do not commit
GEMINI_API_KEY=${GEMINI}
EOF
fi

chmod 600 "$ENV_FILE" 2>/dev/null || true
echo "OK: GEMINI_API_KEY written to $ENV_FILE (from $SECRET_ID)"
