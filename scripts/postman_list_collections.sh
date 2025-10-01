#!/usr/bin/env bash
set -euo pipefail
: "${POSTMAN_API_KEY:?Set POSTMAN_API_KEY in environment or .env first}"

curl -s -H "X-Api-Key: ${POSTMAN_API_KEY}" https://api.getpostman.com/collections | jq '.' || echo "Install jq for pretty output (optional)"
