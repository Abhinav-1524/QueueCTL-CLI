#!/bin/bash
set -e
source "$(dirname "$0")/utils.sh"

info "Running Scheduled Jobs Test"
clean_env

# Schedule job 1 minute in the future (should stay pending)
future_time=$(python - <<'PYCODE'
from datetime import datetime, timedelta, timezone
print((datetime.now(timezone.utc) + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ"))
PYCODE
)

queuectl enqueue "{\"command\":\"echo Future Test\",\"run_at\":\"$future_time\"}" >/dev/null

# Confirm it exists in DB and is pending
count=$(python - <<'PYCODE'
import sqlite3
con = sqlite3.connect("store.db")
cur = con.cursor()
cur.execute("SELECT COUNT(*) FROM jobs WHERE status='pending';")
print(cur.fetchone()[0])
con.close()
PYCODE
)

if [ "$count" -eq 0 ]; then
    err "Scheduled job not pending before time"
    queuectl list --status all
    exit 1
fi
pass "Job correctly pending before run time"

# Accelerate test by fast-forwarding run_at to now (simulate time passing)
python - <<'PYCODE'
import sqlite3, datetime
con = sqlite3.connect("store.db")
cur = con.cursor()
cur.execute("UPDATE jobs SET run_at=datetime('now','utc') WHERE status='pending';")
con.commit()
con.close()
PYCODE

# Start worker briefly to execute job
queuectl worker-start --count 1 >/tmp/worker_sched.log 2>&1 &
pid=$!
sleep 6
queuectl worker-stop >/dev/null 2>&1 || true
kill $pid >/dev/null 2>&1 || true

grep -iq "Future Test" /tmp/worker_sched.log && pass "Scheduled job executed after time" || fail "Job did not execute after run_at"
