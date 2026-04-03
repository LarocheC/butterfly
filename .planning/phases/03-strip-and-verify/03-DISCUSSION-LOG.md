# Phase 3: Strip and Verify - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 03-strip-and-verify
**Areas discussed:** Gitignore cleanup, README.md updates, Commit strategy

---

## Gitignore Cleanup

| Option | Description | Selected |
|--------|-------------|----------|
| Clean up stale entries | Remove gitignore lines for deleted dirs, keep entries for build artifacts and Python standard patterns | ✓ |
| Leave as-is | Don't touch .gitignore beyond adding build artifact entries — stale lines are harmless | |
| Full rewrite | Rewrite .gitignore to only cover what remains in the repo — minimal and clean | |

**User's choice:** Clean up stale entries
**Notes:** None

---

## README.md Updates

| Option | Description | Selected |
|--------|-------------|----------|
| Modernize it | Rewrite to reflect current state: Python 3.10+, PyTorch 2.x, uv/pip install, torch_butterfly only, remove old interface and experiment sections | ✓ |
| Minimal trim | Just remove references to deleted directories. Keep the rest even if slightly outdated | |
| You decide | Claude picks the best approach given the CI/CD pipeline goal | |

**User's choice:** Modernize it
**Notes:** README currently references Python 3.6+, PyTorch 1.8+, conda install, old butterfly/ interface, and learning_transforms/ experiment code.

---

## Commit Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Separate commits | One commit per category: legacy removal, experiment removal, cleanup/gitignore, README update | |
| Single commit | One big commit removing everything at once | |
| You decide | Claude picks based on what makes sense | ✓ |

**User's choice:** You decide
**Notes:** None

---

## Claude's Discretion

- Commit strategy: Claude decides how to organize commits for the removals

## Deferred Ideas

None — discussion stayed within phase scope
