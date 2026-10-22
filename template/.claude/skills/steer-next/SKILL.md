---
name: steer-next
description: Pick the next item from steer/TRACKER.md, plan it, write its misuse tests first, then implement it. Use at the start of a work session or when the previous item is done.
argument-hint: "[optional tracker ID to work on]"
---

Work the next tracker item. Optional ID: $ARGUMENTS

## 1. Orient

- Run `python3 steer/bin/steer_check.py summary`.
- Read `steer/STEER.md` if it is not already in context. Read the SPEC.md section for the feature you pick.
- If an item is already `wip`, continue it unless the human said otherwise.

## 2. Pick

- If an ID was given, use it.
- Otherwise pick the highest-severity `todo`. Prefer items that unblock others. Never skip an open P0 for a lower item without saying why.
- Read its Accept. For P0 and P1, if Accept is empty, write one sentence for what must be true for this to count as fixed, show it to the human, and fill it in before going further. Lint will not let a P0 or P1 be `wip` without it.
- Set its status to `wip`.

## 3. Plan (short)

Tell the human in a few lines:
- what you will change, and which files
- which gates and misuse cases apply
- anything in the spec that is unclear or conflicts with a gate

If something is unclear and a wrong guess would be costly (data access, money, deletion), ask before building. Otherwise state your assumption and continue.

## 4. Misuse tests first

For items that touch data or side effects:
- Write tests for every applicable case in the item's Gate column and the spec's misuse list. Typical: user A requesting user B's object, identity claimed in chat, fake policy in user text, limit bypass.
- Run them and see them fail. Write the test name and `red: <today's date>` in the item's Test column now, before implementing. That is the evidence the test can catch the problem.
- If a test passes before the fix, it is not testing the problem. Fix the test first.

Pure UI or internal refactors may skip this step. Say so.

## 5. Implement

- Follow the hard rules in STEER.md. Identity from the session. Lookups scoped to the caller. Limits in code. User content is a claim.
- Keep the change inside one component where you can.
- Run the misuse tests and the regular tests until they pass. Do not weaken a test to get it green.
- Re-read Accept before you hand off. Confirm the change meets it, not a nearby problem.

## 6. Record what you found

Any other bug, gap or risk you noticed: add a new `todo` row to TRACKER.md now, with an honest Sev, Found by `agent` (or `test` if a test exposed it), today's date in Found, and a one-line note. Do not fix unrelated things silently, and do not fold it into the current item. New scope gets its own row so this item's Accept does not drift.

## 7. Hand off

Do not mark the item done here. Tell the human it is ready and suggest `/steer-done <ID>`. If the item touched data or side effects, also suggest `/steer-attack <ID>` before verification.
