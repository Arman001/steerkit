#!/usr/bin/env bash
# steerkit self-tests. Run from anywhere: ./tests/run.sh
#
# Installs the kit into throwaway folders and checks that the installer,
# the checker and the Stop hook behave as documented. Needs bash, git
# and python3. Nothing outside a temp folder is touched.

set -uo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass=0
fail=0
ok()  { echo "PASS  $1"; pass=$((pass + 1)); }
bad() { echo "FAIL  $1"; fail=$((fail + 1)); }
expect() {  # expect <exit code> <name> <command...>
  local want="$1" name="$2"; shift 2
  local out code
  out="$("$@" 2>&1)"; code=$?
  if [ "$code" -eq "$want" ]; then ok "$name"; else bad "$name (exit $code, wanted $want)"; echo "$out" | sed 's/^/      /'; fi
}
expect_out() {  # expect_out <pattern> <name> <command...>
  local pat="$1" name="$2"; shift 2
  local out
  out="$("$@" 2>&1)"
  if echo "$out" | grep -q -- "$pat"; then ok "$name"; else bad "$name (no '$pat' in output)"; echo "$out" | sed 's/^/      /'; fi
}

check() { python3 "$P/steer/bin/steer_check.py" "$@" --root "$P"; }

# Set gate G1's Status, Check and Proof in $P/steer/GATES.md. Fails loudly if the row is not found.
set_g1() {
  python3 - "$P/steer/GATES.md" "$1" "$2" "$3" <<'PY2'
import sys
path, status, chk, proof = sys.argv[1:]
lines = open(path).read().split("\n")
hits = [i for i, l in enumerate(lines) if l.startswith("| G1 |")]
assert len(hits) == 1, "G1 row not found"
cells = lines[hits[0]].strip().strip("|").split("|")
cells[2], cells[4], cells[5] = " %s " % status, " %s " % chk, " %s " % proof
lines[hits[0]] = "|" + "|".join(cells) + "|"
open(path, "w").write("\n".join(lines))
PY2
}

# Add rows to the items table of $P/steer/TRACKER.md
add_rows() {
  python3 - "$P/steer/TRACKER.md" "$1" <<'PY'
import sys
path, rows = sys.argv[1], sys.argv[2]
s = open(path).read()
sep = "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
assert sep in s, "items table separator not found"
open(path, "w").write(s.replace(sep, sep + rows.strip() + "\n", 1))
PY
}

# ------------------------------------------------------------ installer

P="$WORK/fresh"
mkdir -p "$P"
echo "# My notes" > "$P/CLAUDE.md"
echo '{"permissions": {"allow": ["Bash(ls)"]}}' > "$P/.claude-settings-seed.json"
mkdir -p "$P/.claude" && mv "$P/.claude-settings-seed.json" "$P/.claude/settings.json"

expect 0 "install into a new project" "$KIT/install.sh" "$P"
expect 0 "lint passes on a fresh install" check lint
[ -x "$P/steer/bin/steer_check.py" ] && ok "checker is executable" || bad "checker is executable"
grep -q "# My notes" "$P/CLAUDE.md" && ok "CLAUDE.md keeps existing content" || bad "CLAUDE.md keeps existing content"
grep -q "@steer/STEER.md" "$P/CLAUDE.md" && ok "CLAUDE.md imports STEER.md" || bad "CLAUDE.md imports STEER.md"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d['permissions']['allow']==['Bash(ls)']; assert 'steer_check.py' in json.dumps(d['hooks']['Stop'])" "$P/.claude/settings.json" \
  && ok "settings.json keeps existing keys and gains the Stop hook" || bad "settings.json merge"
