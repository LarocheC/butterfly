# Project Research Summary

**Project:** torch_butterfly build system modernization
**Domain:** PyTorch C++/CUDA extension packaging (setup.py to pyproject.toml migration)
**Researched:** 2026-04-02
**Confidence:** HIGH

## Executive Summary

torch_butterfly is a PyTorch C++/CUDA extension library for butterfly matrix multiplication. Its current build system uses a standalone setup.py that hard-imports torch at the top level, hardcodes the removed sm_35 CUDA architecture, and declares no build dependencies -- making `pip install .` and `uv pip install .` completely broken on modern toolchains. The fix is well-understood: adopt the hybrid pyproject.toml + thin setup.py pattern used by pytorch_scatter, xformers, and the official pytorch/extension-cpp example. All four research tracks converge on the same answer.

The recommended approach is: (1) create a pyproject.toml with `[build-system] requires = ["setuptools>=64", "wheel", "ninja", "torch>=2.0"]` and full PEP 621 metadata, (2) reduce setup.py to only ext_modules and BuildExtension cmdclass, (3) remove the hardcoded sm_35 architecture flag, and (4) fix the fragile PathFinder-based extension loading in `__init__.py`. This is a small, focused migration -- not a rewrite. The library has only three C++ source files.

The primary risk is CUDA version mismatch during build isolation: pip/uv may download a CPU-only torch into the isolated build environment. This is mitigatable through documentation (recommend `--no-build-isolation` for CUDA users) and the existing CUDA version check in `__init__.py`. A secondary risk is the brittle `PathFinder` + `no_python_abi_suffix` extension loading mechanism, which breaks under PEP 660 editable installs. Both risks have clear, tested solutions.

## Key Findings

### Recommended Stack

The stack is straightforward because PyTorch's own tooling dictates the build system. Every major PyTorch extension library uses setuptools + `torch.utils.cpp_extension`. Alternative build backends (scikit-build-core, meson-python, hatch, poetry) either lack C extension support or fight against PyTorch's native integration.

**Core technologies:**
- **setuptools >= 64** with `setuptools.build_meta`: build backend -- required for `torch.utils.cpp_extension` integration and PEP 660 editable installs
- **torch >= 2.0** as build dependency: provides `CppExtension`, `CUDAExtension`, `BuildExtension`
- **ninja >= 1.10** as build dependency: parallel C++ compilation, used automatically by BuildExtension
- **CUDA arch targets sm_70 through sm_90**: drop sm_35, default to Volta+ with `TORCH_CUDA_ARCH_LIST` env var override

### Expected Features

**Must have (table stakes):**
- pyproject.toml with `[build-system]` and `[project]` tables (enables PEP 517 builds)
- torch declared in `[build-system].requires` (fixes the broken `import torch` in setup.py)
- Modern CUDA arch flags (removes sm_35, fixes build on CUDA 12+)
- Python >= 3.10, PyTorch >= 2.0 constraints
- `[tool.setuptools.packages.find]` excluding legacy `butterfly/` directory
- FORCE_CUDA / FORCE_CPU env var support (preserve existing behavior)

**Should have (differentiators):**
- `[project.optional-dependencies]` for dev/test extras
- `TORCH_CUDA_ARCH_LIST` documentation
- uv integration guidance (index configuration for CUDA wheels)
- `-O3` optimization flag for C++ compilation
- Version single-sourcing (current version is `0.0.0`)

**Defer (v2+):**
- Pre-compiled wheel distribution (CI matrix for CUDA variants) -- explicitly out of scope
- Multi-backend support (ROCm, Intel XPU) -- research library, not production framework
- py.typed marker, conda recipes, complex platform-aware compilation flags

### Architecture Approach

Three-layer architecture: declarative metadata (pyproject.toml) feeds into a thin programmatic shim (setup.py with only ext_modules + cmdclass) which delegates to the compilation layer (torch.utils.cpp_extension). The migration preserves the existing `csrc/` source layout and extension auto-discovery pattern while moving all static metadata out of setup.py. Build-time data flow: pip/uv reads pyproject.toml, creates isolated env with torch, runs setup.py which discovers .cpp/.cu sources and compiles them via ninja.

**Major components:**
1. **pyproject.toml** -- all package metadata, build-system requires, package discovery config
2. **setup.py (thin shim)** -- only `get_extensions()` and `BuildExtension` cmdclass
3. **`__init__.py` (fixed)** -- `__file__`-relative extension loading replacing fragile PathFinder hack

### Critical Pitfalls

1. **Build isolation installs wrong PyTorch variant** -- pip/uv fetches CPU-only torch from PyPI by default. Mitigate by documenting `--no-build-isolation` for CUDA users and configuring uv PyTorch index.
2. **`import torch` at setup.py top level without build declaration** -- the exact bug that is broken today. Fix by adding torch to `[build-system].requires`.
3. **PathFinder breaks under PEP 660 editable installs** -- replace with `__file__`-relative `.so` discovery using `os.path` instead of `importlib.machinery.PathFinder`.
4. **Hardcoded sm_35 fails on CUDA 12+** -- remove entirely, let PyTorch/NVCC auto-detect or use env var.
5. **`version.cpp` uses deprecated `RegisterOperators` API** -- migrate to `TORCH_LIBRARY` macro for consistency with `butterfly.cpp` and future-proofing.

