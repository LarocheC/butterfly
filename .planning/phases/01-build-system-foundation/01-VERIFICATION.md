---
phase: 01-build-system-foundation
verified: 2026-04-02T22:00:00Z
status: gaps_found
score: 13/16 must-haves verified
re_verification: false
gaps:
  - truth: "uv pip install . succeeds in a clean virtual environment AND import torch_butterfly works"
    status: partial
    reason: "uv pip install . exits 0 and compiles .so extensions correctly. However, import torch_butterfly fails in the test venv because the FORCE_CPU=1 build produces a CPU-only extension while the torch pulled in by build-system.requires has CUDA 13.0, triggering the existing check_cuda_version() guard in __init__.py. INST-01 is marked Pending in REQUIREMENTS.md. Full import success is blocked pending Phase 2 (EXT-01)."
    artifacts:
      - path: "torch_butterfly/__init__.py"
        issue: "PathFinder-based .so loading works after install, but check_cuda_version() raises RuntimeError when CPU-built extension is loaded alongside a CUDA-enabled torch (cuda_version() returns -1 vs torch.version.cuda='13.0'). This is pre-existing code, not changed by Phase 1."
    missing:
      - "End-to-end import torch_butterfly succeeding after install (blocked by EXT-01 in Phase 2)"
      - "Test confirming CUDA build + import works when CUDA toolkit is available (INST-01 full scope)"
  - truth: "pip install . succeeds in a clean virtual environment AND import torch_butterfly works"
    status: partial
    reason: "pip install . exits 0 and package metadata is correct. Same import blocker as INST-01: CPU-built extension mismatches CUDA-enabled torch at import time. INST-02 is marked Pending in REQUIREMENTS.md."
    artifacts:
      - path: "torch_butterfly/__init__.py"
        issue: "Same check_cuda_version() issue as INST-01."
    missing:
      - "End-to-end import torch_butterfly succeeding after pip install (blocked by EXT-01 in Phase 2)"
human_verification:
  - test: "Install with CUDA available and verify import works"
    expected: "FORCE_CUDA=1 uv pip install . --no-build-isolation (in a venv with torch + CUDA toolkit) followed by import torch_butterfly succeeds with no RuntimeError"
    why_human: "No CUDA toolkit is available on the verification machine; cannot compile CUDA extension or test CUDA import path programmatically"
  - test: "pip show torch-butterfly displays correct metadata"
    expected: "Name: torch-butterfly, Version: 0.1.0, Requires-Python: >=3.10, Requires: torch>=2.0, numpy"
    why_human: "Needs user to run in their own environment to confirm the display is correct after a fresh install"
---

# Phase 01: Build System Foundation Verification Report

**Phase Goal:** Users can install torch_butterfly from source with `uv pip install .` or `pip install .` and get a working package with CUDA support
**Verified:** 2026-04-02T22:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | pyproject.toml exists with PEP 621 metadata and build-system declaration | VERIFIED | File exists, TOML parses cleanly, all required fields present |
| 2  | setup.py contains only get_extensions() and setup(ext_modules, cmdclass) | VERIFIED | ast.parse confirms setup() kwargs = ['ext_modules', 'cmdclass'] only |
| 3  | No package metadata remains in setup.py | VERIFIED | grep for name=, version=, author=, install_requires, python_requires, packages= all return 0 matches |
| 4  | Hardcoded -arch=sm_35 is completely removed | VERIFIED | grep sm_35 setup.py returns 0 matches |
| 5  | CUDA auto-detection from torch.cuda.is_available() and CUDA_HOME is preserved | VERIFIED | setup.py line 17: `WITH_CUDA = torch.cuda.is_available() and CUDA_HOME is not None` |
| 6  | FORCE_CUDA and FORCE_CPU env vars still work | VERIFIED | setup.py lines 18-21 handle both env vars |
| 7  | TORCH_CUDA_ARCH_LIST env var is supported | VERIFIED | setup.py lines 36-37: sets default if not present, respects existing value |
| 8  | No -arch flags are passed to nvcc | VERIFIED | nvcc_flags contains only --expt-extended-lambda and -lineinfo |
| 9  | MANIFEST.in includes csrc/ sources | VERIFIED | MANIFEST.in line 1: `recursive-include csrc *.cpp *.cu *.h *.cuh` |
| 10 | requirements.txt is deleted | VERIFIED | File does not exist in repo |
| 11 | Package discovery includes torch_butterfly* and excludes butterfly/ | VERIFIED | pyproject.toml: `[tool.setuptools.packages.find] include = ["torch_butterfly*"]` |
| 12 | Optional dependency groups dev and test are defined | VERIFIED | pyproject.toml has `[project.optional-dependencies]` with dev and test groups |
| 13 | Install works without conda | VERIFIED | uv pip install . --no-build-isolation FORCE_CPU=1 exits 0 with no conda commands |
| 14 | uv pip install . succeeds AND import torch_butterfly works | PARTIAL | Install exits 0, .so files compiled. Import fails: check_cuda_version() raises RuntimeError (CPU build vs CUDA torch mismatch). INST-01 marked Pending in REQUIREMENTS.md. |
| 15 | pip install . succeeds AND import torch_butterfly works | PARTIAL | Install exits 0, wheel built. Same import blocker as #14. INST-02 marked Pending in REQUIREMENTS.md. |
| 16 | Python >=3.10 and torch>=2.0 enforced in metadata | VERIFIED | requires-python = ">=3.10", dependencies = ["torch>=2.0", "numpy"] |

