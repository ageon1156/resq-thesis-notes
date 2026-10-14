#!/usr/bin/env bash
# Counts, per source file changed since the upstream fork point, how many lines at HEAD
# git-blame attributes to the user's identity vs. everyone else.
# Usage: bash thesis-review/scripts/blame_ownership.sh [FORK] [AUTHOR_EMAIL_REGEX]
# Mechanical commits 4bb4dd75f ("touch all files") and 845fb5d58 ("remove all comments") are
# ignored so their whitespace/blank-line edits are attributed to the prior author.
# Output: TSV  file  own_lines  other_lines  total
FORK=${1:-9266caae9}
ME=${2:-ageon1156}
git diff --name-only --diff-filter=AMR "$FORK" HEAD -- '*.kt' '*.java' '*.kts' '*.cpp' '*.py' |
while read -r f; do
  [ -f "$f" ] || continue
  case "$f" in *codec2/*) continue;; esac
  git blame --line-porcelain -w --ignore-rev 4bb4dd75f --ignore-rev 845fb5d58 HEAD -- "$f" 2>/dev/null |
    awk -v f="$f" -v me="$ME" '/^author-mail /{t++; if ($0 ~ me) o++} END {printf "%s\t%d\t%d\t%d\n", f, o, t-o, t}'
done
