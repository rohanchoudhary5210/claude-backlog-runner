#!/usr/bin/env bash
# Tests for scripts/statusline_capture.sh
set -u
here="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"
fail=0

out=$(echo '{"rate_limits":{"five_hour":{"used_percentage":12,"resets_at":9999999999}}}' \
  | BACKLOG_USAGE_FILE="$tmp/u.json" bash "$here/scripts/statusline_capture.sh")
grep -q '"five_hour"' "$tmp/u.json" 2>/dev/null || { echo "FAIL: usage file not written"; fail=1; }
grep -q '"captured_at"' "$tmp/u.json" 2>/dev/null || { echo "FAIL: captured_at missing"; fail=1; }
[[ "$out" == "5h 12"* ]] || { echo "FAIL: stdout was '$out'"; fail=1; }

out=$(echo '{"model":{}}' | BACKLOG_USAGE_FILE="$tmp/none/u.json" bash "$here/scripts/statusline_capture.sh")
[[ "$out" == "usage n/a" ]] || { echo "FAIL: expected 'usage n/a', got '$out'"; fail=1; }
[[ ! -e "$tmp/none/u.json" ]] || { echo "FAIL: file created without rate_limits"; fail=1; }

rm -rf "$tmp"
[[ $fail == 0 ]] && echo "statusline tests: PASS"
exit $fail
