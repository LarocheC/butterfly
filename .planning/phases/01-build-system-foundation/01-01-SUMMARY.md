---
phase: 01-build-system-foundation
plan: "01"
subsystem: infra
tags: [pyproject-toml, setuptools, cuda, pep621, build-system]

# Dependency graph
requires: []
provides:
  - "pyproject.toml with PEP 621 metadata and build-system declaration"
  - "Thin setup.py shim with CUDA arch fix and TORCH_CUDA_ARCH_LIST support"
  - "MANIFEST.in for sdist inclusion of csrc/ sources"
affects: [01-02, 02-01]

# Tech tracking
tech-stack:
  added: [setuptools>=77, ninja, wheel]
  patterns: [pyproject-toml-metadata, thin-setup-shim, torch-cuda-arch-list]

key-files:
  created: [pyproject.toml, MANIFEST.in]
  modified: [setup.py]

key-decisions:
  - "CUDA arch default 7.0 8.0 9.0+PTX covering Volta through Hopper with PTX forward compat"
  - "torch>=2.0 in build-system.requires for PEP 517 build isolation compatibility"
  - "Keep no_python_abi_suffix=True for now (Phase 2 will address with __init__.py rework)"
  - "Keep NVCC_FLAGS env var alongside TORCH_CUDA_ARCH_LIST for non-arch flags"

patterns-established:
  - "All package metadata in pyproject.toml, zero metadata in setup.py"
  - "TORCH_CUDA_ARCH_LIST env var for CUDA architecture override"

requirements-completed: [BUILD-01, BUILD-02, BUILD-03, BUILD-04, BUILD-05, BUILD-06, CUDA-01, CUDA-02, CUDA-03, CUDA-04, INST-04, INST-05, INST-06]

# Metrics
duration: 2min
completed: 2026-04-02
---

# Phase 1, Plan 1: pyproject.toml and Build Shim Summary

**PEP 621 pyproject.toml with torch build isolation, thin setup.py shim with CUDA 7.0/8.0/9.0+PTX arch targeting, and MANIFEST.in for sdist**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-02T12:34:41Z
- **Completed:** 2026-04-02T12:36:11Z
- **Tasks:** 4
- **Files modified:** 3 (1 created, 1 modified, 1 deleted)

## Accomplishments
- Created pyproject.toml with complete PEP 621 metadata, build-system declaration (setuptools + torch + ninja + wheel), runtime deps (torch>=2.0, numpy), and optional dep groups (dev, test)
- Reduced setup.py from 87-line metadata-heavy file to 63-line thin shim containing only get_extensions() and BuildExtension cmdclass
- Replaced hardcoded -arch=sm_35 (broken on CUDA 12+) with TORCH_CUDA_ARCH_LIST env var support defaulting to 7.0 8.0 9.0+PTX
- Created MANIFEST.in ensuring csrc/ C++/CUDA sources are included in sdist
- Deleted stale requirements.txt (python>=3.6, pytorch>=1.8, ray>=0.6.5)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pyproject.toml** - `5852d27` (feat)
2. **Task 2: Reduce setup.py to thin shim** - `65fe50b` (refactor)
3. **Task 3: Create MANIFEST.in** - `27fffe7` (feat)
4. **Task 4: Delete requirements.txt** - `b56c81e` (chore)

## Files Created/Modified
- `pyproject.toml` - New PEP 621 package metadata and build-system declaration
- `setup.py` - Reduced to thin shim with only ext_modules and BuildExtension
- `MANIFEST.in` - Ensures csrc/ sources included in source distributions
- `requirements.txt` - Deleted (replaced by pyproject.toml)

## Decisions Made
- **CUDA arch default:** 7.0 8.0 9.0+PTX -- covers Volta, Ampere, Hopper with PTX forward compat for Ada/Blackwell (per D-01, D-02 from CONTEXT.md)
- **TORCH_CUDA_ARCH_LIST:** Set as env var default rather than passing -gencode flags directly, allowing PyTorch's BuildExtension to handle flag generation (per D-03)
- **NVCC_FLAGS preserved:** Kept for non-arch flags (--expt-extended-lambda, -lineinfo). TORCH_CUDA_ARCH_LIST handles arch targeting separately.
- **Build isolation:** torch>=2.0 in build-system.requires so standard `pip install .` / `uv pip install .` works without flags (Strategy A from ARCHITECTURE.md)
- **no_python_abi_suffix=True:** Kept for now as removing it would break __init__.py's load_library() calls (Phase 2 scope)
- **Added -O3 to cxx args:** Standard optimization for release builds

## Deviations from Plan

None -- plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- pyproject.toml + setup.py shim + MANIFEST.in form complete PEP 517 build configuration
- Plan 01-02 can proceed with install testing (uv pip install ., FORCE_CUDA, FORCE_CPU)
- Phase 2 can proceed with __init__.py rework and editable install support

## Self-Check: PASSED

- All 4 created/modified files verified present
- requirements.txt confirmed deleted
- All 4 task commits verified in git log

---
*Phase: 01-build-system-foundation*
*Completed: 2026-04-02*