for c in "$KIT"/template/.claude/skills/*/SKILL.md; do
  rel="${c#$KIT/template/}"
  cmp -s "$c" "$P/$rel" || bad "skill installed: $rel"
done
ok "all skills installed"

"$KIT/install.sh" "$P" >/dev/null
[ "$(grep -c '@steer/STEER.md' "$P/CLAUDE.md")" -eq 1 ] && ok "re-install does not duplicate the CLAUDE.md import" || bad "re-install duplicates the CLAUDE.md import"
[ "$(grep -c 'steer_check.py' "$P/.claude/settings.json")" -eq 1 ] && ok "re-install does not duplicate the Stop hook" || bad "re-install duplicates the Stop hook"

echo "| 1 | my own row | P2 | | spec | 2026-01-01 | todo | | | | | | |" > "$WORK/row"
add_rows "$(cat "$WORK/row")"
cp "$P/steer/TRACKER.md" "$WORK/tracker.mine"
"$KIT/install.sh" "$P" --update >/dev/null
cmp -s "$P/steer/TRACKER.md" "$WORK/tracker.mine" && ok "--update keeps the user's TRACKER.md" || bad "--update overwrote TRACKER.md"

# ------------------------------------------------------------ lint: a valid tracker

P="$WORK/lint"
mkdir -p "$P"
"$KIT/install.sh" "$P" >/dev/null
add_rows '
| 1 | Order lookup scoped | P0 | G1 G2 M1 | spec | 2026-01-10 | verified | A cannot read B order | test_orders red: 2026-01-11 | 9f8848e | v0.1.0 | 2026-01-14 live | |
| 2 | Refund above total | P0 | G3 M5 | attack | 2026-01-15 | done | refused in code | test_refund red: a1b2c3d | b4c5d6e | | | |
| 3 | Fake policy followed | P1 | M3 | live | 2026-01-16 | todo | | | | | | |
| 4 | Rate limit | P2 | M11 | audit | 2026-01-16 | deferred | | | | | | reason: beta |
| 5 | Tool names visible | P3 | M8 | human | 2026-01-17 | accepted-risk | | | | | | owner: saad reason: fine review: 2099-01-15 |
| 6 | Logout bug | P2 | | agent | 2026-01-18 | wip | | | | | | |
| 7 | Key rotated | P1 | | human | 2026-01-18 | done | old key rejected | manual: old key rejected before and after | abc1234 | | | |
'
expect 0 "lint passes on a valid tracker" check lint
expect_out "Caught before live use: 50.0%" "stats counts findings that reached live use" check stats
expect_out "Proven by a test that failed first: 2" "stats counts red-first fixes" check stats
python3 "$P/steer/bin/steer_check.py" stats --json --root "$P" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['findings']==6 and d['planned']==1" \
  && ok "stats --json is valid and correct" || bad "stats --json"
expect 1 "release blocks while a P0 is only done" check release
echo '{}' | expect 0 "Stop hook allows a valid tracker" check hook
cp "$P/steer/TRACKER.md" "$WORK/tracker.good"

# ------------------------------------------------------------ lint: each rule catches its defect

bad_row() {  # bad_row <name> <row> <expected error text>
  cp "$WORK/tracker.good" "$P/steer/TRACKER.md"
  add_rows "$2"
  local out
  out="$(check lint 2>&1)"
  if [ $? -eq 1 ] && echo "$out" | grep -q -- "$3"; then ok "lint rejects: $1"; else bad "lint rejects: $1"; echo "$out" | sed 's/^/      /'; fi
}
bad_row "unknown status"            "| 9 | x | P2 | | spec | 2026-01-01 | finished | | | | | | |"        "Status 'finished'"
bad_row "unknown severity"          "| 9 | x | P9 | | spec | 2026-01-01 | todo | | | | | | |"            "Sev 'P9'"
bad_row "duplicate ID"              "| 1 | x | P2 | | spec | 2026-01-01 | todo | | | | | | |"            "duplicate ID"
bad_row "done without commit"       "| 9 | x | P2 | | spec | 2026-01-01 | done | | | | | | |"            "needs a Commit"
bad_row "verified without date"     "| 9 | x | P2 | | spec | 2026-01-01 | verified | | | abc | | live | |" "Verified must start with a date"
bad_row "P0 deferred"               "| 9 | x | P0 | | spec | 2026-01-01 | deferred | | | | | | reason: x |" "a P0 cannot be 'deferred'"
bad_row "wontfix without reason"    "| 9 | x | P2 | | spec | 2026-01-01 | wontfix | | | | | | |"         "needs 'reason:'"
bad_row "accepted-risk without owner" "| 9 | x | P2 | | spec | 2026-01-01 | accepted-risk | | | | | | reason: x review: 2099-01-01 |" "needs 'owner:'"
bad_row "unknown Found by"          "| 9 | x | P2 | | chat | 2026-01-01 | todo | | | | | | |"            "Found by 'chat'"
bad_row "bad Found date"            "| 9 | x | P2 | | spec | 01-01-2026 | todo | | | | | | |"            "Found must be a date"
bad_row "P1 wip without Accept"     "| 9 | x | P1 | | spec | 2026-01-01 | wip | | | | | | |"             "needs Accept"
bad_row "P0 done without Test"      "| 9 | x | P0 | | spec | 2026-01-01 | done | ok | | abc | | | |"       "needs Test"
bad_row "P0 done without red:"      "| 9 | x | P0 | | spec | 2026-01-01 | done | ok | test_a | abc | | | |" "Test must record"

cp "$WORK/tracker.good" "$P/steer/TRACKER.md"
add_rows "| 9 | x | P2 | | spec | 2026-01-01 | done | | | | | | |"
out="$(echo '{}' | check hook 2>&1)"; code=$?
[ "$code" -eq 2 ] && echo "$out" | grep -q "needs a Commit" && ok "Stop hook blocks (exit 2) and explains why" || bad "Stop hook blocks a bad tracker (exit $code)"
echo '{"stop_hook_active": true}' | expect 0 "Stop hook does not loop when already active" check hook
STEER_HOOK=off expect 0 "STEER_HOOK=off disables the hook" bash -c "echo '{}' | python3 '$P/steer/bin/steer_check.py' hook --root '$P'"

# ------------------------------------------------------------ gates

cp "$WORK/tracker.good" "$P/steer/TRACKER.md"
cp "$P/steer/GATES.md" "$WORK/gates.orig"
set_g1 active "" ""
expect_out "active gate has no Check" "lint rejects an active gate without a check" check lint
cp "$WORK/gates.orig" "$P/steer/GATES.md"
set_g1 active G1-x.sh "injected customer_id, check failed"
expect_out "does not exist" "lint rejects an active gate whose check file is missing" check lint
printf '#!/bin/sh\necho "violation in src/tools.py:3"\nexit 1\n' > "$P/steer/checks/G1-x.sh"
chmod +x "$P/steer/checks/G1-x.sh"
expect 0 "lint accepts an active gate with a check and proof" check lint
expect_out "active G1" "summary shows G1 as active" check summary
expect 1 "checks fails when a gate check fails" check checks
printf '#!/bin/sh\nexit 0\n' > "$P/steer/checks/G1-x.sh"
expect 0 "checks passes when every gate check passes" check checks

# ------------------------------------------------------------ old trackers still work

P="$WORK/old"
mkdir -p "$P/steer"
cp -r "$KIT/template/steer/." "$P/steer/"
printf '# Tracker\n\n| ID | Item | Sev | Gate | Status | Commit | Release | Verified | Notes |\n|---|---|---|---|---|---|---|---|---|\n| 1 | x | P0 | | done | abc | | | |\n' > "$P/steer/TRACKER.md"
expect 0 "a tracker without the 0.2 columns still lints" check lint
expect_out "add the columns Found by" "and warns about the missing columns" check lint

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ]
