# torch_butterfly — Build System Modernization

## What This Is

Modernize the packaging and build system for `torch_butterfly`, a PyTorch library implementing butterfly matrices for efficient structured linear transforms (FFT, DCT, Hadamard, circulant, etc.). The library has C++/CUDA extensions and currently uses a legacy `setup.py`-based build. The goal is to make it installable via `uv` with a modern `pyproject.toml`, targeting Python 3.10+ and PyTorch 2.x.

## Core Value

A single `uv pip install .` (or `uv pip install -e .`) that just works — with CUDA support when available, without conda or manual steps.

## Requirements

### Validated

- ✓ C++/CUDA butterfly multiply kernels (csrc/) — existing, working
- ✓ Python butterfly module layer (torch_butterfly/) — existing, working
- ✓ Special transforms (FFT, DCT, Hadamard, etc.) — existing, working
- ✓ Pure-PyTorch fallback when no CUDA — existing, working
- ✓ Test suite (tests/) — existing

### Active

- [ ] UV-compatible editable installation (uv pip install -e .)
- [ ] Fix extension loading for reliable imports (PathFinder replacement)
- [ ] Remove or isolate legacy code that blocks clean install

### Validated (Phase 1)

- ✓ pyproject.toml-based build with PEP 621 metadata — Phase 1
- ✓ UV-compatible non-editable installation (uv pip install .) — Phase 1
- ✓ pip install . works — Phase 1
- ✓ Python 3.10+ enforced in metadata — Phase 1
- ✓ PyTorch 2.x compatibility (torch>=2.0 as build+runtime dep) — Phase 1
- ✓ CUDA extension compilation with FORCE_CUDA/FORCE_CPU/TORCH_CUDA_ARCH_LIST — Phase 1
- ✓ Simplified dependencies (torch + numpy only, stale requirements.txt deleted) — Phase 1

### Out of Scope

- Pre-compiled wheel distribution — uncertain if library proves useful, not worth the effort
- Modernizing the C++/CUDA kernel code itself — only touching the build plumbing
- Updating experiment directories (cnn/, convolution/, transformer/, etc.) — not part of core package
- Adding new features or transforms — packaging only
- Legacy butterfly/ package modernization — focus on torch_butterfly/ only

## Context

- **Existing codebase:** Research library by Tri Dao (Hazy Research, Stanford). Two generations: legacy `butterfly/` and current `torch_butterfly/`. Only `torch_butterfly/` is in scope.
- **Current pain:** setup.py requires torch at import time (breaks pip/uv), conda environment needed, CUDA 10.1 era defaults, Python 3.6 era code.
- **C++/CUDA extensions:** Use `torch.utils.cpp_extension` (CppExtension/CUDAExtension) with `TORCH_LIBRARY` dispatch. This pattern works with modern PyTorch but needs build system adaptation for pyproject.toml.
- **Key env vars:** `FORCE_CUDA=1`, `FORCE_CPU=1`, `NVCC_FLAGS`, `BUILD_DOCS=1` — should be preserved.
- **sm_35 minimum CUDA arch** currently set — may need updating for modern GPUs.

## Constraints

- **Build system:** Must use pyproject.toml as the single source of truth for packaging
- **UV compatibility:** Must work with `uv pip install` without conda
- **CUDA support:** Must retain CUDA extension compilation via torch.utils.cpp_extension
- **Python:** >=3.10, <4
- **PyTorch:** >=2.0
- **Backwards compat:** No need to support Python <3.10 or PyTorch <2.0

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep torch.utils.cpp_extension | Works with PyTorch 2.x, avoids pre-compiled wheel complexity | — Pending |
| Target Python 3.10+ only | Modern packaging features, user's preference | — Pending |
| Target PyTorch 2.x only | Major API changes between 1.x and 2.x, simplifies compat | — Pending |
| Skip pre-compiled wheels | Library value unproven, packaging effort too high | — Pending |
| Focus on torch_butterfly/ only | Legacy butterfly/ package is being replaced | — Pending |

---
*Last updated: 2026-04-02 after Phase 1 completion*
