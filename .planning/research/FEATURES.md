# Feature Landscape

**Domain:** Python packaging modernization for a PyTorch C++/CUDA extension library
**Project:** torch_butterfly build system modernization
**Researched:** 2026-04-02

## Table Stakes

Features users expect from a modern Python package with C++/CUDA extensions. Missing any of these means the build feels broken or outdated.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `pyproject.toml` as packaging entry point | PEP 517/518 is the standard since 2019. Every modern tool (pip, uv, build) expects it. `setup.py`-only packages break `uv pip install` workflows. | Low | Minimal file: `[build-system]` with `requires = ["setuptools", "torch"]` and `build-backend = "setuptools.build_meta"`. This is exactly what pytorch_scatter does. |
| `[project]` metadata table | PEP 621 is the standard for declaring name, version, description, authors, license, classifiers, Python version. Replaces `setup()` kwargs. | Low | Move all static metadata from `setup()` into `[project]`. Keep `setup.py` only for `ext_modules` logic. |
| `torch` in build-system requires | Without this, `setup.py` fails on import because `torch` is not installed during the build isolation phase. This is the exact bug that breaks `pip install` and `uv pip install`. | Low | Critical fix. The current `setup.py` does `import torch` at the top level. Adding torch to `[build-system].requires` ensures it is available before `setup.py` runs. |
| Python 3.10+ version constraint | Current `python_requires='>=3.6'` is stale. Python 3.6-3.9 are EOL. Declaring `>=3.10` signals the package is maintained and prevents broken installs on unsupported interpreters. | Low | Single line: `requires-python = ">=3.10"` |
| PyTorch 2.x dependency declaration | Users need to know what PyTorch version is required. Currently `install_requires` is empty -- torch is not declared as a runtime dependency at all. | Low | Add `dependencies = ["torch>=2.0"]` in `[project]`. |
| Modern CUDA arch flags | Current code hardcodes `-arch=sm_35`. SM 3.5 was dropped from CUDA 12+. This causes build failures on any system with CUDA 12 or later. | Medium | Remove hardcoded `sm_35`. Use `TORCH_CUDA_ARCH_LIST` env var if set, otherwise let PyTorch's `CUDAExtension` auto-detect the GPU architecture. This is what well-maintained extensions do. |
| `FORCE_CUDA` / `FORCE_CPU` env var support | Standard pattern for PyTorch extension packages. Users building in CI or cross-compiling need explicit control over CUDA vs CPU builds. | Low | Already implemented. Preserve as-is. |
| Ninja build backend | Dramatically speeds up C++ compilation. PyTorch's `BuildExtension` defaults to Ninja when available. | Low | Already enabled via `use_ninja=True`. Preserve. |
| Editable install support (`pip install -e .`) | Required for development workflows. Setuptools supports PEP 660 editable installs with pyproject.toml since setuptools 64+. | Low | Works automatically with setuptools as backend. No special config needed beyond having `[build-system]` declared. |
| Clean dependency list | Current setup has empty `install_requires`, commented-out `setup_requires` and `tests_require`. Stale dependency metadata is confusing. | Low | Declare actual runtime deps in `[project].dependencies`. Use `[project.optional-dependencies]` for dev/test extras. |

## Differentiators

Features that improve developer/user experience but are not strictly required for the package to function.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `[project.optional-dependencies]` groups | Lets users do `pip install torch_butterfly[dev]` or `[test]` to get pytest, etc. Clean separation of runtime vs development deps. | Low | Group test deps under `[test]`, dev tools under `[dev]`. |
| `TORCH_CUDA_ARCH_LIST` documentation | Users building from source on specific GPU hardware benefit from knowing they can set `TORCH_CUDA_ARCH_LIST="7.0 8.0 9.0"` to control compilation targets. | Low | Document in README or BUILDING.md. No code change needed if auto-detect is used. |
| `uv` integration guidance | Declaring a PyTorch index source for CUDA builds in `pyproject.toml` via `[tool.uv.sources]` lets uv resolve the correct CUDA-enabled torch wheel. The `--torch-backend=auto` flag in uv 0.5.3+ can auto-detect GPU hardware. | Medium | Optional `[tool.uv]` section. Not all users use uv, but the project goal specifically targets uv compatibility. |
| Build isolation compatibility | Ensuring the package builds correctly under PEP 517 build isolation (where build deps are installed in a temporary venv). Some PyTorch extensions break here because `torch` path detection fails. | Medium | Tested by running `pip install --no-build-isolation .` and `pip install .` (with isolation). The `[build-system].requires` fix handles most cases. |
| `py.typed` marker | PEP 561 marker file indicating the package ships type information. Enables type checking in downstream code. | Low | Single empty file `torch_butterfly/py.typed`. Not critical for a research library but signals quality. |
| Classifiers and project URLs | PyPI classifiers (Development Status, Framework :: PyTorch, License, etc.) and project URLs (homepage, repository, issues) help discoverability. | Low | Pure metadata, no functional impact. |
| `[tool.setuptools.packages.find]` config | Replaces the hardcoded `packages=['torch_butterfly']` with automatic package discovery. Prevents forgetting to add new sub-packages. | Low | `[tool.setuptools.packages.find]` with `include = ["torch_butterfly*"]` to exclude legacy `butterfly/` and experiment dirs. |
| Platform-aware compilation flags | Adding `-O3` optimization, proper OpenMP flags, and platform-specific handling (macOS ARM64, Windows MSVC). pytorch_scatter does this well. | Medium | Current setup is minimal on compiler flags. Adding `-O3` for release builds and OpenMP support improves performance. |
| Version single-sourcing | Having version defined once (in `pyproject.toml` or `__init__.py`) instead of duplicated in multiple places. Current version is `0.0.0`. | Low | Use `[project] version = "X.Y.Z"` or `dynamic = ["version"]` with `[tool.setuptools.dynamic]`. |

