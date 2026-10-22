---
name: steer-attack
description: Adversarial pass on a tracker item or the whole system. Try to break it as a misuser would, give a written verdict per gate, and log findings in the tracker. Best run in a fresh session, not the one that wrote the code.
argument-hint: "[tracker ID, feature name, or 'all']"
---

Your job in this pass is to break the system, not to defend it. Target: $ARGUMENTS

If you wrote the code under attack earlier in this same session, say so at the top of your report. A fresh session is less likely to share the same blind spots. A different model is better still, since the same model can miss the same things in a fresh session. If the human can run this pass with another model or agent, suggest it.

## 1. Load the rules, not the reasoning

Read `steer/GATES.md`, `steer/MISUSE.md`, the relevant SPEC.md sections and the tracker rows for the target. Then read the code. Do not rely on comments or commit messages to tell you what the code does.

## 2. Attack

For every applicable misuse case, and anything else you can think of:
- Find the code path a misuser would take: API route, agent tool, background job, export, search.
- Check the actual guard: where identity comes from, how lookups are filtered, where limits are checked, whether user or retrieved text can change behaviour.
- Where the project lets you, run it: call the tool or endpoint as user A against user B's data, send a fake policy, exceed a limit, split a limit across requests. Prefer running over reading.

Look especially at the boundaries between components. Problems collect where one part assumes another part checked something.

## 3. Verdict per gate

Write a short report:

| Gate | Verdict | Evidence |
|---|---|---|
| G1 | holds / violated / not applicable | file:line, test, or what you ran |

Include candidate gates too. For review-enforced gates, this table is the enforcement. The human approves it.

## 4. Log findings

For each problem found, add a `todo` row to `steer/TRACKER.md`:
- Sev: P0 if it leaks data, moves money, or bypasses a limit. Otherwise judge honestly.
- Found by: `attack`. Found: today's date
- Accept: one sentence for what must be true once it is fixed
- Gate: the gate and misuse IDs it relates to
- Notes: how to reproduce in one line

If the same kind of problem appears that is not covered by any misuse case, add it to the project-specific section of `steer/MISUSE.md`.

## 5. Report

Lead with the most serious finding. If nothing was found, say what you tried, so the human can judge how thorough the pass was. Do not fix anything in this pass unless the human asks.

If a finding is a pattern that could come back, suggest `/steer-promote` to turn it into a gate.
