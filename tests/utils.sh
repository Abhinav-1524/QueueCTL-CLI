#!/bin/bash
set -e

# Colored output handling (cross-platform safe)
RED=$(printf '\033[0;31m')
GREEN=$(printf '\033[0;32m')
YELLOW=$(printf '\033[1;33m')
BLUE=$(printf '\033[1;34m')
RESET=$(printf '\033[0m')

info()  { echo -e "${BLUE}[INFO]${RESET} $1"; }
ok()    { echo -e "${GREEN}[OK]${RESET} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${RESET} $1"; }
err()   { echo -e "${RED}[ERR]${RESET} $1"; }

fail()  { err "$1"; exit 1; }
pass()  { ok "$1"; }

clean_env() {
  rm -f store.db worker_threads.json stop_signal.json 2>/dev/null || true
}
