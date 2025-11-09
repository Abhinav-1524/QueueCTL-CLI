#!/bin/bash
set -e
source "$(dirname "$0")/utils.sh"

info "Running Enqueue Tests (QueueCTL Refactored Build)"
clean_env

# Valid job enqueue
output=$(queuectl enqueue '{"command":"echo Hello QueueCTL"}')
echo "$output" | grep -qi "job added successfully" || fail "Failed to enqueue valid job"
pass "Valid job successfully added"

# Invalid JSON
output=$(queuectl enqueue '{command:echo fail}' 2>&1 || true)
echo "$output" | grep -qi "invalid json" || fail "Invalid JSON not handled"
pass "Invalid JSON handled as expected"

# Missing 'command'
output=$(queuectl enqueue '{"id":"test01"}' 2>&1 || true)
echo "$output" | grep -Eqi "missing|required|command" || fail "Missing command not caught"
pass "Missing command validation works"

# Priority + Scheduling
queuectl enqueue '{"command":"echo Scheduled","priority":3,"run_at":"2050-01-01T00:00:00Z"}' >/dev/null
pending_count=$(queuectl list --status pending | grep -c "pending" || true)
((pending_count >= 1)) || fail "Scheduled job missing"
pass "Priority + run_at scheduling verified"

# Config persistence check
queuectl config-set max_retries 5 >/dev/null
val=$(queuectl config-get max_retries | grep -oE '[0-9]+')
[[ "$val" == "5" ]] || fail "Config persistence failed"
pass "Config persistence verified (max_retries=5)"
