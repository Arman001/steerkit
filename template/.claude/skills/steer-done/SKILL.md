---
name: steer-done
description: Close a tracker item as done with evidence (tests run, commit hash), after implementation is complete. Use when an item from /steer-next is finished.
argument-hint: "[tracker ID]"
---

Close tracker item: $ARGUMENTS (if empty, use the item currently `wip`).

## Checks before closing

1. Run the project's tests, including the misuse tests for this item. All must pass. If any fail, stop and report. Do not mark done.
2. Run `python3 steer/bin/steer_check.py checks`. If an active gate's check fails, the item is not done.
3. Re-read the item's Gate column. For each listed gate or misuse case, confirm in one line how it is covered (test name, or why it does not apply).
4. Re-read the item's Accept. State in one line how the change meets it. If it does not, the item is not done.
5. For P0 and P1, check the Test column names the proving test and has `red:` from when it failed before the fix. If the test was never seen failing, run the red check below, then record `red:`. If no automated test is possible, record `manual: <how it was checked before and after>` and tell the human.

## Red check (only when the test was never seen failing)

This temporarily removes the fix to watch the test fail. It must never touch anything else in the working tree.

Fix files are the implementation files of this item only, not its test files. List them before starting.

1. **Refuse if there is other work in the tree.** Run `git status --porcelain=v1 --untracked-files=all`. If anything is listed that is not a fix file or a test file of this item, stop and ask the human. Do not stash, commit or discard it.
2. **If the fix is already committed**, stop and ask the human. Do not revert, reset or rewrite history.
3. **Record the state** in files, since shell variables do not survive between commands:
   ```bash
   g=$(git rev-parse --git-dir)
   git ls-files -o --exclude-standard > "$g/steer-red-untracked"
   git stash list | wc -l > "$g/steer-red-stashes"
   { git status --porcelain=v1 --untracked-files=no; git diff HEAD --binary; tr '\n' '\0' < "$g/steer-red-untracked" | xargs -0 -r sha256sum; } | sha256sum > "$g/steer-red-before"
   ```
4. **Remove the fix:** `git stash push --include-untracked -m "steer red check <ID>" -- <fix files>`. Then confirm `git stash list | wc -l` is one more than the number in `$g/steer-red-stashes`. If not, nothing was stashed: stop and do not pop.
5. **Run the proving test.** It must fail. Note the date.
6. **Restore:** `git stash pop --index`. If it reports a conflict or error, stop and tell the human. The stash is still in `git stash list`. Do not try to fix it with reset or checkout.
7. **Confirm** the tree matches step 3:
   ```bash
   g=$(git rev-parse --git-dir)
   { git status --porcelain=v1 --untracked-files=no; git diff HEAD --binary; tr '\n' '\0' < "$g/steer-red-untracked" | xargs -0 -r sha256sum; } | sha256sum | cmp - "$g/steer-red-before" && echo "tree matches"
   [ "$(git stash list | wc -l)" -eq "$(cat "$g/steer-red-stashes")" ] && echo "stash list matches"
   git ls-files -o --exclude-standard | grep -vxF -f "$g/steer-red-untracked"
   ```
   Both lines must print. If not, stop and tell the human what differs. The last command lists untracked files that appeared during the check, usually test caches. Mention them, but they are not a failure. Then `rm "$g"/steer-red-*`.
8. Run the test again. It must pass.

Never use `git checkout -- .`, `git restore .`, `git reset --hard` or `git clean` in this check.

## Commit

If the work is not committed yet, ask the human whether to commit now. Commit only with their agreement, with a message that references the tracker ID.

## Update the tracker

- Status: `done`
- Commit: the short hash
- Test: as above
- Release: leave blank unless the human tells you this is shipping in a named release. If so, fill it in.
- Notes: one line on how it was tested, e.g. `misuse M1 M3 pass, 14 unit, 3 integration`

Never set `verified` here. Verification needs a live test or the human's confirmation, via `/steer-verify`.

## Finish

Run `python3 steer/bin/steer_check.py lint` and fix anything it reports.

Tell the human in two or three lines: what was closed, the evidence, and what remains for verification. If the item touched data or side effects and has not had an attack pass, suggest `/steer-attack <ID>` in a fresh session.
