# Checks

One executable per mechanical gate check. Name it after the gate: `G1-no-identity-params.sh`, `G2-scoped-lookups.py`.

## Contract

- Exit `0` when the gate holds. Exit non-zero when it is violated.
- Print what failed and where, so the agent can fix it without guessing.
- Run from the project root. Use only what the project already has installed.
- Files ending in `.md` or `.sample` are ignored by the runner.

Run all checks:

```
python3 steer/bin/steer_check.py checks
```

## Making a check count

1. Write the check.
2. Run it on the current code. It should pass (or fail on real problems you then fix).
3. **Inject the defect** the gate is about. For G1, add a `user_id` parameter to one tool. Run the check. It must fail.
4. Remove the injected defect.
5. In `steer/GATES.md`, set Check to the file name, write how you proved it in Proof, set Status to `active`, and add a changelog line.

`/steer-promote` walks through these steps.

## Mechanical vs review

Some rules cannot be checked by a script, for example "policies only load from a controlled source." Those use review enforcement: `/steer-attack` gives a written verdict per gate ID and a human approves it. Prefer mechanical whenever a script can do it, even a rough one. A rough check that runs every time beats a perfect review that gets skipped.
