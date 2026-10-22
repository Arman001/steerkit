---
name: steer-promote
description: Turn a finding or a candidate gate into an active gate with a named check that is proven by injecting the defect. Human-approved. Use when a class of bug has appeared and should never come back.
argument-hint: "[gate ID, or tracker ID of the finding]"
disable-model-invocation: true
---

Promote to an active gate: $ARGUMENTS

Findings become rules only when something enforces them. No named check, no gate.

## 1. Define the rule

- If promoting a tracker finding: write the general rule behind it, not the single bug. "Order lookup leaked" becomes "every lookup by ID is filtered by the session user".
- If it matches an existing candidate gate, use that ID. Otherwise propose the next free G number.
- Show the human the rule in one sentence and ask them to approve the wording.

## 2. Choose enforcement

- **mechanical** if a script can detect violations, even roughly. Prefer this.
- **review** only if no script can. Then the enforcement is the per-gate verdict table from `/steer-attack`, approved by the human.

## 3. Write the check (mechanical)

- Create `steer/checks/<GATE-ID>-<short-name>.<ext>`, executable, run from the project root, exit non-zero on violation, print file and line of each violation. Follow `steer/checks/README.md`.
- Run it on the current code. Fix real violations it finds, or log them as P0 tracker rows with Found by `gate` if they need more work.

## 4. Prove it

This step is not optional.

1. Inject the defect the gate is about into the code, in the smallest way possible.
2. Run the check. It must fail, and its output must point at the injected defect.
3. Remove the injected defect. Run the check again. It must pass.
4. Show the human both runs.

If the check does not fail on the injected defect, it does not count. Improve it or fall back to review enforcement.

## 5. Record

With the human's approval:
- In `steer/GATES.md`: fill Check (file name, or `steer-attack verdict` for review), Proof (one line on what was injected and that it failed), set Status to `active`, and add a changelog row with the date and the finding that led to it.
- Link the tracker finding's Notes to the gate ID.
- Run `python3 steer/bin/steer_check.py lint` and `python3 steer/bin/steer_check.py checks`.

If the human rejects the gate, add a changelog row saying it was rejected and why, so it is not proposed again.
