# Tracker

The single source of truth for what has been built, what was found, and what is proven. Every session starts by reading this file.

## Legend

**Status:** `todo`, `wip`, `done`, `verified`, `deferred`, `accepted-risk`, `wontfix`

**Sev:** `P0` blocks release, `P1` before release, `P2` soon, `P3` nice to have

**Found by:** how the item entered the tracker. `spec` is planned work. Everything else is a finding.

| Value | Meaning |
|---|---|
| `spec` | Planned work seeded from SPEC.md |
| `agent` | The agent noticed it while working on something else |
| `test` | A unit, integration or misuse test failed |
| `gate` | A gate check failed |
| `attack` | `/steer-attack` found it |
| `audit` | `/steer-audit` found it |
| `live` | Found while running the live test in `/steer-verify` |
| `human` | The human noticed it while using or reviewing the product |
| `user` | Reported by a real user after release |

`live`, `human` and `user` mean the problem got past every automated layer. `steer_check.py stats` counts these separately.

**Columns**

- **Gate:** gate IDs (G1, G2) and misuse IDs (M1, M3) this item relates to
- **Found:** the date it entered the tracker, YYYY-MM-DD
- **Accept:** one sentence saying what must be true for it to count as fixed. Required for P0 and P1 before work starts. Re-read it before building and before closing, so a fix cannot satisfy the wrong problem.
- **Test:** the test that proves it, plus `red: <date or commit>` for when that test was seen failing before the fix. If no automated test is possible, `manual: <how it was checked before and after>`. Required for P0 and P1 at `done`.
- **Commit:** short hash of the fix
- **Release:** the release this shipped in. Leave blank until it ships
- **Verified:** date and how, e.g. `2026-10-26 live`, `2026-10-26 human`

**Required by status**

- `done`: Commit. P0/P1 also need Accept and Test
- `verified`: Commit and Verified
- `deferred`, `wontfix`: `reason:` in Notes. Not allowed for P0
- `accepted-risk`: `owner:`, `reason:` and `review:` (YYYY-MM-DD) in Notes

Rules are enforced by `python3 steer/bin/steer_check.py lint`. `python3 steer/bin/steer_check.py release` fails while any P0 is not verified or accepted. `python3 steer/bin/steer_check.py stats` reports what was found, by what, and how fast it was closed.

## Items

| ID | Item | Sev | Gate | Found by | Found | Status | Accept | Test | Commit | Release | Verified | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|

<!--
Example rows (copy the format, do not uncomment):
| 1 | Order lookup scoped to session user | P0 | G1 G2 M1 | spec | 2026-10-20 | verified | As user A, get_order on B's order returns nothing, same as a missing ID | test_orders::test_foreign_order red: 2026-10-21 | 9f8848e | v0.1.0 | 2026-10-26 live | |
| 2 | Refund tool accepts amount above order total | P0 | G3 M5 | attack | 2026-10-24 | done | Refund above order total or ceiling is refused in tool code, prompt cannot change it | test_refunds::test_over_total red: a1b2c3d | b4c5d6e | | | repro: ask for refund of 9999 on a 20 order |
| 3 | Rate limit per user | P2 | M11 | audit | 2026-10-24 | deferred | | | | | | reason: not needed before beta |
| 4 | Prompt reveals tool names | P3 | M8 | human | 2026-10-25 | accepted-risk | | | | | | owner: saad reason: names are not sensitive review: 2027-01-15 |
-->