## Anti-Features

Things to deliberately NOT build. Complexity without payoff for this project.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Pre-compiled wheel distribution (CI matrix for CUDA variants) | Explicitly out of scope per PROJECT.md. Library value is unproven. Building wheels for N CUDA versions x M Python versions x P platforms is enormous CI cost. pytorch_scatter needed a dedicated wheel index (`https://data.pyg.org/whl/`). | Source-only distribution. Users compile C++/CUDA locally. |
| Custom build backend (scikit-build-core, meson-python, cmake) | PyTorch's `torch.utils.cpp_extension` already handles C++ and CUDA compilation through setuptools. Introducing cmake/scikit-build adds a second build system with no benefit -- the extensions already compile correctly. | Keep setuptools + `torch.utils.cpp_extension` (the pattern every PyTorch extension library uses). |
| Complex multi-backend support (ROCm, Intel XPU, Apple MPS) | torch_butterfly is a research library, not a production framework. ROCm/XPU support adds testing burden with minimal user demand. MPS does not use custom CUDA kernels. | Support CUDA and CPU-only. PyTorch handles MPS at the Python level automatically for ops that have fallback paths. |
| Monorepo packaging (multiple packages from one repo) | The repo has both `butterfly/` (legacy) and `torch_butterfly/` (current). Packaging both creates confusion. | Package only `torch_butterfly/`. Explicitly exclude `butterfly/` from package discovery. |
| `setup.cfg` as intermediate step | Some guides suggest migrating `setup.py` to `setup.cfg` first, then to `pyproject.toml`. This is wasted effort -- go directly to `pyproject.toml`. | Skip `setup.cfg` entirely. |
| Poetry or Hatch as build backend | Neither handles C++ extensions natively. Would require custom build hooks or shelling out to setuptools anyway. Adds a dependency with no benefit over bare setuptools for extension packages. | Use `setuptools.build_meta` -- the standard for packages with C extensions. |
| Conda recipe / conda-forge packaging | Adds maintenance burden. The goal is `uv pip install .` working without conda. | Focus on pip/uv installation. Conda users can still `pip install` within conda envs. |
| `BUILD_DOCS` env var for conditional extension skipping | Currently `ext_modules=get_extensions() if not BUILD_DOCS else []`. This is a hack for ReadTheDocs. Modern approach is to use autodoc-style documentation that does not import compiled extensions. | Remove `BUILD_DOCS` or keep it but do not expand it. Docs are out of scope. |

## Feature Dependencies

```
pyproject.toml [build-system] table
  |-> torch in build-system requires (MUST be simultaneous)
  |-> [project] metadata table (can be done together)
  |    |-> dependencies declaration (torch>=2.0)
  |    |-> optional-dependencies groups (test, dev)
  |    |-> python_requires
  |    |-> version single-sourcing
  |-> setuptools package discovery config

Modern CUDA arch flags
  |-> Remove hardcoded sm_35 (prerequisite)
  |-> TORCH_CUDA_ARCH_LIST support (auto-detect as default)

Editable install support
  |-> Requires pyproject.toml [build-system] (prerequisite)
  |-> Works automatically with setuptools >= 64

uv integration
  |-> Requires pyproject.toml (prerequisite)
  |-> [tool.uv.sources] for PyTorch index (optional enhancement)
```

## MVP Recommendation

Prioritize (these solve the core `uv pip install .` goal):

1. **pyproject.toml with [build-system] and [project]** -- This is the single most impactful change. It enables PEP 517 builds, declares torch as a build dependency, and makes `uv pip install .` work.
2. **Modern CUDA arch flags** -- Remove `sm_35`, use auto-detection. Without this, builds fail on CUDA 12+ systems.
3. **Clean dependency declaration** -- Declare `torch>=2.0` as runtime dependency, `python_requires=">=3.10"`.
4. **Package discovery exclusion** -- Ensure only `torch_butterfly/` is packaged, not `butterfly/` or experiment dirs.

Defer:
- **uv-specific [tool.uv] configuration**: Nice to have but not required for `uv pip install .` to work. The basic pyproject.toml fix is sufficient.
- **Platform-aware compilation flags**: Current compilation works. Optimization flags are polish, not blocking.
- **py.typed marker**: Type stubs for a research CUDA library are low priority.
- **Classifiers and project URLs**: Pure metadata, zero functional impact.

## Sources

- [PyTorch `torch.utils.cpp_extension` docs](https://docs.pytorch.org/docs/stable/cpp_extension.html) -- BuildExtension, CppExtension, CUDAExtension API
- [pytorch_scatter pyproject.toml](https://github.com/rusty1s/pytorch_scatter) -- Reference implementation of a PyTorch C++ extension package with modern packaging
- [pytorch_scatter issue #265](https://github.com/rusty1s/pytorch_scatter/issues/265) -- The exact `import torch` in setup.py problem and its fix
- [Python Packaging User Guide: pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) -- Official packaging standards
- [Using uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/) -- uv-specific PyTorch configuration, `--torch-backend`, index sources
- [setuptools: Building Extension Modules](https://setuptools.pypa.io/en/latest/userguide/ext_modules.html) -- C/C++ extension support in setuptools
- [NVIDIA CUDA arch reference](https://arnon.dk/matching-sm-architectures-arch-and-gencode-for-various-nvidia-cards/) -- SM architecture to GPU mapping
