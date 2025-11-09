#!/bin/bash
set -e
source "$(dirname "$0")/utils.sh"

info "Running Config Tests"

queuectl config-set max_retries 7 >/dev/null
val=$(queuectl config-get max_retries | grep -oE '[0-9]+')
[[ "$val" == "7" ]] || fail "Config set/get failed"
pass "Config set/get verified"

queuectl config-reset >/dev/null
val=$(queuectl config-get max_retries | grep -oE '[0-9]+')
[[ "$val" == "3" ]] || fail "Config reset failed"
pass "Config reset verified"
