#!/bin/bash
set -e
source "$(dirname "$0")/utils.sh"

info "Running Full End-to-End Lifecycle Test"
clean_env

# ------------------------------------------------------------
# Step 1: Configure short retry window
# ------------------------------------------------------------
queuectl config-set max_retries 1 >/dev/null
queuectl config-set backoff_base 1 >/dev/null

# ------------------------------------------------------------
# Step 2: Enqueue 3 jobs — one failing, one delayed, one normal
# ------------------------------------------------------------
queuectl enqueue '{"command":"echo Success Job"}' >/dev/null
queuectl enqueue '{"command":"exit 1"}' >/dev/null
queuectl enqueue '{"command":"echo Delayed Job", "run_at":"2099-01-01T00:00:00Z"}' >/dev/null

# ------------------------------------------------------------
# Step 3: Run worker
# ------------------------------------------------------------
queuectl worker-start --count 1 >/tmp/e2e_worker.log 2>&1 &
pid=$!

sleep 5  # allow job execution
queuectl worker-stop >/dev/null 2>&1 || true
kill $pid >/dev/null 2>&1 || true

# ------------------------------------------------------------
# Step 4: Verify completed job
# ------------------------------------------------------------
grep -qi "finished" /tmp/e2e_worker.log && pass "Job processing completed" || fail "No jobs completed"

# ------------------------------------------------------------
# Step 5: Verify DLQ entry (failed job)
# ------------------------------------------------------------
sleep 2  # small wait for final commit
output=$(queuectl dlq-list || true)
echo "$output" | grep -qi "dead" && pass "Failed job correctly moved to DLQ" || fail "No job found in DLQ"

# ------------------------------------------------------------
# Step 6: Verify scheduled job still pending
# ------------------------------------------------------------
pending=$(python - <<'PYCODE'
import sqlite3
con = sqlite3.connect("store.db")
cur = con.execute("SELECT COUNT(*) FROM jobs WHERE status='pending'")
print(cur.fetchone()[0])
con.close()
PYCODE
)

if [ "$pending" -ge 1 ]; then
  pass "Future scheduled job correctly pending"
else
  fail "Scheduled job missing or executed prematurely"
fi
