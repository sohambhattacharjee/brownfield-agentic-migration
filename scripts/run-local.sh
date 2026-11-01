#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
python3 app/shipping_service.py &
shipping_pid=$!
cleanup() {
  kill "$shipping_pid" 2>/dev/null || true
  wait "$shipping_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
sleep 0.3
python3 app/legacy_monolith.py
