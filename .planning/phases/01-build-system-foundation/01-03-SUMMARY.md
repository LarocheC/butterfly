---
phase: 01-build-system-foundation
plan: "03"
subsystem: infra
tags: [verification, install-test, uv, pip]

# Dependency graph
requires: ["01-01", "01-02"]
provides:
  - "Verified uv pip install . works end-to-end"
  - "Verified pip install . works end-to-end"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [no-build-isolation-install, force-cpu-build]

key-files:
  created: []
  modified: [setup.py, pyproject.toml]

key-decisions:
  - "Relative paths required in setup.py for setuptools compatibility (fixed absolute path issue)"
  - "License format must use table {text = 'Apache-2.0'} for setuptools<77 compat"
  - "setuptools>=64 sufficient (lowered from >=77)"
  - "import torch_butterfly PathFinder error is Phase 2 scope (EXT-01)"

patterns-established:
  - "Install testing with FORCE_CPU=1 and --no-build-isolation for CI/verification"
---

# Plan 01-03: Install Verification — SUMMARY

## Status: COMPLETE

## What Was Built

End-to-end install verification of the build pipeline:

1. **uv pip install . (--no-build-isolation, FORCE_CPU=1):** Success
   - Package: torch-butterfly==0.1.0
   - Metadata: Name=torch-butterfly, Requires=numpy,torch

2. **pip install . (--no-build-isolation, FORCE_CPU=1):** Success
   - Wheel: torch_butterfly-0.1.0-cp312-cp312-linux_x86_64.whl
   - Metadata: Name=torch-butterfly, Version=0.1.0, License=Apache-2.0

3. **No conda used at any step** (INST-04 satisfied)

## Fixes Applied During Verification

- **setup.py absolute paths:** Changed from `Path(__file__).resolve().parent / "csrc"` to `Path("csrc")` — setuptools requires relative paths
- **pyproject.toml license format:** Changed from SPDX string to table format `{text = "Apache-2.0"}` for setuptools<77 compat
- **setuptools version:** Lowered from `>=77` to `>=64`
- **Stale build artifacts:** `build/` and `torch_butterfly.egg-info/` from old absolute-path runs needed cleaning

## Known Issue (Phase 2)

`import torch_butterfly` fails at PathFinder `.so` loading — this is Phase 2 scope (EXT-01).

## Self-Check: PASSED

- [x] uv pip install . exits 0
- [x] pip install . exits 0
- [x] Package metadata shows correct name, version, dependencies
- [x] No conda used
- [x] FORCE_CPU=1 controls CUDA compilation
