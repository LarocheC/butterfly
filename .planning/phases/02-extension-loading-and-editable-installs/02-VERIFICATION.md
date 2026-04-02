---
phase: 02-extension-loading-and-editable-installs
verified: 2026-04-02T20:29:19Z
status: passed
score: 5/5 must-haves verified
---

# Phase 2: Extension Loading and Editable Installs — Verification Report

**Phase Goal:** Editable installs work reliably and the C++ extension loading mechanism is robust across install modes
**Verified:** 2026-04-02T20:29:19Z
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                 | Status     | Evidence                                                                  |
| --- | --------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------- |
| 1   | `import torch_butterfly` succeeds after `uv pip install -e .`        | ✓ VERIFIED | Orchestrator confirmed editable install + forward pass OK                 |
| 2   | `import torch_butterfly` succeeds after `uv pip install .`           | ✓ VERIFIED | Orchestrator confirmed non-editable install + forward pass OK             |
| 3   | CUDA version mismatch produces a warning, not a crash                | ✓ VERIFIED | `__init__.py` line 51: `warnings.warn(...)` — no `RuntimeError` present  |
| 4   | `torch.ops.torch_butterfly.cuda_version()` is callable after import  | ✓ VERIFIED | `version.cpp` registers op; `__init__.py` calls it in `check_cuda_version()` |
| 5   | `torch.ops.torch_butterfly.butterfly_multiply_fw` callable after import | ✓ VERIFIED | `butterfly.cpp` line 127 registers it; `_butterfly` loaded by `_load_extension` |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact                         | Expected                                       | Status     | Details                                                              |
| -------------------------------- | ---------------------------------------------- | ---------- | -------------------------------------------------------------------- |
| `csrc/version.cpp`               | TORCH_LIBRARY-based cuda_version registration  | ✓ VERIFIED | Uses `TORCH_LIBRARY_FRAGMENT(torch_butterfly, m)` at line 22; `RegisterOperators` absent (0 matches) |
| `setup.py`                       | BuildExtension without `no_python_abi_suffix`  | ✓ VERIFIED | `BuildExtension.with_options(use_ninja=True)` at lines 67-69; `no_python_abi_suffix` absent (0 matches) |
| `torch_butterfly/__init__.py`    | Glob-based extension loading and CUDA warning  | ✓ VERIFIED | `_load_extension()` defined at line 13, called at lines 34-35; `glob.glob` at line 22; `warnings.warn` at line 51 |

**Note on version.cpp:** The plan's `must_haves.artifacts` specifies `contains: "TORCH_LIBRARY(torch_butterfly"` but the actual implementation uses `TORCH_LIBRARY_FRAGMENT(torch_butterfly, m)`. This is a documented intentional deviation — `TORCH_LIBRARY_FRAGMENT` is the correct macro when two separate `.so` files (version and butterfly) both register into the same `torch_butterfly` namespace, avoiding a namespace collision. The orchestrator context confirms this was deliberate. The goal — modern TORCH_LIBRARY-based op registration, not the deprecated `RegisterOperators` — is fully achieved.

### Key Link Verification

| From                          | To                                     | Via                                         | Status     | Details                                                                                              |
| ----------------------------- | -------------------------------------- | ------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------- |
| `torch_butterfly/__init__.py` | `_version*.so` and `_butterfly*.so`    | `glob.glob` + `torch.ops.load_library`      | ✓ WIRED    | `_load_extension()` uses `glob.glob(pattern)` where pattern is `os.path.join(_ext_dir, f'{name}*.so')` etc.; `torch.ops.load_library(matches[0])` at line 24 |
| `torch_butterfly/__init__.py` | `torch.ops.torch_butterfly.cuda_version` | `check_cuda_version()` called at line 62    | ✓ WIRED    | `check_cuda_version()` calls `torch.ops.torch_butterfly.cuda_version()` at line 40; `warnings.warn` at line 51 when mismatch |
| `csrc/version.cpp`            | `torch_butterfly` namespace            | `TORCH_LIBRARY_FRAGMENT` macro              | ✓ WIRED    | `TORCH_LIBRARY_FRAGMENT(torch_butterfly, m)` at line 22 registers `cuda_version` into namespace     |

### Data-Flow Trace (Level 4)

Not applicable — this phase produces no UI components or data-rendering artifacts. All artifacts are infrastructure (C++ extension loading, build configuration).

### Behavioral Spot-Checks

