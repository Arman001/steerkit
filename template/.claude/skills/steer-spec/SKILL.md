---
name: steer-spec
description: Draft or extend steer/SPEC.md for a product or a new feature, including actors, data ownership, access matrix, agent tools, policy sources and misuse cases, then seed tracker items. Use before building anything new.
argument-hint: "[product idea or feature to spec]"
---

You are writing the spec that makes the unasked questions explicit. Input: $ARGUMENTS

## Steps

1. Read `steer/STEER.md`, `steer/SPEC.md`, `steer/MISUSE.md`, and `steer/GATES.md`. Run `python3 steer/bin/steer_check.py summary` and read only the tracker rows for features you are extending, plus the highest existing ID so new rows get the next free one. If SPEC.md already has content, extend it. Never overwrite approved sections.

2. If the input is thin, ask the human up to five short questions that change the design: who the users are, what data is private, what the agent can do on its own, what side effects exist, and whether there are multiple tenants or roles. Do not ask about things you can sensibly default; state the default instead.

3. Fill or extend SPEC.md sections 1 to 7. For every feature:
   - Ask "who should be allowed to see or change this?" for each object it touches, and update the access matrix.
   - List every agent tool it needs. For each: what the model supplies, where identity comes from (always the session), side effects, limits enforced in code, and whether the user must confirm.
   - Go through every case in `steer/MISUSE.md` and write how it applies, with the expected safe behaviour. Write "n/a" with a reason when it does not apply. Add feature-specific cases.
   - List the gates that apply.

4. Flag design choices that would break a gate, for example a tool that needs a `user_id` argument, or a policy that only exists in the prompt. Propose the alternative.

5. Seed `steer/TRACKER.md` with `todo` rows: one per feature slice, plus one per misuse-test group for features that touch data or side effects. Use the next free IDs. Set Sev honestly: anything that would leak data or move money is P0. Put misuse IDs and gate IDs in the Gate column. Found by is `spec`, Found is today's date. For P0 and P1, write Accept from the spec's access rules and misuse cases, e.g. "As user A, get_order on B's order returns nothing, same as a missing ID".

6. Stop and show the human:
   - the access matrix and agent tools table
   - any gate conflicts you flagged
   - the tracker rows you added

   Ask them to approve or correct the access rules. Access rules are the human's decision, not yours.
