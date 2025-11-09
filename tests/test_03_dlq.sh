#!/bin/bash
set -e
source "$(dirname "$0")/utils.sh"

info "Running DLQ Tests"
clean_env

# Helper function to query SQLite safely using Python
pyquery() {
    query="$1"
    python - "$query" <<'PYCODE'
import sqlite3, sys
query = sys.argv[1]
con = sqlite3.connect("store.db")
cur = con.cursor()
cur.execute(query)
rows = cur.fetchall()
for r in rows:
    print(r[0])
con.close()
PYCODE
}

# ------------------------------------------------------------
# Simulate a dead job
# ------------------------------------------------------------
queuectl enqueue '{"command":"exit 1"}' >/dev/null
python - <<'PYCODE'
import sqlite3
con = sqlite3.connect("store.db")
con.execute("UPDATE jobs SET status='dead' WHERE status='pending';")
con.commit()
con.close()
PYCODE

# ------------------------------------------------------------
# List DLQ
# ------------------------------------------------------------
output=$(queuectl dlq-list)
echo "$output" | grep -qi "dead" || fail "DLQ list missing job"
pass "DLQ listing works"

# ------------------------------------------------------------
# Retry DLQ job
# ------------------------------------------------------------
id=$(pyquery "SELECT id FROM jobs LIMIT 1;")
queuectl dlq-retry "$id" >/dev/null
status=$(pyquery "SELECT status FROM jobs WHERE id='$id';")
[[ "$status" == "pending" ]] || fail "Retry did not set job to pending"
pass "DLQ retry successful"

# ------------------------------------------------------------
# Purge DLQ
# ------------------------------------------------------------
queuectl dlq-purge --confirm >/dev/null
count=$(pyquery "SELECT COUNT(*) FROM jobs WHERE status='dead';")
[[ "$count" == "0" ]] || fail "DLQ purge failed"
pass "DLQ purge verified"
