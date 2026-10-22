---
name: steer-verify
description: Verify a done tracker item with a live test the human runs or confirms, then mark it verified. Human-driven; only the human can confirm verification.
argument-hint: "[tracker ID]"
disable-model-invocation: true
---

Verify tracker item: $ARGUMENTS (if empty, list items with status `done` and ask which).

Verification means the item works in the running product, used the way a real user would use it and the way a misuser would try to abuse it. Tests passing is `done`, not `verified`.

## 1. Prepare a live test script

From the item, its spec section and its misuse cases, write a short checklist the human can run in the live app (local, staging or a preview environment). Include:
- the happy path, as a real user
- each applicable misuse attempt, with exactly what to type or do, and what should happen
- anything to check in logs or data afterwards

Keep it to what fits in ten minutes. If you can run parts of it yourself against a running instance, do that and report results, but the human still confirms.

## 2. Wait for the result

Ask the human to run it and report back. Do not assume a result.

## 3. Record

- **All passed, and the human confirms:** set Status to `verified` and Verified to `<today's date> live` (or `human` if they confirmed without running the checklist). Keep the Commit.
- **Something failed:** leave the item `done` or set it back to `wip`, and add a `todo` row for each failure with Sev, Found by `live` (or `human` if the human spotted it outside the checklist), today's date in Found, and a reproduction note. These rows matter: they are the problems that got past every automated layer.

Run `python3 steer/bin/steer_check.py lint` and fix anything it reports.
