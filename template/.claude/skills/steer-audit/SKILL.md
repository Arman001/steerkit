---
name: steer-audit
description: Full phased audit of the codebase against steer gates, targets and misuse cases. Findings become prioritised tracker rows. Use after a milestone, before a release, or when taking over an existing codebase.
argument-hint: "[optional area to focus on]"
---

Audit the system. Optional focus: $ARGUMENTS

This is a sweep, not a fix session. Do not change application code. Only write to `steer/TRACKER.md` and, if needed, the project-specific section of `steer/MISUSE.md`.

## 1. Map

Read SPEC.md, GATES.md, TARGETS.md and the tracker. Then map the real system: entry points (routes, agent tools, jobs, webhooks), data stores, external services, and where identity and policy come from. Note anything in the code that the spec does not mention. Undocumented paths are where gaps hide.

## 2. Audit in phases

Work through these in order and keep findings separate per phase.

- **Phase 0, release blockers:** cross-user or cross-tenant data access, identity taken from model or request input, limits only in prompts, policies changeable by user or retrieved content, secrets in code or prompts, agent writes to production. Anything here is P0.
- **Phase 1, security and correctness:** remaining misuse cases, role checks, field-level protection, unsafe output handling, missing confirmation on side effects, error paths that leak data.
- **Phase 2, integration:** places where components assume another component checked something, inconsistent validation between layers, missing integration tests across boundaries.
- **Phase 3, quality and targets:** logging, limits on cost and loops, narrow permissions, test gaps, things TARGETS.md asks for.

## 3. Record

For each finding add a `todo` row: honest Sev (Phase 0 findings are P0), gate or misuse IDs, Found by `audit`, today's date in Found, an Accept sentence for P0 and P1, and a Notes line with file and a one-line reproduction. Check for an existing row first. If one exists, add to its notes instead of duplicating.

## 4. Report

Summarise per phase: count of findings and the top three overall. Point out any finding type that showed up more than once. Those are candidates for `/steer-promote`. State what you did not cover, so the audit's limits are clear.
