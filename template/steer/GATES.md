# Gates

A gate is a rule that blocks a merge or a release. A violation is a defect, not a preference.

**The test for a gate is one question: is there a named enforcement mechanism?** If yes, it can be active. If no, it stays a candidate until someone writes the check, however important it sounds.

Two kinds of enforcement:

- **mechanical**: an executable in `steer/checks/` that exits non-zero on a violation. Runs locally and in CI.
- **review**: `/steer-attack` gives a written verdict per gate ID, and a human approves it. Use only when a script genuinely cannot check the rule.

**A check only counts once it has been proven.** Inject the defect it is meant to catch (for example, add a `customer_id` argument to a tool), run the check, and confirm it fails. Record how in the Proof column. A check that has never failed tells you nothing.

## Status values

- `candidate`: agreed rule, no proven check yet. Treated as a target.
- `active`: has a check and a proof. Blocks merge and release.
- `retired`: no longer applies. Keep the row, add the reason.

`steer/bin/steer_check.py lint` refuses an `active` gate with an empty Check or Proof, or a mechanical check file that does not exist.

## Gates

| ID | Rule | Status | Enforcement | Check | Proof | Source |
|---|---|---|---|---|---|---|
| G1 | No agent tool or endpoint accepts the acting user's identity as an argument. Identity is read from the session. | candidate | mechanical | | | OWASP API1 (BOLA). Anatoliy Kolodkin, Laurent Poupet, Roshan Tamil Sellvan |
| G2 | Every lookup by ID is filtered by the caller (`id AND owner`). A foreign ID returns nothing. Tested by calling the tool directly as user A with user B's ID, in CI, not through the chat. | candidate | mechanical | | | OWASP API1. Muhammad Ahsan, Laurent Poupet, Haggai Guggenheimer |
| G3 | Business limits (refund ceilings, quotas, roles) are enforced in tool code before the side effect, not only in the prompt. | candidate | review | | | OWASP LLM06. Laurent Poupet, Roshan Tamil Sellvan |
| G4 | User, document and tool-output content never changes policy. Decided by where content comes from, not by topic: anything typed into the chat is a request, and only documents and records the agent looks up from a controlled source count as a source. | candidate | review | | | OWASP LLM01. Vlad Gerov, Rehan Shakir |
| G5 | Every feature that touches data or side effects has misuse tests from `steer/MISUSE.md`, written before the implementation. | candidate | review | | | Ali Asghar, Faisal Feroz |
| G6 | Agent sessions cannot write to production resources. | candidate | mechanical | | | Allan S. |

## Changelog

Record every gate added, activated, retired or rejected, with the reason. Rejected gates stay here so the same idea is not proposed twice.

| Date | Change | Reason |
|---|---|---|
| | Initial candidates from steerkit | |