## Implications for Roadmap

### Phase 1: Core pyproject.toml and Build Fix
**Rationale:** This is the entire reason for the project. Everything else depends on having a working pyproject.toml. The CUDA arch fix must be simultaneous because sm_35 blocks any CUDA build on modern systems.
**Delivers:** Working `uv pip install .` and `pip install .` for the first time.
**Addresses:** pyproject.toml creation, torch as build dep, PEP 621 metadata, sm_35 removal, MANIFEST.in for csrc/, package discovery excluding butterfly/, ninja in build requires, setuptools license format.
**Avoids:** Pitfalls #1 (build isolation), #2 (import torch), #4 (sm_35), #9 (missing csrc/), #10 (license format), #11 (ninja).

### Phase 2: Extension Loading and Code Cleanup
**Rationale:** With pyproject.toml working, fix the runtime import mechanism that breaks editable installs. Group this with the deprecated API cleanup since both touch `csrc/` and `__init__.py`.
**Delivers:** Reliable editable installs (`uv pip install -e .`), modernized C++ operator registration.
**Addresses:** PathFinder replacement in `__init__.py`, `no_python_abi_suffix` evaluation, `version.cpp` migration to TORCH_LIBRARY macro.
**Avoids:** Pitfalls #3 (PathFinder), #5 (RegisterOperators), #6 (no_python_abi_suffix).

### Phase 3: Developer Experience and Documentation
**Rationale:** Polish phase. The build works, editable installs work, now document the workflows and add optional quality-of-life features.
**Delivers:** Clear development workflow docs, uv-specific guidance, optional-dependencies groups, version bump from 0.0.0.
**Addresses:** C++ rebuild workflow documentation, `TORCH_CUDA_ARCH_LIST` docs, `[tool.uv]` configuration guidance, optional-dependencies for dev/test.
**Avoids:** Pitfall #7 (C++ rebuild confusion), #8 (uv two-phase install friction).

### Phase Ordering Rationale

- Phase 1 must come first because literally nothing works without it -- the package cannot be installed.
- Phase 2 depends on Phase 1 because editable install testing requires a working pyproject.toml.
- Phase 3 is pure polish and documentation that can only be written after the build actually works.
- Each phase produces a testable, shippable increment. Phase 1 alone would be a valid minimal PR.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** The `no_python_abi_suffix` + PathFinder interaction needs empirical testing. Whether modern PyTorch's `load_library` handles ABI-tagged filenames is unclear from documentation alone. Build both variants and test.

Phases with standard patterns (skip research-phase):
- **Phase 1:** Extremely well-documented. The pytorch/extension-cpp example, pytorch_scatter, and xformers all demonstrate the exact pattern. Copy and adapt.
- **Phase 3:** Pure documentation and metadata. No technical risk.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Every major PyTorch extension uses identical stack. pytorch_scatter is direct ancestor. |
| Features | HIGH | Clear table stakes vs. nice-to-haves. Scope is narrow and well-defined. |
| Architecture | HIGH | Three-layer pattern is the only viable approach for PyTorch C++ extensions. |
| Pitfalls | HIGH (critical), MEDIUM (moderate) | Critical pitfalls verified against official examples. PathFinder and ABI suffix issues need empirical testing. |

**Overall confidence:** HIGH

### Gaps to Address

- **`no_python_abi_suffix` behavior with modern PyTorch**: needs testing during Phase 2. The pytorch/extension-cpp example no longer uses this option, suggesting it may be safe to remove.
- **uv `--torch-backend=auto` stability**: uv's PyTorch integration is evolving. Verify current behavior against latest uv docs when writing Phase 3 documentation.
- **setuptools version pinning (64 vs 77)**: STACK.md recommends >=64, ARCHITECTURE.md recommends >=77 (for license field change). Use >=64 as the minimum since it enables PEP 660, but use the SPDX license format that setuptools 77+ requires (it is backward-compatible with 64+).

## Sources

### Primary (HIGH confidence)
- [pytorch/extension-cpp](https://github.com/pytorch/extension-cpp) -- official PyTorch C++ extension example
- [pytorch_scatter](https://github.com/rusty1s/pytorch_scatter) -- direct ancestor of this project's setup.py, already migrated
- [torch.utils.cpp_extension docs](https://docs.pytorch.org/docs/stable/cpp_extension.html) -- BuildExtension, CppExtension, CUDAExtension API
- [Python Packaging: pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) -- PEP 517/518/621 standards
- [uv PyTorch integration](https://docs.astral.sh/uv/guides/integration/pytorch/) -- index config, --torch-backend

### Secondary (MEDIUM confidence)
- [pytorch_scatter issues #265, #381, #455](https://github.com/rusty1s/pytorch_scatter/issues) -- import torch in setup.py problem and fixes
- [PyTorch CUDA arch deprecation notices](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128)
- [uv issue #10694](https://github.com/astral-sh/uv/issues/10694) -- two-stage sync for PyTorch projects

---
*Research completed: 2026-04-02*
*Ready for roadmap: yes*
