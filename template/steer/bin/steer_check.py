#!/usr/bin/env python3
"""steerkit checker.

Usage:
  python3 steer/bin/steer_check.py lint      Validate TRACKER.md and GATES.md
  python3 steer/bin/steer_check.py checks    Run every mechanical check in steer/checks/
  python3 steer/bin/steer_check.py release   lint + checks + no open P0
  python3 steer/bin/steer_check.py summary   Counts, open P0s, next items
  python3 steer/bin/steer_check.py stats     What was found, by what, how fast it was closed (--json)
  python3 steer/bin/steer_check.py hook      Claude Code Stop hook (reads JSON on stdin)

Options:
  --root PATH   Project root. Defaults to the folder that contains steer/.

Exit codes: 0 ok, 1 problems found (2 in hook mode, which tells Claude Code to keep working).
Standard library only, Python 3.8+.
"""

import json
import os
import re
import subprocess
import sys
from datetime import date
from statistics import median
from pathlib import Path

STATUSES = ["todo", "wip", "done", "verified", "deferred", "accepted-risk", "wontfix"]
SEVERITIES = ["P0", "P1", "P2", "P3"]
CLOSED_FOR_RELEASE = {"verified", "accepted-risk"}
GATE_STATUSES = ["candidate", "active", "retired"]
ENFORCEMENT = ["mechanical", "review"]
TRACKER_COLS = ["id", "item", "sev", "gate", "status", "commit", "release", "verified", "notes"]
# Added in steerkit 0.2. Older trackers without them still lint, with a warning.
STATS_COLS = ["found by", "found", "accept", "test"]
# How an item entered the tracker. `spec` is planned work; everything else is a finding.
FOUND_BY = ["spec", "agent", "test", "gate", "attack", "audit", "live", "human", "user"]
# Findings that got past every automated layer and were caught in use.
ESCAPED = {"live", "human", "user"}
STRICT_SEV = {"P0", "P1"}  # Accept and Test are required for these
GATE_COLS = ["id", "rule", "status", "enforcement", "check", "proof", "source"]
IGNORED_CHECK_SUFFIXES = (".md", ".sample", ".txt")
CHECK_TIMEOUT = int(os.environ.get("STEER_CHECK_TIMEOUT", "300"))


# ---------------------------------------------------------------- parsing

def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    # allow escaped pipes inside cells
    cells = re.split(r"(?<!\\)\|", line)
    return [c.strip().replace("\\|", "|") for c in cells]


def is_separator(cells):
    return all(re.fullmatch(r":?-{2,}:?", c or "---") for c in cells)


def find_table(text, required):
    """Return (header, rows) for the first table whose header has all required columns.

    rows is a list of (line_number, dict).
    """
    lines = strip_comments(text).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|"):
            header = [c.lower() for c in split_row(line)]
            if all(r in header for r in required):
                rows = []
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith("|"):
                    cells = split_row(lines[j])
                    if not is_separator(cells):
                        cells += [""] * (len(header) - len(cells))
                        rows.append((j + 1, dict(zip(header, cells))))
                    j += 1
                return header, rows
        i += 1
    return None, []


def parse_date(text):
    """Date at the start of text (YYYY-MM-DD), or None."""
    m = re.match(r"\s*(\d{4})-(\d{2})-(\d{2})", text or "")
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def note_field(notes, key):
    """Value of `key:` in a Notes cell, up to the next `word:` key."""
    m = re.search(r"\b" + re.escape(key) + r"\s*:\s*(.*?)(?=\s+\w[\w-]*\s*:|$)", notes, flags=re.I)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------- lint

