#!/bin/bash
set -e
source "$(dirname "$0")/utils.sh"

info "Running DLQ Purge Confirmation Test"
clean_env

# ------------------------------------------------------------
# Create a fake dead job (using Python instead of sqlite3 CLI)
# ------------------------------------------------------------
queuectl enqueue '{"command":"exit 1"}' >/dev/null

python - <<'PYCODE'
import sqlite3
con = sqlite3.connect("store.db")
cur = con.cursor()
cur.execute("UPDATE jobs SET status='dead' WHERE status='pending';")
con.commit()
con.close()
PYCODE

# ------------------------------------------------------------
# Verify job is dead before purge
# ------------------------------------------------------------
dead_count=$(python - <<'PYCODE'
import sqlite3
con = sqlite3.connect("store.db")
cur = con.execute("SELECT COUNT(*) FROM jobs WHERE status='dead'")
print(cur.fetchone()[0])
con.close()
PYCODE
)

if [ "$dead_count" -lt 1 ]; then
  fail "No dead jobs found before purge"
else
  pass "Dead job exists before purge"
fi

# ------------------------------------------------------------
# Run purge without --confirm (should not delete)
# ------------------------------------------------------------
output=$(queuectl dlq-purge 2>&1 || true)
echo "$output" | grep -qi "confirm" || fail "Missing confirmation prompt"
pass "Confirmation prompt required"

# ------------------------------------------------------------
# Run purge with --confirm (should delete)
# ------------------------------------------------------------
queuectl dlq-purge --confirm >/dev/null

remaining=$(python - <<'PYCODE'
import sqlite3
con = sqlite3.connect("store.db")
cur = con.execute("SELECT COUNT(*) FROM jobs WHERE status='dead'")
print(cur.fetchone()[0])
con.close()
PYCODE
)

if [ "$remaining" -eq 0 ]; then
  pass "DLQ purge successfully removed all dead jobs"
else
  fail "DLQ purge did not clear all dead jobs"
fi
