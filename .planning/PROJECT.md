# torch_butterfly — Build System Modernization

## What This Is

A PyTorch library implementing butterfly matrices for efficient structured linear transforms (FFT, DCT, Hadamard, circulant, etc.) with C++/CUDA extensions. Now installable via `uv pip install .` or `uv pip install -e .` with a modern `pyproject.toml`, targeting Python 3.10+ and PyTorch 2.x.

## Core Value

A single `uv pip install .` (or `uv pip install -e .`) that just works — with CUDA support when available, without conda or manual steps.

## Requirements

### Validated

- ✓ C++/CUDA butterfly multiply kernels (csrc/) — existing
- ✓ Python butterfly module layer (torch_butterfly/) — existing
- ✓ Special transforms (FFT, DCT, Hadamard, etc.) — existing
- ✓ Pure-PyTorch fallback when no CUDA — existing
- ✓ Test suite (tests/) — existing
- ✓ pyproject.toml-based build with PEP 621 metadata — v1.0
- ✓ UV-compatible installation (uv pip install . and -e .) — v1.0
- ✓ pip install . works — v1.0
- ✓ Python 3.10+ enforced in metadata — v1.0
- ✓ PyTorch 2.x compatibility — v1.0
- ✓ CUDA extension compilation with FORCE_CUDA/FORCE_CPU/TORCH_CUDA_ARCH_LIST — v1.0
- ✓ Simplified dependencies (torch + numpy only) — v1.0
- ✓ Glob-based extension loading replacing PathFinder — v1.0
- ✓ RegisterOperators migrated to TORCH_LIBRARY_FRAGMENT — v1.0
- ✓ CUDA version check downgraded to warning — v1.0

### Active

(None — v1.0 complete)

### Out of Scope

- Pre-compiled wheel distribution — library value unproven
- Legacy butterfly/ package modernization — focus on torch_butterfly/ only
- Experiment directory updates — not part of core package
- C++/CUDA kernel code changes — only build plumbing

## Context

Shipped v1.0 with 4 files changed (pyproject.toml created, setup.py rewritten, __init__.py rewritten, permutation.py scipy lazy import). requirements.txt deleted. Build system modernized from broken setup.py-only to working pyproject.toml + thin shim.

## Constraints

- **Build system:** pyproject.toml as single source of truth
- **UV compatibility:** Works with `uv pip install` without conda
- **CUDA support:** Retained via torch.utils.cpp_extension
- **Python:** >=3.10, <4
- **PyTorch:** >=2.0

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep torch.utils.cpp_extension | Works with PyTorch 2.x, avoids wheel complexity | ✓ Good |
| Target Python 3.10+ only | Modern packaging, user preference | ✓ Good |
| Target PyTorch 2.x only | Simplifies compat | ✓ Good |
| Skip pre-compiled wheels | Library value unproven | ✓ Good |
| CUDA arch 7.0 8.0 9.0+PTX | Volta through Hopper with forward compat | ✓ Good |
| Remove no_python_abi_suffix | Standard ABI tags with glob discovery | ✓ Good |
| TORCH_LIBRARY_FRAGMENT for version.cpp | Avoids namespace collision with butterfly.cpp | ✓ Good |
| Downgrade CUDA check to warning | Prevents crash on version mismatch | ✓ Good |
| setuptools>=64 (not >=77) | License table format compatible with older setuptools | ✓ Good |

---
*Last updated: 2026-04-02 after v1.0 milestone*