def lint_tracker(root, errors, warnings):
    path = root / "steer" / "TRACKER.md"
    if not path.exists():
        errors.append("steer/TRACKER.md is missing")
        return []
    header, rows = find_table(path.read_text(encoding="utf-8"), ["id", "status", "sev"])
    if header is None:
        errors.append("steer/TRACKER.md: no items table with ID, Sev and Status columns")
        return []
    missing = [c for c in TRACKER_COLS if c not in header]
    if missing:
        errors.append("steer/TRACKER.md: items table is missing columns: " + ", ".join(missing))
        return []

    has_stats = all(c in header for c in STATS_COLS)
    if not has_stats:
        warnings.append("steer/TRACKER.md: add the columns Found by, Found, Accept and Test "
                        "(see the template) so evidence and stats are recorded")

    seen = {}
    today = date.today()
    for ln, r in rows:
        rid = r["id"] or "?"
        where = "TRACKER.md line {} (ID {})".format(ln, rid)
        status = r["status"].lower()
        sev = r["sev"].upper()
        notes = r["notes"]

        if not r["id"]:
            errors.append("{}: missing ID".format(where))
        elif r["id"] in seen:
            errors.append("{}: duplicate ID, also on line {}".format(where, seen[r["id"]]))
        else:
            seen[r["id"]] = ln

        if sev not in SEVERITIES:
            errors.append("{}: Sev '{}' must be one of {}".format(where, r["sev"], ", ".join(SEVERITIES)))
        if status not in STATUSES:
            errors.append("{}: Status '{}' must be one of {}".format(where, r["status"], ", ".join(STATUSES)))
            continue

        if status in ("done", "verified") and not r["commit"]:
            errors.append("{}: '{}' needs a Commit".format(where, status))
        if status == "verified":
            if not r["verified"]:
                errors.append("{}: 'verified' needs the Verified column (date and how, e.g. 2026-10-26 live)".format(where))
            elif not parse_date(r["verified"]):
                errors.append("{}: Verified must start with a date, YYYY-MM-DD".format(where))
        if has_stats:
            lint_stats_fields(r, where, sev, status, today, errors, warnings)
        if status in ("deferred", "wontfix"):
            if sev == "P0":
                errors.append("{}: a P0 cannot be '{}'. Fix it, or use accepted-risk with an owner".format(where, status))
            if not note_field(notes, "reason"):
                errors.append("{}: '{}' needs 'reason:' in Notes".format(where, status))
        if status == "accepted-risk":
            for key in ("owner", "reason", "review"):
                if not note_field(notes, key):
                    errors.append("{}: 'accepted-risk' needs '{}:' in Notes".format(where, key))
            review = note_field(notes, "review")
            m = re.match(r"(\d{4})-(\d{2})-(\d{2})", review)
            if review and not m:
                errors.append("{}: 'review:' must be a date, YYYY-MM-DD".format(where))
            elif m:
                try:
                    if date(int(m.group(1)), int(m.group(2)), int(m.group(3))) < today:
                        warnings.append("{}: accepted risk is past its review date {}".format(where, review))
                except ValueError:
                    errors.append("{}: 'review:' is not a valid date".format(where))
        if r["release"] and status not in ("done", "verified", "accepted-risk"):
            warnings.append("{}: has a Release but status is '{}'".format(where, status))
    return rows


def lint_stats_fields(r, where, sev, status, today, errors, warnings):
    found_by = r["found by"].lower()
    if not found_by:
        errors.append("{}: needs Found by ({})".format(where, ", ".join(FOUND_BY)))
    elif found_by not in FOUND_BY:
        errors.append("{}: Found by '{}' must be one of {}".format(where, r["found by"], ", ".join(FOUND_BY)))

    found = parse_date(r["found"])
    if not r["found"]:
        errors.append("{}: needs Found (YYYY-MM-DD, the day it entered the tracker)".format(where))
    elif not found:
        errors.append("{}: Found must be a date, YYYY-MM-DD".format(where))
    elif found > today:
        warnings.append("{}: Found date {} is in the future".format(where, r["found"]))
    verified = parse_date(r["verified"])
    if found and verified and verified < found:
        warnings.append("{}: Verified date is before the Found date".format(where))

    if sev not in STRICT_SEV:
        return
    if status in ("wip", "done", "verified") and not r["accept"]:
        errors.append("{}: a {} item needs Accept (what must be true for it to count as fixed) "
                      "before work starts".format(where, sev))
    if status in ("done", "verified"):
        test = r["test"]
        if not test:
            errors.append("{}: a {} item marked '{}' needs Test: the test name and `red:` "
                          "(when it was seen failing before the fix)".format(where, sev, status))
        elif not (note_field(test, "red") or note_field(test, "manual")):
            errors.append("{}: Test must record `red: <when it failed before the fix>`, or "
                          "`manual: <how it was checked before and after>` if no automated test is possible".format(where))


