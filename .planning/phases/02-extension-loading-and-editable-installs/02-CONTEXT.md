# Phase 2: Extension Loading and Editable Installs - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the runtime extension loading in `__init__.py` so that `import torch_butterfly` works for both regular installs (`uv pip install .`) and editable installs (`uv pip install -e .`). Modernize the deprecated `RegisterOperators` API in `csrc/version.cpp` to use `TORCH_LIBRARY`. Downgrade the CUDA version check from error to warning. Remove `no_python_abi_suffix=True` from setup.py.

This phase does NOT touch complex_utils.py, cupy references, or other module code beyond what's needed for the loading fix.

</domain>

<decisions>
## Implementation Decisions

### Extension Loading Mechanism
- **D-01:** Replace PathFinder-based .so discovery with `__file__`-relative path resolution (e.g., `os.path.join(os.path.dirname(__file__), '_butterfly*.so')` with glob)
- **D-02:** Use `torch.ops.load_library()` to load the found .so files (preserve current API)
- **D-03:** Must work for both regular installs (site-packages) and editable installs (source tree)

### ABI Suffix
- **D-04:** Remove `no_python_abi_suffix=True` from setup.py's `BuildExtension.with_options()`
- **D-05:** Use glob pattern to find .so files regardless of ABI tag (e.g., `_butterfly*.so` or `_butterfly.*.so`)

### CUDA Version Check
- **D-06:** Downgrade `check_cuda_version()` from `RuntimeError` to `warnings.warn()` when CUDA versions mismatch
- **D-07:** Keep the check itself — it's useful diagnostic info, just shouldn't be fatal

### C++ API Modernization
- **D-08:** Migrate `csrc/version.cpp` from `torch::RegisterOperators().op(...)` to `TORCH_LIBRARY` macro (consistent with `csrc/butterfly.cpp`)

### Scope
- **D-09:** Minimal cleanup only — fix loading, CUDA check, version.cpp. Don't touch complex_utils.py, cupy refs, or PyTorch 1.7 workarounds
- **D-10:** Phase 1 verification gaps (INST-01, INST-02 import failures) should be resolved by this phase

### Claude's Discretion
- Exact glob pattern for finding .so files with ABI tags
- Whether to add a graceful fallback if .so files aren't found (pure-Python mode warning vs hard error)
- Exact warning message text for CUDA version mismatch
- Whether to update `__version__` string

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current Code
- `torch_butterfly/__init__.py` — Current PathFinder loading mechanism to replace
- `csrc/version.cpp` — Deprecated RegisterOperators API to modernize
- `csrc/butterfly.cpp` — Modern TORCH_LIBRARY macro (reference for version.cpp migration)
- `setup.py` — Contains `no_python_abi_suffix=True` to remove

### Phase 1 Artifacts
- `.planning/phases/01-build-system-foundation/01-CONTEXT.md` — Phase 1 decisions (D-01 through D-12)
- `.planning/phases/01-build-system-foundation/01-VERIFICATION.md` — Phase 1 gaps (INST-01, INST-02 import failures)
- `.planning/phases/01-build-system-foundation/01-01-SUMMARY.md` — What was built in Phase 1

### Research
- `.planning/research/PITFALLS.md` — Pitfalls #3 (PathFinder), #5 (RegisterOperators), #6 (no_python_abi_suffix)
- `.planning/research/SUMMARY.md` — Phase 2 implications section

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `csrc/butterfly.cpp` TORCH_LIBRARY pattern — direct template for version.cpp migration
- `torch.ops.load_library()` — already used in __init__.py, just needs the path resolution fix

### Established Patterns
- Extensions are named `torch_butterfly._butterfly` and `torch_butterfly._version`
- They register ops in the `torch_butterfly` namespace via TORCH_LIBRARY
- `torch.ops.torch_butterfly.butterfly_multiply` etc. are the public C++ op interface

### Integration Points
- `__init__.py` loads extensions then imports from `.butterfly`, `.butterfly_base4`, `.multiply`
- `check_cuda_version()` calls `torch.ops.torch_butterfly.cuda_version()` — needs extensions loaded first
- After extensions load: `from .butterfly import Butterfly, ButterflyUnitary, ButterflyBmm`

</code_context>

<specifics>
## Specific Ideas

No specific requirements — follow the pytorch_scatter / pytorch/extension-cpp patterns identified in Phase 1 research.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-extension-loading-and-editable-installs*
*Context gathered: 2026-04-02*