**Score:** 13/16 truths verified (2 partial, 1 human-only)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `pyproject.toml` | PEP 621 metadata + build-system | VERIFIED | 34 lines, all required sections present, TOML valid |
| `setup.py` | Thin shim, extension-only | VERIFIED | 71 lines, only get_extensions() + setup(ext_modules, cmdclass) |
| `MANIFEST.in` | sdist csrc/ inclusion | VERIFIED | 3 lines, includes *.cpp *.cu *.h *.cuh recursively plus LICENSE and README.md |
| `requirements.txt` | Must not exist | VERIFIED | Deleted |
| `csrc/*.cpp` | Source files discoverable by get_extensions() | VERIFIED | csrc/butterfly.cpp, csrc/version.cpp present; cpu/ and cuda/ subdirs with matching files |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `pyproject.toml` build-system | `setup.py` | `build-backend = "setuptools.build_meta"` invoking setup() | WIRED | pyproject.toml declares setuptools.build_meta; setup.py calls setup(ext_modules, cmdclass) |
| `setup.py` get_extensions() | `csrc/*.cpp` | `Path("csrc").glob("*.cpp")` | WIRED | Line 43: `for main in extensions_dir.glob("*.cpp")` finds butterfly.cpp and version.cpp |
| `setup.py` get_extensions() | `torch.utils.cpp_extension` | `from torch.utils.cpp_extension import BuildExtension, CppExtension, CUDAExtension, CUDA_HOME` | WIRED | Line 13 imports all required symbols; BuildExtension.with_options used in setup() cmdclass |

### Data-Flow Trace (Level 4)

Not applicable — this phase produces build configuration files, not components that render dynamic data.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| pyproject.toml is valid TOML | `python3 -c "import tomllib; tomllib.load(...)"` | Parsed successfully | PASS |
| setup.py is valid Python | `python3 -c "import ast; ast.parse(...)"` | Parsed successfully | PASS |
| setup() has only ext_modules + cmdclass kwargs | AST inspection of setup() call | kwargs = ['ext_modules', 'cmdclass'] | PASS |
| uv pip install . exits 0 (FORCE_CPU=1, --no-build-isolation) | `uv pip install . --no-build-isolation` | exit 0, package installed | PASS |
| Package metadata correct after install | `importlib.metadata.distribution('torch-butterfly')` | Name=torch-butterfly, Version=0.1.0, Requires-Python=>=3.10 | PASS |
| .so extensions compiled | `find site-packages/torch_butterfly -name "*.so"` | `_butterfly.so`, `_version.so` present | PASS |
| import torch_butterfly works (installed, no CUDA mismatch) | Python import in test venv | RuntimeError: CUDA version mismatch (CPU build vs CUDA torch) | FAIL |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| BUILD-01 | 01-01 | pyproject.toml with [build-system] declaring torch, setuptools, ninja, wheel | SATISFIED | pyproject.toml build-system.requires = ["setuptools>=64", "torch>=2.0", "ninja", "wheel"] |
| BUILD-02 | 01-01 | PEP 621 [project] table with name, version, description, python-requires, etc. | SATISFIED | All PEP 621 fields present: name, version, description, readme, license, requires-python, authors, keywords |
| BUILD-03 | 01-01 | Package discovery excludes legacy butterfly/ directory | SATISFIED | [tool.setuptools.packages.find] include = ["torch_butterfly*"] — legacy butterfly/ is excluded |
| BUILD-04 | 01-01 | MANIFEST.in includes csrc/ source files | SATISFIED | `recursive-include csrc *.cpp *.cu *.h *.cuh` in MANIFEST.in |
| BUILD-05 | 01-01 | Optional dependency groups for dev and test | SATISFIED | [project.optional-dependencies] has dev (pytest, flake8) and test (pytest) groups |
| BUILD-06 | 01-01, 01-02 | setup.py reduced to thin shim | SATISFIED | setup() kwargs = ['ext_modules', 'cmdclass'] only; no metadata |
| CUDA-01 | 01-01, 01-02 | Hardcoded sm_35 removed | SATISFIED | grep sm_35 setup.py returns 0 matches |
| CUDA-02 | 01-01, 01-02 | CUDA auto-detection from torch + CUDA_HOME | SATISFIED | Line 17: `WITH_CUDA = torch.cuda.is_available() and CUDA_HOME is not None` |
| CUDA-03 | 01-01, 01-02 | TORCH_CUDA_ARCH_LIST env var supported | SATISFIED | Lines 36-37: defaults to "7.0 8.0 9.0+PTX" if not set; respects override |
| CUDA-04 | 01-01, 01-02 | FORCE_CUDA and FORCE_CPU preserved | SATISFIED | Lines 18-21 handle both env vars |
| INST-01 | 01-03 | uv pip install . works from source checkout | BLOCKED | Install exits 0, .so compiled. `import torch_butterfly` fails — CPU-built extension raises CUDA version mismatch against CUDA-enabled torch. Marked Pending in REQUIREMENTS.md. |
| INST-02 | 01-03 | pip install . works from source checkout | BLOCKED | Same as INST-01. Marked Pending in REQUIREMENTS.md. |
| INST-04 | 01-01, 01-03 | Install works without conda | SATISFIED | uv pip install . and pip install . tested without conda |
| INST-05 | 01-01 | Python >=3.10, <4 enforced in metadata | SATISFIED | requires-python = ">=3.10" in pyproject.toml |
| INST-06 | 01-01 | PyTorch >=2.0 declared as runtime dependency | SATISFIED | dependencies = ["torch>=2.0", "numpy"] |