def lint_gates(root, errors, warnings):
    path = root / "steer" / "GATES.md"
    if not path.exists():
        warnings.append("steer/GATES.md is missing")
        return []
    header, rows = find_table(path.read_text(encoding="utf-8"), ["id", "status", "enforcement"])
    if header is None:
        errors.append("steer/GATES.md: no gates table with ID, Status and Enforcement columns")
        return []
    missing = [c for c in GATE_COLS if c not in header]
    if missing:
        errors.append("steer/GATES.md: gates table is missing columns: " + ", ".join(missing))
        return []

    seen = set()
    checks_dir = root / "steer" / "checks"
    for ln, g in rows:
        gid = g["id"] or "?"
        where = "GATES.md line {} ({})".format(ln, gid)
        status = g["status"].lower()
        enf = g["enforcement"].lower()
        if gid in seen:
            errors.append("{}: duplicate gate ID".format(where))
        seen.add(gid)
        if status not in GATE_STATUSES:
            errors.append("{}: Status '{}' must be one of {}".format(where, g["status"], ", ".join(GATE_STATUSES)))
            continue
        if enf not in ENFORCEMENT:
            errors.append("{}: Enforcement '{}' must be mechanical or review".format(where, g["enforcement"]))
            continue
        if status != "active":
            continue
        if not g["check"]:
            errors.append("{}: active gate has no Check. No named check, no gate. Set it back to candidate".format(where))
        if not g["proof"]:
            errors.append("{}: active gate has no Proof. Inject the defect, confirm the check fails, record how".format(where))
        if enf == "mechanical" and g["check"]:
            name = g["check"].strip("` ")
            f = checks_dir / Path(name).name
            if not f.exists():
                errors.append("{}: check file steer/checks/{} does not exist".format(where, f.name))
            elif not os.access(str(f), os.X_OK):
                errors.append("{}: check file steer/checks/{} is not executable (chmod +x)".format(where, f.name))
    return rows


# ---------------------------------------------------------------- checks

def list_checks(root):
    d = root / "steer" / "checks"
    if not d.is_dir():
        return [], []
    run, skipped = [], []
    for f in sorted(d.iterdir()):
        if f.is_dir() or f.name.startswith(".") or f.name.endswith(IGNORED_CHECK_SUFFIXES):
            continue
        if os.access(str(f), os.X_OK):
            run.append(f)
        else:
            skipped.append(f)
    return run, skipped


def run_checks(root, errors, warnings, quiet=False):
    run, skipped = list_checks(root)
    for f in skipped:
        warnings.append("steer/checks/{} is not executable and was skipped".format(f.name))
    if not run:
        if not quiet:
            print("steer: no executable checks in steer/checks/")
        return
    for f in run:
        try:
            p = subprocess.run([str(f)], cwd=str(root), stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=CHECK_TIMEOUT)
            out = p.stdout.decode("utf-8", "replace").strip()
            code = p.returncode
        except subprocess.TimeoutExpired:
            out, code = "timed out after {}s".format(CHECK_TIMEOUT), 124
        except OSError as e:
            out, code = str(e), 126
        if code == 0:
            if not quiet:
                print("PASS  {}".format(f.name))
        else:
            if not quiet:
                print("FAIL  {}".format(f.name))
            tail = "\n".join(out.splitlines()[-20:])
            errors.append("check {} failed (exit {}):\n{}".format(f.name, code, tail))


# ---------------------------------------------------------------- commands

def report(errors, warnings, stream=sys.stdout):
    for w in warnings:
        print("warning: " + w, file=stream)
    for e in errors:
        print("error: " + e, file=stream)


def cmd_lint(root):
    errors, warnings = [], []
    lint_tracker(root, errors, warnings)
    lint_gates(root, errors, warnings)
    report(errors, warnings)
    if not errors:
        print("steer lint: ok")
    return 1 if errors else 0


def cmd_checks(root):
    errors, warnings = [], []
    run_checks(root, errors, warnings)
    report(errors, warnings)
    return 1 if errors else 0


def cmd_release(root):
    errors, warnings = [], []
    rows = lint_tracker(root, errors, warnings)
    lint_gates(root, errors, warnings)
    for ln, r in rows:
        sev, status = r["sev"].upper(), r["status"].lower()
        if sev == "P0" and status not in CLOSED_FOR_RELEASE:
            errors.append("release blocked: P0 item {} ('{}') is '{}'".format(r["id"], r["item"], status))
        if sev == "P1" and status not in CLOSED_FOR_RELEASE | {"done"}:
            warnings.append("P1 item {} ('{}') is still '{}'".format(r["id"], r["item"], status))
    run_checks(root, errors, warnings)
    report(errors, warnings)
    print("steer release: " + ("BLOCKED" if errors else "ok"))
    return 1 if errors else 0


