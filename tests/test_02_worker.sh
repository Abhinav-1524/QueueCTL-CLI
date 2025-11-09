#!/bin/bash
set -e
source "$(dirname "$0")/utils.sh"

info " Running Worker Tests"
clean_env

# Enqueue a test job
queuectl enqueue '{"command":"echo Worker Test"}' >/dev/null

# Start worker asynchronously
queuectl worker-start --count 1 > /tmp/worker_out.log 2>&1 &
pid=$!

# Wait for job execution
sleep 6
queuectl worker-stop >/dev/null 2>&1 || true
sleep 2
kill $pid >/dev/null 2>&1 || true

# Normalize output (strip non-ASCII)
iconv -f utf-8 -t ascii//TRANSLIT /tmp/worker_out.log 2>/dev/null | tr -cd '\11\12\15\40-\176' > /tmp/worker_clean.log

# Optional debug
# cat /tmp/worker_clean.log

# Match both variants: finished + optional success
if grep -Eiq "Job .*finished(.*success)?" /tmp/worker_clean.log; then
    pass "Worker executed job successfully"
else
    err "Worker did not execute job"
    echo "--- Worker Log ---"
    cat /tmp/worker_clean.log
    exit 1
fi

# Verify worker stop acknowledgment
output=$(queuectl worker-stop 2>&1 || true)
echo "$output" | grep -Eqi "stop|signal" || fail "Worker stop not acknowledged"
pass "Worker stop tested successfully"
