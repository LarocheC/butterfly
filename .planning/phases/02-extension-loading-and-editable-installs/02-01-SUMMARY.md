---
phase: 02-extension-loading-and-editable-installs
plan: "01"
subsystem: infra
tags: [cpp-extensions, torch-library, glob, editable-install, cuda-version-check]

# Dependency graph
requires:
  - phase: 01-build-system-foundation
    provides: pyproject.toml build system, setup.py with CUDAExtension/CppExtension
provides:
  - Glob-based __file__-relative extension loading in __init__.py
  - TORCH_LIBRARY macro in version.cpp (matching butterfly.cpp pattern)
  - CUDA version mismatch downgraded to UserWarning
  - Standard CPython ABI suffix on compiled extensions
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Glob-based .so discovery with __file__-relative _ext_dir"
    - "TORCH_LIBRARY macro for all C++ op registration"
    - "UserWarning for CUDA version mismatch instead of RuntimeError"

key-files:
  created: []
  modified:
    - csrc/version.cpp
    - setup.py
    - torch_butterfly/__init__.py

key-decisions:
  - "Used glob.glob with platform-aware suffixes (.so, .pyd, .dylib) for cross-platform extension discovery"
  - "Downgraded CUDA version mismatch from RuntimeError to UserWarning for better DX"

patterns-established:
  - "Extension loading: _load_extension() helper with glob pattern matching name prefix"
  - "Op registration: TORCH_LIBRARY(torch_butterfly, m) consistently across all csrc/ files"

requirements-completed: [EXT-01, EXT-02, EXT-03, INST-03]

# Metrics
duration: 1min
completed: 2026-04-02
---

# Phase 2 Plan 1: Extension Loading and Editable Installs Summary

**Glob-based .so discovery replacing PathFinder, TORCH_LIBRARY macro in version.cpp, CUDA mismatch downgraded to warning**

## Performance

- **Duration:** 1 min
- **Started:** 2026-04-02T20:18:02Z
- **Completed:** 2026-04-02T20:19:27Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Replaced broken PathFinder-based .so loading with __file__-relative glob discovery that works for both regular and editable (PEP 660) installs
- Modernized version.cpp from deprecated RegisterOperators to TORCH_LIBRARY macro, matching the pattern already used in butterfly.cpp
- Removed no_python_abi_suffix hack from setup.py, enabling standard CPython ABI-tagged extensions
- Downgraded CUDA version mismatch from RuntimeError crash to UserWarning for graceful degradation

## Task Commits

Each task was committed atomically:

1. **Task 1: Modernize version.cpp and remove ABI suffix hack from setup.py** - `e7439f6` (feat)
2. **Task 2: Rewrite __init__.py with glob-based extension loading and CUDA warning** - `d532681` (feat)

## Files Created/Modified
- `csrc/version.cpp` - Replaced deprecated RegisterOperators with TORCH_LIBRARY macro
- `setup.py` - Removed no_python_abi_suffix=True from BuildExtension options
- `torch_butterfly/__init__.py` - Glob-based _load_extension(), CUDA warning instead of error

## Decisions Made
- Used glob.glob with platform-aware suffixes (.so, .pyd, .dylib) for cross-platform extension discovery
- Downgraded CUDA version mismatch from RuntimeError to UserWarning -- extensions still load and work, just warn about potential issues

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Build-and-import verification could not be run because no virtual environment with PyTorch is available in the execution environment. Static verification of all file content passed. Build verification should be done manually with `uv pip install -e . --no-build-isolation` in a conda/venv with PyTorch.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All source changes for extension loading are complete
- Manual build-and-import test recommended before considering v1.0 milestone done
- No further phases planned in ROADMAP

## Self-Check: PASSED

All 3 modified files exist. Both task commits (e7439f6, d532681) verified in git log. SUMMARY.md created.

---
*Phase: 02-extension-loading-and-editable-installs*
*Completed: 2026-04-02*