def cmd_summary(root):
    errors, warnings = [], []
    rows = lint_tracker(root, errors, warnings)
    gates = lint_gates(root, errors, warnings)
    counts = {s: 0 for s in STATUSES}
    for _, r in rows:
        s = r["status"].lower()
        if s in counts:
            counts[s] += 1
    print("Tracker: " + ", ".join("{} {}".format(v, k) for k, v in counts.items() if v) if rows else "Tracker: empty")
    open_p0 = [r for _, r in rows if r["sev"].upper() == "P0" and r["status"].lower() not in CLOSED_FOR_RELEASE]
    if open_p0:
        print("Open P0:")
        for r in open_p0:
            print("  {}  {}  [{}]".format(r["id"], r["item"], r["status"]))
    wip = [r for _, r in rows if r["status"].lower() == "wip"]
    if wip:
        print("In progress:")
        for r in wip:
            print("  {}  {}".format(r["id"], r["item"]))
    todo = [r for _, r in rows if r["status"].lower() == "todo"]
    todo.sort(key=lambda r: SEVERITIES.index(r["sev"].upper()) if r["sev"].upper() in SEVERITIES else 9)
    if todo:
        print("Next up:")
        for r in todo[:5]:
            print("  {}  {}  {}".format(r["id"], r["sev"], r["item"]))
    unverified = [r for _, r in rows if r["status"].lower() == "done"]
    if unverified:
        print("Done, awaiting verification: " + ", ".join(r["id"] for r in unverified))
    if gates:
        by = {}
        for _, g in gates:
            by.setdefault(g["status"].lower(), []).append(g["id"])
        print("Gates: " + "; ".join("{} {}".format(k, " ".join(v)) for k, v in by.items()))
    if errors or warnings:
        print()
        report(errors, warnings)
    return 0


def kit_version(root):
    """steerkit version and commit from steer/VERSION, written by the installer."""
    path = root / "steer" / "VERSION"
    if not path.exists():
        return "unknown"
    info = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            info[k.strip()] = v.strip()
    return "{} ({})".format(info.get("version", "unknown"), info.get("commit", "unknown"))


def days(a, b):
    return (b - a).days if a and b else None


def fmt_days(values):
    return "{:g} days".format(median(values)) if values else "n/a"


