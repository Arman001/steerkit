# Targets

Standards to work toward. They set direction. Nothing claims compliance with them, and they do not block a merge.

When a target keeps showing up in audits as a real defect, and someone can name how to check it, promote it to a gate with `/steer-promote`.

| ID | Target | Why | Notes |
|---|---|---|---|
| T1 | Each tool has the narrowest permissions it needs (read-only where possible, scoped database user, scoped API keys). | Limits blast radius when something else fails. OWASP LLM06 | |
| T2 | Side-effect tools (payments, refunds, emails, deletes) ask the user to confirm before acting. | Prevents the agent acting on a misread instruction. OWASP LLM06 | |
| T3 | Model output is treated as untrusted before it reaches HTML, SQL, shell or another system. | OWASP LLM05 | |
| T4 | System prompts contain no secrets, keys or internal-only rules that would matter if leaked. | OWASP LLM07 | |
| T5 | Every tool call is logged with session user, tool, inputs and result, so incidents can be traced. | You cannot audit what you did not record | |
| T6 | Token, request and loop limits per session and per user. | OWASP LLM10, API4 | |
| T7 | Changes are kept small and inside one component where possible. | Problems collect where components share paths. Nabarun Mondal | |
| T8 | Tests cover the connections between components, not only the components. | Each part can be correct while the combination is not | |
