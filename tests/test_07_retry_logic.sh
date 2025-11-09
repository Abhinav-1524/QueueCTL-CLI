#!/bin/bash
set -e
source "$(dirname "$0")/utils.sh"

info "Running Retry Logic Test"
clean_env

# Configure lower retry count
queuectl config-set max_retries 2 >/dev/null

# Enqueue a failing job
queuectl enqueue '{"command":"exit 1"}' >/dev/null

# Run worker to process and retry
timeout 10s queuectl worker-start --count 1 >/tmp/retry_out.log 2>&1 || true

# Verify job moved to DLQ
output=$(queuectl dlq-list || true)
echo "$output" | grep -qi "dead" || fail "Job did not move to DLQ after retries"
pass "Retry logic correctly moved job to DLQ"