def cmd_stats(root, as_json=False):
    errors, warnings = [], []
    rows = [r for _, r in lint_tracker(root, errors, warnings)]
    gates = [g for _, g in lint_gates(root, errors, warnings)]
    today = date.today()

    def fb(r):
        return r.get("found by", "").lower() or "unknown"

    planned = [r for r in rows if fb(r) == "spec"]
    findings = [r for r in rows if fb(r) != "spec"]
    by_source = {}
    for r in findings:
        sev = r["sev"].upper()
        by_source.setdefault(fb(r), {}).setdefault(sev, 0)
        by_source[fb(r)][sev] += 1
    escaped = [r for r in findings if fb(r) in ESCAPED]
    known = [r for r in findings if fb(r) != "unknown"]

    closed = [r for r in rows if r["status"].lower() in ("done", "verified")]
    strict_closed = [r for r in closed if r["sev"].upper() in STRICT_SEV]
    red = [r for r in strict_closed if note_field(r.get("test", ""), "red")]
    manual = [r for r in strict_closed if not note_field(r.get("test", ""), "red")
              and note_field(r.get("test", ""), "manual")]

    to_verify = [days(parse_date(r.get("found")), parse_date(r["verified"]))
                 for r in rows if r["status"].lower() == "verified"]
    to_verify = [d for d in to_verify if d is not None]
    p0_verify = [days(parse_date(r.get("found")), parse_date(r["verified"]))
                 for r in rows if r["status"].lower() == "verified" and r["sev"].upper() == "P0"]
    p0_verify = [d for d in p0_verify if d is not None]
    open_age = [days(parse_date(r.get("found")), today) for r in rows
                if r["status"].lower() in ("todo", "wip", "done")]
    open_age = [d for d in open_age if d is not None]
    overdue = [r for r in rows if r["status"].lower() == "accepted-risk"
               and parse_date(note_field(r["notes"], "review"))
               and parse_date(note_field(r["notes"], "review")) < today]

    status_counts = {s: 0 for s in STATUSES}
    for r in rows:
        if r["status"].lower() in status_counts:
            status_counts[r["status"].lower()] += 1
    gate_counts = {s: 0 for s in GATE_STATUSES}
    for g in gates:
        if g["status"].lower() in gate_counts:
            gate_counts[g["status"].lower()] += 1

    data = {
        "date": today.isoformat(),
        "steerkit": kit_version(root),
        "items": len(rows),
        "planned": len(planned),
        "findings": len(findings),
        "findings_by_source": by_source,
        "escaped_to_live": len(escaped),
        "caught_before_live_pct": round(100.0 * (len(known) - len(escaped)) / len(known), 1) if known else None,
        "status": status_counts,
        "p0_p1_closed": len(strict_closed),
        "p0_p1_closed_red_first": len(red),
        "p0_p1_closed_manual": len(manual),
        "median_days_found_to_verified": median(to_verify) if to_verify else None,
        "median_days_found_to_verified_p0": median(p0_verify) if p0_verify else None,
        "median_days_open": median(open_age) if open_age else None,
        "accepted_risk_overdue": len(overdue),
        "gates": gate_counts,
    }
    if as_json:
        print(json.dumps(data, indent=2))
        return 0

    print("steer stats, {}, steerkit {}".format(data["date"], data["steerkit"]))
    print()
    print("Items: {} total, {} planned (spec), {} findings".format(len(rows), len(planned), len(findings)))
    if by_source:
        print()
        print("Findings by how they were found:")
        print("  {:<8} {:>5} {:>4} {:>4} {:>4} {:>4}".format("source", "total", "P0", "P1", "P2", "P3"))
        for src in FOUND_BY + ["unknown"]:
            if src in by_source:
                c = by_source[src]
                print("  {:<8} {:>5} {:>4} {:>4} {:>4} {:>4}".format(
                    src, sum(c.values()), *(c.get(s, 0) for s in SEVERITIES)))
        if known:
            print()
            print("Caught before live use: {}% ({} of {} findings reached live, human or user)".format(
                data["caught_before_live_pct"], len(escaped), len(known)))
    print()
    print("Status: " + ", ".join("{} {}".format(v, k) for k, v in status_counts.items() if v) if rows else "Status: empty")
    if strict_closed:
        print("P0/P1 closed: {}. Proven by a test that failed first: {}. Checked manually: {}".format(
            len(strict_closed), len(red), len(manual)))
    print("Median days found to verified: {} (P0: {})".format(fmt_days(to_verify), fmt_days(p0_verify)))
    print("Median age of open items: {}".format(fmt_days(open_age)))
    if overdue:
        print("Accepted risks past review date: {}".format(", ".join(r["id"] for r in overdue)))
    if gates:
        print("Gates: " + ", ".join("{} {}".format(v, k) for k, v in gate_counts.items() if v))
    if errors:
        print()
        print("Note: the tracker has lint errors, so these numbers may be off. Run lint.")
    return 0


def cmd_hook(root):
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        payload = {}
    if os.environ.get("STEER_HOOK", "").lower() in ("off", "0", "false"):
        return 0
    if not (root / "steer" / "TRACKER.md").exists():
        return 0
    errors, warnings = [], []
    lint_tracker(root, errors, warnings)
    lint_gates(root, errors, warnings)
    if os.environ.get("STEER_CHECKS_ON_STOP", "") in ("1", "true", "on"):
        run_checks(root, errors, warnings, quiet=True)
    if not errors:
        return 0
    if payload.get("stop_hook_active"):
        # Already blocked once this turn. Let the turn end instead of looping,
        # and leave the problems visible.
        print("steer: tracker still has problems, run `python3 steer/bin/steer_check.py lint`", file=sys.stderr)
        return 0
    print("steer: the tracker or gates break the steer rules. Fix these before finishing:", file=sys.stderr)
    for e in errors:
        print("- " + e, file=sys.stderr)
    print("Do not mark items done or verified without the required evidence. "
          "If something cannot be fixed now, record it with the right status and reason.", file=sys.stderr)
    return 2


def find_root(argv):
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 < len(argv):
            return Path(argv[i + 1]).resolve()
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env and (Path(env) / "steer").is_dir():
        return Path(env).resolve()
    here = Path(__file__).resolve()
    if here.parent.name == "bin" and here.parent.parent.name == "steer":
        return here.parent.parent.parent
    return Path.cwd()


def main(argv):
    commands = {"lint": cmd_lint, "checks": cmd_checks, "release": cmd_release,
                "summary": cmd_summary, "stats": cmd_stats, "hook": cmd_hook}
    args = [a for a in argv[1:] if not a.startswith("--")]
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 < len(argv) and argv[i + 1] in args:
            args.remove(argv[i + 1])
    if not args or args[0] not in commands:
        print(__doc__)
        return 1
    if args[0] == "stats":
        return cmd_stats(find_root(argv), as_json="--json" in argv)
    return commands[args[0]](find_root(argv))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
