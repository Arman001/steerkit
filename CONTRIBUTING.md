# Contributing

steerkit came out of a thread where engineers shared what actually worked for them. Contributions continue that: real cases, real checks, real fixes.

## What is most useful

- **Misuse cases** you have hit in a real product, for `template/steer/MISUSE.md`
- **Gate checks** for a specific stack (FastAPI, Django, Express, LangGraph, MCP servers), as samples in `template/steer/checks/`
- **Bug fixes** to the installer, the checker or the Stop hook
- **Skill improvements** where a skill led the agent the wrong way. Say what happened.
- **Reports from using it**: what got skipped, what was annoying, what caught something. Open an issue.

## What will usually be declined

- **Rules nobody can check.** A gate needs a named enforcement mechanism. Without one, it is a target at most. Every rule is one more thing the code has to satisfy, so the bar is high.
- **Required fields or steps for P2 and P3 items.** The overhead goes where the risk is.
- **Dependencies.** The checker uses the Python standard library only, 3.8+. The installer is plain bash.
- **Stack-specific code in the core.** Stack-specific checks go in as `.sample` files.

If you are unsure, open an issue first and ask.

## How to contribute

1. **Fork** the repo on GitHub and clone your fork.
2. **Create a branch** named after the change:
   ```bash
   git switch -c misuse-split-refunds
   ```
3. **Make the change.** Keep it to one thing per pull request.
4. **Run the tests:**
   ```bash
   ./tests/run.sh
   ```
   They install the kit into temp folders and check the installer, the checker and the Stop hook. Nothing outside a temp folder is touched. You need bash, git and python3.
5. **If you changed the checker or the installer, add a test** in `tests/run.sh`, and confirm it fails without your change. This kit's own rule applies to itself: a test that has never failed proves nothing.
6. **Push your branch** and open a pull request against `main`. Fill in the template.

CI runs the tests on Linux (Python 3.8 and 3.12) and macOS. A pull request is merged once CI passes and the maintainer has reviewed it.

## Style

- Plain, direct sentences. No marketing language.
- Rules say what to do and why, in one or two lines.
- Credit ideas. If a change came from someone's comment, post or experience, say so in the pull request, and add them to the credits in `README.md` if it is a substantial idea.

## Repo layout

```
template/          what gets installed into a project
  steer/           rules, spec, gates, tracker, checker
  .claude/         Claude Code skills and the Stop hook
install.sh         the installer
tests/run.sh       self-tests, run by CI
examples/ci/       CI workflow for projects that use steerkit
```
