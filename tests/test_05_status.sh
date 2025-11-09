#!/bin/bash
set -e
source "$(dirname "$0")/utils.sh"

info "Running Status Tests"

queuectl enqueue '{"command":"echo StatusCheck"}' >/dev/null
output=$(queuectl status)
echo "$output" | grep -qi "Queue Summary" || fail "Status command failed"
echo "$output" | grep -Eqi "pending|completed|failed" || fail "Status output missing states"
pass "System status command verified successfully"
