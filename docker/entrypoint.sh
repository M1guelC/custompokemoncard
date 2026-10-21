#!/bin/sh
set -e
if [ ! -w "${HOME:-/tmp}" ]; then
  export HOME=/tmp
fi
mkdir -p "$HOME"
if [ "$#" -gt 0 ]; then
  exec "$@"
fi
if [ "${CARD_SERVER_ONLY:-}" != "1" ] && [ "${CARD_CONTAINER:-}" != "1" ]; then
  if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    echo "No display was passed in. From the project folder, run:"
    echo "  ./run"
    exit 1
  fi
fi
cd /app
exec python main.py
