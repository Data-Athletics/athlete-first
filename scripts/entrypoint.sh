#!/bin/bash

set -e

env="${1:-prod}"
main="./app/main.py"

bash /scripts/wait-for-db.sh

if [[ "$env" = "prod" ]]; then
  fastapi run "$main" --host 0.0.0.0 --port "${PORT}"
else
  fastapi dev "$main" --host 0.0.0.0 --port "${PORT}"
fi