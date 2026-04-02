# Phase 2: Extension Loading and Editable Installs - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 02-extension-loading-and-editable-installs
**Areas discussed:** Extension loading, ABI suffix, CUDA version check, Scope boundary

---

## Extension Loading

| Option | Description | Selected |
|--------|-------------|----------|
| __file__-relative | Use os.path to find .so relative to __init__.py. Simple, works for both install modes. | ✓ |
| importlib.resources | Modern Python API. More correct but heavier, may not handle .so in editable mode. | |
| You decide | Claude's discretion | |

**User's choice:** __file__-relative (Recommended)

---

## ABI Suffix

| Option | Description | Selected |
|--------|-------------|----------|
| Remove it | Standard ABI-tagged filenames, glob to find .so. More standard. | ✓ |
| Keep it | Continue untagged .so files. Simpler but non-standard. | |
| You decide | Claude's discretion | |

**User's choice:** Remove it (Recommended)

---

## CUDA Version Check

| Option | Description | Selected |
|--------|-------------|----------|
| Downgrade to warning | Log warning instead of RuntimeError. Users can still use the library. | ✓ |
| Remove entirely | Drop the check. Modern PyTorch handles compat itself. | |
| Keep as error | Maintain RuntimeError on mismatch. | |
| You decide | Claude's discretion | |

**User's choice:** Downgrade to warning (Recommended)

---

## Scope Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal | Only fix loading, CUDA check, version.cpp. Don't touch other code. | ✓ |
| Light cleanup | Also remove PyTorch 1.7 workarounds in complex_utils.py. | |
| You decide | Claude's discretion | |

**User's choice:** Minimal (Recommended)

---

## Claude's Discretion

- Exact glob pattern for .so discovery
- Graceful fallback behavior if .so not found
- Warning message text
- __version__ string update

## Deferred Ideas

None — discussion stayed within phase scope
