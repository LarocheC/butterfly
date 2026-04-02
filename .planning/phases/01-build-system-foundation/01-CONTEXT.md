# Phase 1: Build System Foundation - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the broken setup.py-only build with a pyproject.toml + thin setup.py shim so that `uv pip install .` and `pip install .` work with automatic CUDA detection. This phase covers build configuration, metadata, CUDA architecture targeting, dependency declarations, and removal of stale files. It does NOT cover extension loading changes (`__init__.py` PathFinder fix) or C++ API modernization — those are Phase 2.

</domain>

<decisions>
## Implementation Decisions

### CUDA Architecture Targets
- **D-01:** Default CUDA architecture list: `7.0 8.0 9.0+PTX` (Volta, Ampere, Hopper with PTX forward compat)
- **D-02:** Include PTX for the highest architecture to enable JIT compilation on future GPUs (Ada, Blackwell)
- **D-03:** Support `TORCH_CUDA_ARCH_LIST` env var for user override of architecture targets
- **D-04:** Remove hardcoded `-arch=sm_35` entirely

### Dependency Declaration
- **D-05:** Runtime dependencies: `torch>=2.0` and `numpy` only. No ray, scipy, wandb, or other experiment-specific deps.
- **D-06:** Optional dependency groups: `dev` (development tools) and `test` (pytest and test deps)
- **D-07:** Delete `requirements.txt` — pyproject.toml is the single source of truth

### Build Isolation Strategy
- **D-08:** Include `torch>=2.0` in `[build-system].requires` so standard `pip install .` / `uv pip install .` works out of the box
- **D-09:** Document both paths: default (build isolation, may get CPU torch for build) and advanced (`--no-build-isolation` for exact CUDA match)
- **D-10:** Preserve `FORCE_CUDA=1` / `FORCE_CPU=1` env vars for manual CUDA override

### Legacy Cleanup
- **D-11:** Delete `requirements.txt` (stale: python>=3.6, pytorch>=1.8, ray>=0.6.5)
- **D-12:** Leave Dockerfile and README conda instructions as-is for now — out of Phase 1 scope

### Claude's Discretion
- NVCC_FLAGS env var: Claude decides whether to keep, replace, or simplify alongside TORCH_CUDA_ARCH_LIST
- Exact content of dev vs test optional dependency groups
- Whether to add `-O3` optimization flag for C++ compilation
- MANIFEST.in exact contents (must include csrc/ at minimum)
- setuptools version pin (>=64 vs higher)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Build System
- `.planning/research/STACK.md` — Recommended stack with pyproject.toml examples and rationale
- `.planning/research/ARCHITECTURE.md` — Three-layer build architecture (pyproject.toml → setup.py shim → torch.utils.cpp_extension)
- `.planning/research/PITFALLS.md` — 11 domain pitfalls with prevention strategies
- `.planning/research/SUMMARY.md` — Synthesized research findings and phase implications

### Current Code
- `setup.py` — Current build script to be reduced to thin shim
- `torch_butterfly/__init__.py` — Current extension loading (Phase 2 scope, but understand for context)
- `csrc/butterfly.cpp` — Main C++ extension with TORCH_LIBRARY macro (already modern)
- `csrc/version.cpp` — Version extension with deprecated RegisterOperators (Phase 2 scope)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `setup.py:get_extensions()` — Extension auto-discovery pattern (iterates csrc/*.cpp, finds matching cpu/cuda files). Keep this logic in the thin shim.
- `setup.py` FORCE_CUDA/FORCE_CPU env var handling — Preserve this pattern.
- `csrc/butterfly.cpp` TORCH_LIBRARY macro — Already uses modern operator registration.

### Established Patterns
- C++ sources in `csrc/`, CPU variants in `csrc/cpu/`, CUDA variants in `csrc/cuda/` — clean separation
- Extension naming: `torch_butterfly._butterfly`, `torch_butterfly._version`
- `--expt-extended-lambda` and `-lineinfo` NVCC flags currently used

### Integration Points
- `setup.py` is the only entry point for building — pyproject.toml wraps it
- `torch_butterfly/__init__.py` loads compiled extensions at import time via `torch.ops.load_library()`
- Package includes only `torch_butterfly/` directory (legacy `butterfly/` excluded)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches following the pytorch_scatter / pytorch/extension-cpp patterns identified in research.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-build-system-foundation*
*Context gathered: 2026-04-02*
