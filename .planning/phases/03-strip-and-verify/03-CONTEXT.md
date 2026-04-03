# Phase 3: Strip and Verify - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Remove all non-core directories and files from the repository, leaving only the `torch_butterfly` library (`torch_butterfly/`, `csrc/`, `tests/`), build files (`pyproject.toml`, `setup.py`, `MANIFEST.in`), and repo essentials (`README.md`, `LICENSE`, `.gitignore`). Verify tests still pass after cleanup.

</domain>

<decisions>
## Implementation Decisions

### Gitignore Cleanup
- **D-01:** Remove stale `.gitignore` entries that reference deleted directories (`learning_transforms/logs/`, `learning_transforms/results/`, `cnn/logs/`, `cnn/results/`, `config/`, `data/`). Keep all standard Python patterns and build artifact entries.

### README Modernization
- **D-02:** Rewrite README.md to reflect current state: Python 3.10+, PyTorch 2.x, `uv pip install .` / `pip install .` as install method. Remove all references to old `butterfly/` interface, `learning_transforms/`, conda install, and experiment code. Keep the academic paper references and core usage documentation for `torch_butterfly`.

### Submodule Removal
- **D-03:** Fully remove the `fairseq` git submodule: `git rm fairseq`, delete `.gitmodules`, clean up `.git/modules/fairseq` if needed.

### Claude's Discretion
- **Commit strategy:** Claude decides how to organize commits. Separate commits per logical group (legacy removal, experiment removal, cleanup, README) recommended for clean git history, but one combined commit is acceptable if the diff is simple enough.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Build Configuration
- `pyproject.toml` — Current build system config, package metadata, Python/PyTorch version constraints
- `setup.py` — Thin build shim for C++/CUDA extensions
- `MANIFEST.in` — Source distribution manifest (ensure it doesn't reference removed dirs)

### Git Configuration
- `.gitmodules` — Fairseq submodule definition (to be removed)
- `.gitignore` — Current ignore patterns (to be cleaned up)

### Documentation
- `README.md` — Current README (to be modernized)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.gitignore` already has comprehensive Python patterns from gitignore.io — just needs stale project-specific entries removed
- `build/` and `*.egg-info/` patterns already present in `.gitignore` — `torch_butterfly.egg-info/` is tracked despite this

### Established Patterns
- BUILD-03 in `pyproject.toml` already excludes `butterfly/` from package discovery — no build config changes needed for legacy removal
- `MANIFEST.in` only includes `csrc/` — no references to experiment dirs

### Integration Points
- No code in `torch_butterfly/` or `tests/` imports from directories being removed
- `tests/` only imports from `torch_butterfly` — safe from removal side effects

</code_context>

<specifics>
## Specific Ideas

- User plans to move this repo to their company's CI/CD pipeline for package publishing — the cleanup is preparation for that
- Academic paper references should be preserved in the modernized README

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-strip-and-verify*
*Context gathered: 2026-04-03*
