# Project Retrospective

## Milestone: v1.0 — Build System Modernization

**Shipped:** 2026-04-02
**Phases:** 2 | **Plans:** 4

### What Was Built
- pyproject.toml with PEP 621 metadata, torch>=2.0 build dep, setuptools>=64 backend
- Thin setup.py shim with CUDA arch targeting (7.0 8.0 9.0+PTX via TORCH_CUDA_ARCH_LIST)
- Glob-based __file__-relative extension loading replacing fragile PathFinder
- TORCH_LIBRARY_FRAGMENT migration in version.cpp
- CUDA version check downgraded from RuntimeError to UserWarning
- scipy made lazy import in permutation.py

### What Worked
- Research-first approach: domain research identified the exact patterns (pytorch_scatter, pytorch/extension-cpp) before planning
- Parallel execution of Wave 1 plans saved time
- Incremental verification during execution caught real issues (absolute paths, license format, TORCH_LIBRARY collision) early

### What Was Inefficient
- Plan 01-01 agent ended up doing 01-02's work too (setup.py rewrite) — the two plans could have been one
- The 01-02 agent launched in a worktree but couldn't find its plan file (plans were committed after worktree creation)
- Build artifacts (build/, egg-info/) needed manual cleanup between test iterations

### Patterns Established
- Thin setup.py shim pattern for PyTorch C++ extensions with pyproject.toml
- TORCH_CUDA_ARCH_LIST as the standard env var for CUDA architecture control
- Glob-based .so discovery with platform-aware suffixes (.so, .pyd, .dylib)
- TORCH_LIBRARY_FRAGMENT when multiple .so files register ops in the same namespace

### Key Lessons
- Always clean build/ and egg-info/ between install tests — stale artifacts cause confusing failures
- setuptools version matters for license field format (SPDX string needs >=77, table format works with >=64)
- Worktree isolation + plan files committed separately = race condition. Consider committing plans before spawning worktree agents.

## Cross-Milestone Trends

(First milestone — trends will emerge with subsequent milestones)