| Behavior                                 | Command / Evidence                                                         | Status   |
| ---------------------------------------- | -------------------------------------------------------------------------- | -------- |
| Non-editable install + forward pass      | Orchestrator: `uv pip install .` — import OK, `Butterfly(8,8)` forward OK  | ✓ PASS   |
| Editable install + forward pass          | Orchestrator: `uv pip install -e .` — import OK, FFT special transforms OK | ✓ PASS   |
| CUDA version check is a warning not crash | `grep -c "RuntimeError" torch_butterfly/__init__.py` = 0                  | ✓ PASS   |
| glob-based loading pattern present       | `glob.glob`, `_load_extension`, `_ext_dir`, `warnings.warn` all present   | ✓ PASS   |
| No deprecated RegisterOperators         | `grep -c "RegisterOperators" csrc/version.cpp` = 0                        | ✓ PASS   |

### Requirements Coverage

| Requirement | Source Plan | Description                                                                                   | Status       | Evidence                                                                          |
| ----------- | ----------- | --------------------------------------------------------------------------------------------- | ------------ | --------------------------------------------------------------------------------- |
| EXT-01      | 02-01-PLAN  | PathFinder-based extension loading replaced with `__file__`-relative .so discovery           | ✓ SATISFIED  | `__init__.py`: `PathFinder` absent, `glob.glob` + `_ext_dir` present at lines 10, 22 |
| EXT-02      | 02-01-PLAN  | Editable installs (`uv pip install -e .`) load extensions correctly                           | ✓ SATISFIED  | Orchestrator confirmed editable install works; glob-based `_ext_dir` discovery works in source tree |
| EXT-03      | 02-01-PLAN  | Deprecated RegisterOperators in `csrc/version.cpp` migrated to TORCH_LIBRARY macro           | ✓ SATISFIED  | `version.cpp` uses `TORCH_LIBRARY_FRAGMENT(torch_butterfly, m)`; `RegisterOperators` absent |
| INST-03     | 02-01-PLAN  | `uv pip install -e .` works for development (editable)                                       | ✓ SATISFIED  | Orchestrator confirmed forward pass and FFT special transforms work under editable install |

All four requirements claimed in the PLAN frontmatter are satisfied. No orphaned requirements found for Phase 2 in REQUIREMENTS.md (INST-01 and INST-02 are Phase 2 in the tracker table but are marked unchecked — these were not claimed by any plan and are not in the PLAN's `requirements` field; they represent non-editable `pip install` which is separate from this phase's scope).

### Anti-Patterns Found

| File                              | Line | Pattern                                               | Severity | Impact                      |
| --------------------------------- | ---- | ----------------------------------------------------- | -------- | --------------------------- |
| `torch_butterfly/__init__.py`     | 26   | `raise ImportError` when no .so found                 | INFO     | Correct error — not a stub. Informs user to reinstall. |
| `torch_butterfly/permutation.py`  | 288  | `import scipy.linalg` inside function body (lazy)     | INFO     | Intentional lazy import per orchestrator context — avoids hard scipy dependency at module load time. |

No blockers or warnings. The `ImportError` in `_load_extension` is correct behavior, not a stub. The lazy scipy import is an explicit improvement noted by the orchestrator.

### Human Verification Required

#### 1. CUDA Mismatch Warning Path

**Test:** Build extensions against one CUDA version, then import with a PyTorch compiled for a different CUDA version.
**Expected:** `warnings.warn` fires with a `UserWarning` describing the mismatch — no exception raised, import succeeds.
**Why human:** Requires two different CUDA toolchains; cannot verify programmatically from source alone.

#### 2. Windows .pyd Loading Path

**Test:** On Windows, run `uv pip install -e .` and `import torch_butterfly`.
**Expected:** `_load_extension` finds `_version*.pyd` and `_butterfly*.pyd` via the `*.pyd` glob suffix.
**Why human:** Linux-only development environment; `.pyd` suffix path never exercised in CI.

---

## Gaps Summary

No gaps. All five observable truths are verified, all three artifacts pass all applicable levels (exists, substantive, wired), all four key links are confirmed wired, and all four requirement IDs are satisfied. The one noteworthy divergence from the PLAN (`TORCH_LIBRARY_FRAGMENT` vs `TORCH_LIBRARY`) is intentional and correct — it prevents namespace collision when two `.so` files both register into the same operator namespace, and is confirmed working by the orchestrator's end-to-end install tests.

---

_Verified: 2026-04-02T20:29:19Z_
_Verifier: Claude (gsd-verifier)_
