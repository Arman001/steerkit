#!/usr/bin/env bash
# steerkit installer
#
#   ./install.sh /path/to/your/project              install, never overwrites your files
#   ./install.sh /path/to/your/project --update     also refresh steerkit tooling (skills, checker, STEER.md)
#   ./install.sh /path/to/your/project --agents-md  also point AGENTS.md at the rules (Codex, Cursor, others)
#
# Your own files (SPEC.md, TRACKER.md, GATES.md, TARGETS.md, MISUSE.md, your checks) are never overwritten.

set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$KIT_DIR/template"

TARGET=""
UPDATE=0
AGENTS_MD=0
for arg in "$@"; do
  case "$arg" in
    --update) UPDATE=1 ;;
    --agents-md) AGENTS_MD=1 ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) TARGET="$arg" ;;
  esac
done

if [ -z "$TARGET" ]; then
  echo "usage: ./install.sh /path/to/project [--update] [--agents-md]"
  exit 1
fi
mkdir -p "$TARGET"
TARGET="$(cd "$TARGET" && pwd)"
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }

# Files steerkit owns and may refresh with --update
TOOLING=(
  "steer/STEER.md"
  "steer/bin/steer_check.py"
  "steer/checks/README.md"
  "steer/checks/G1-no-identity-params.sh.sample"
)

copy_file() {  # copy_file <relative path> <overwrite 0|1>
  local rel="$1" overwrite="$2"
  local from="$SRC/$rel" to="$TARGET/$rel"
  mkdir -p "$(dirname "$to")"
  if [ -e "$to" ] && [ "$overwrite" -ne 1 ]; then
    echo "  keep    $rel"
  else
    cp "$from" "$to"
    echo "  write   $rel"
  fi
}

echo "Installing steerkit into $TARGET"

# 1. steer/ folder
while IFS= read -r -d '' f; do
  rel="${f#$SRC/}"
  overwrite=0
  if [ "$UPDATE" -eq 1 ]; then
    for t in "${TOOLING[@]}"; do [ "$rel" = "$t" ] && overwrite=1; done
  fi
  copy_file "$rel" "$overwrite"
done < <(find "$SRC/steer" -type f -print0 | sort -z)
chmod +x "$TARGET/steer/bin/steer_check.py"

# Record which steerkit this project runs, so rules and stats can be traced to a version.
# Rewritten on every install and --update.
KIT_VERSION="$(cat "$KIT_DIR/VERSION" 2>/dev/null || echo unknown)"
KIT_COMMIT="$(git -C "$KIT_DIR" rev-parse --short HEAD 2>/dev/null || true)"
if [ -n "$KIT_COMMIT" ] && [ -n "$(git -C "$KIT_DIR" status --porcelain 2>/dev/null)" ]; then
  KIT_COMMIT="$KIT_COMMIT+dirty"
fi
{
  printf 'version: %s\n' "$KIT_VERSION"
  [ -n "$KIT_COMMIT" ] && printf 'commit: %s\n' "$KIT_COMMIT"
  printf 'installed: %s\n' "$(date +%Y-%m-%d)"
} > "$TARGET/steer/VERSION"
echo "  write   steer/VERSION (steerkit $KIT_VERSION${KIT_COMMIT:+, $KIT_COMMIT})"

# 2. Claude Code skills
while IFS= read -r -d '' f; do
  rel="${f#$SRC/}"
  copy_file "$rel" "$UPDATE"
done < <(find "$SRC/.claude/skills" -type f -print0 | sort -z)

# 3. Stop hook in .claude/settings.json (merged, never replaced)
SETTINGS="$TARGET/.claude/settings.json"
mkdir -p "$TARGET/.claude"
python3 - "$SETTINGS" "$SRC/.claude/settings.json" <<'PY'
import json, sys, os
target, source = sys.argv[1], sys.argv[2]
hook = json.load(open(source))["hooks"]["Stop"][0]
if os.path.exists(target):
    try:
        data = json.load(open(target))
    except ValueError:
        print("  skip    .claude/settings.json is not valid JSON. Add the Stop hook from template/.claude/settings.json by hand")
        sys.exit(0)
else:
    data = {}
stops = data.setdefault("hooks", {}).setdefault("Stop", [])
if "steer_check.py" in json.dumps(stops):
    print("  keep    .claude/settings.json (steer Stop hook already present)")
else:
    stops.append(hook)
    with open(target, "w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    print("  merge   .claude/settings.json (added steer Stop hook)")
PY

# 4. CLAUDE.md imports the rules
CLAUDE_MD="$TARGET/CLAUDE.md"
if [ -f "$CLAUDE_MD" ] && grep -q "@steer/STEER.md" "$CLAUDE_MD"; then
  echo "  keep    CLAUDE.md (already imports steer/STEER.md)"
else
  {
    [ -s "$CLAUDE_MD" ] && echo
    echo "## Steer"
    echo
    echo "This project follows the steerkit rules. Read and follow them every session:"
    echo
    echo "@steer/STEER.md"
  } >> "$CLAUDE_MD"
  echo "  append  CLAUDE.md (imports steer/STEER.md)"
fi

# 5. Optional AGENTS.md pointer for other coding agents
if [ "$AGENTS_MD" -eq 1 ]; then
  AGENTS="$TARGET/AGENTS.md"
  if [ -f "$AGENTS" ] && grep -q "steer/STEER.md" "$AGENTS"; then
    echo "  keep    AGENTS.md"
  else
    {
      [ -s "$AGENTS" ] && echo
      echo "## Steer"
      echo
      echo "Before any work, read steer/STEER.md and follow it. Workflow prompts are in .claude/skills/steer-*/SKILL.md."
      echo "Run \`python3 steer/bin/steer_check.py lint\` before finishing any task."
    } >> "$AGENTS"
    echo "  append  AGENTS.md"
  fi
fi

echo
python3 "$TARGET/steer/bin/steer_check.py" lint --root "$TARGET" || true
echo
echo "Done. Next: open the project in Claude Code and run /steer-spec <what you are building>"