**Orphaned requirements check:** REQUIREMENTS.md maps INST-01 and INST-02 to Phase 1 with status Pending — these are claimed by plan 01-03 but not fully satisfied. No requirements assigned to Phase 1 are missing from plan coverage.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| setup.py | 68 | `no_python_abi_suffix=True` | Info | Intentional workaround for Phase 1; Phase 2 (EXT-01) will address. Documented in SUMMARY decisions. |

No TODO/FIXME/PLACEHOLDER/empty return patterns found in any Phase 1 modified files (pyproject.toml, setup.py, MANIFEST.in).

### Human Verification Required

#### 1. CUDA Build + Import Test

**Test:** On a machine with CUDA toolkit and a matching CUDA-enabled torch, run:
```bash
uv venv /tmp/test-bfly-cuda
VIRTUAL_ENV=/tmp/test-bfly-cuda uv pip install torch --index-url https://download.pytorch.org/whl/cu121
FORCE_CUDA=1 VIRTUAL_ENV=/tmp/test-bfly-cuda uv pip install . --no-build-isolation
/tmp/test-bfly-cuda/bin/python -c "import torch_butterfly; print('OK:', torch_butterfly.__file__)"
```
**Expected:** Import succeeds with no RuntimeError; `Butterfly`, `ButterflyUnitary`, `butterfly_multiply` are accessible.
**Why human:** No CUDA toolkit available on the verification machine; cannot compile CUDA extensions programmatically in this environment.

#### 2. pip show metadata verification

**Test:** After `pip install .`, run `pip show torch-butterfly`
**Expected:** Shows `Name: torch-butterfly`, `Version: 0.1.0`, `Requires: torch>=2.0, numpy`, `Location:` pointing to site-packages
**Why human:** No isolated pip environment with torch available on the verification machine at this time.

### Gaps Summary

Two requirements — INST-01 and INST-02 — are only partially satisfied by Phase 1.

The install commands (`uv pip install .` and `pip install .`) both exit 0 and produce a correctly packaged wheel with compiled .so extensions (`_butterfly.so`, `_version.so`). Package metadata is correct. This satisfies the "install pipeline works" aspect of both requirements.

The gap is that `import torch_butterfly` fails after install when the extension is built CPU-only (FORCE_CPU=1) but the available torch has CUDA support. The failure is in the pre-existing `check_cuda_version()` guard in `torch_butterfly/__init__.py` (not modified in Phase 1): it calls `torch.ops.torch_butterfly.cuda_version()` which returns -1 for a CPU build, then compares against `torch.version.cuda = "13.0"`, triggering a RuntimeError.

This is correctly identified in plan 01-03's SUMMARY as a known issue scoped to Phase 2 (EXT-01: "PathFinder-based extension loading in __init__.py replaced with __file__-relative .so discovery"). REQUIREMENTS.md explicitly marks INST-01 and INST-02 as Pending.

**Root cause of gap:** The phase goal includes "get a working package with CUDA support" — this requires either (a) a CUDA toolkit present for compilation or (b) the __init__.py extension loading to be fixed. Both are Phase 2 work. Phase 1 successfully delivers the build configuration foundation but cannot close the full install-and-import loop without Phase 2.

**All 13 build system, CUDA arch, and install metadata requirements (BUILD-01 through BUILD-06, CUDA-01 through CUDA-04, INST-04, INST-05, INST-06) are fully verified.**

---

_Verified: 2026-04-02T22:00:00Z_
_Verifier: Claude (gsd-verifier)_
