#!/bin/bash
set -e
source "$(dirname "$0")/utils.sh"

info "Running Multi-Worker Concurrency Test"
clean_env

# Enqueue 5 jobs
for i in {1..5}; do
  queuectl enqueue "{\"command\":\"echo Job $i\"}" >/dev/null
done

# Start 3 workers in background
queuectl worker-start --count 3 >/tmp/multi_worker.log 2>&1 &
pid=$!

# Wait for all jobs to finish (max 30s)
for i in {1..30}; do
  jobs_done=$(grep -c "finished" /tmp/multi_worker.log || true)
  if (( jobs_done >= 5 )); then
    break
  fi
  sleep 1
done

# Gracefully stop workers
queuectl worker-stop >/dev/null 2>&1 || true
kill $pid >/dev/null 2>&1 || true

# Evaluate results
grep -qi "finished" /tmp/multi_worker.log || fail "No job executions found"
jobs_done=$(grep -c "finished" /tmp/multi_worker.log || true)

if (( jobs_done < 5 )); then
  echo "--- Worker Log (trimmed) ---"
  tail -n 15 /tmp/multi_worker.log
  fail "Only $jobs_done/5 jobs executed (timeout)"
else
  pass "Multi-worker concurrent job execution verified"
fi
