#!/usr/bin/env bash
set -euo pipefail

curl --fail-with-body \
  --request POST \
  --header 'Content-Type: application/json' \
  --data @scripts/demo_request.json \
  http://127.0.0.1:8000/events/docs-request
