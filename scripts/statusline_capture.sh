#!/usr/bin/env bash
# Claude Code statusLine command: saves rate_limits for the backlog runner
# and prints a short usage line.
input=$(cat)
file="${BACKLOG_USAGE_FILE:-$HOME/.claude/backlog-runner/usage.json}"
rl=$(printf '%s' "$input" | jq -c '.rate_limits // empty' 2>/dev/null)

if [ -z "$rl" ] || [ "$rl" = "{}" ]; then
  echo "usage n/a"
  exit 0
fi

mkdir -p "$(dirname "$file")"
printf '%s\n' "$rl" > "$file.tmp" && mv "$file.tmp" "$file"

five=$(printf '%s' "$rl" | jq -r '.five_hour.used_percentage // empty | floor')
seven=$(printf '%s' "$rl" | jq -r '.seven_day.used_percentage // empty | floor')
echo "5h ${five:-?}% · 7d ${seven:-?}%"
