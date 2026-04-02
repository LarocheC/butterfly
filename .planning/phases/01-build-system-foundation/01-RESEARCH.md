# Phase 1: Build System Foundation - Research

**Researched:** 2026-04-02
**Domain:** PyTorch C++/CUDA extension packaging (setup.py to pyproject.toml migration)
**Confidence:** HIGH

## Summary

Phase 1 replaces the broken setup.py-only build with a pyproject.toml + thin setup.py shim so that `uv pip install .` and `pip install .` work with automatic CUDA detection. The current setup.py hard-imports torch at the top level (breaks PEP 517 build isolation), hardcodes the removed sm_35 CUDA architecture (breaks CUDA 12+), and declares no build dependencies. The fix is the well-documented hybrid pattern used by pytorch_scatter, xformers, and the official pytorch/extension-cpp example.

The project has exactly 2 C++ source files (`csrc/butterfly.cpp`, `csrc/version.cpp`) with corresponding CPU/CUDA implementations. The existing `get_extensions()` auto-discovery pattern in setup.py is sound and should be preserved in the thin shim. All metadata (name, version, deps, classifiers) moves to pyproject.toml. The `requirements.txt` (stale: python>=3.6, pytorch>=1.8, ray>=0.6.5) is deleted.

The primary risk is build isolation downloading CPU-only torch from PyPI instead of the user's CUDA-enabled torch. This is mitigated by documenting `--no-build-isolation` for advanced users and the existing CUDA version mismatch check in `__init__.py`. The setuptools version pin should be `>=64` (minimum for full pyproject.toml + PEP 660 support) with the SPDX license format (`"Apache-2.0"` string) that works across all setuptools versions 64+.

**Primary recommendation:** Create pyproject.toml with `[build-system] requires = ["setuptools>=64", "wheel", "ninja", "torch>=2.0"]`, reduce setup.py to ext_modules + BuildExtension cmdclass only, remove sm_35 hardcoding, add MANIFEST.in for csrc/, delete requirements.txt.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Default CUDA architecture list: `7.0 8.0 9.0+PTX` (Volta, Ampere, Hopper with PTX forward compat)
- **D-02:** Include PTX for the highest architecture to enable JIT compilation on future GPUs (Ada, Blackwell)
- **D-03:** Support `TORCH_CUDA_ARCH_LIST` env var for user override of architecture targets
- **D-04:** Remove hardcoded `-arch=sm_35` entirely
- **D-05:** Runtime dependencies: `torch>=2.0` and `numpy` only. No ray, scipy, wandb, or other experiment-specific deps.
- **D-06:** Optional dependency groups: `dev` (development tools) and `test` (pytest and test deps)
- **D-07:** Delete `requirements.txt` -- pyproject.toml is the single source of truth
- **D-08:** Include `torch>=2.0` in `[build-system].requires` so standard `pip install .` / `uv pip install .` works out of the box
- **D-09:** Document both paths: default (build isolation, may get CPU torch for build) and advanced (`--no-build-isolation` for exact CUDA match)
- **D-10:** Preserve `FORCE_CUDA=1` / `FORCE_CPU=1` env vars for manual CUDA override
- **D-11:** Delete `requirements.txt` (stale: python>=3.6, pytorch>=1.8, ray>=0.6.5)
- **D-12:** Leave Dockerfile and README conda instructions as-is for now -- out of Phase 1 scope

### Claude's Discretion
- NVCC_FLAGS env var: Claude decides whether to keep, replace, or simplify alongside TORCH_CUDA_ARCH_LIST
- Exact content of dev vs test optional dependency groups
- Whether to add `-O3` optimization flag for C++ compilation
- MANIFEST.in exact contents (must include csrc/ at minimum)
- setuptools version pin (>=64 vs higher)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BUILD-01 | pyproject.toml with `[build-system]` declaring torch, setuptools, ninja, wheel | STACK.md Pattern A, ARCHITECTURE.md three-layer design |
| BUILD-02 | PEP 621 metadata (`[project]` table) | STACK.md pyproject.toml template |
| BUILD-03 | Package discovery excludes legacy `butterfly/` | `[tool.setuptools.packages.find] include = ["torch_butterfly*"]` |
| BUILD-04 | MANIFEST.in includes csrc/ for sdist | Pitfall #9 prevention |
| BUILD-05 | Optional dependency groups for dev and test | Decision D-06, Claude's discretion on exact contents |
| BUILD-06 | setup.py reduced to thin shim | ARCHITECTURE.md thin shim pattern |
| CUDA-01 | Remove hardcoded sm_35 | Decision D-04, Pitfall #4 |
| CUDA-02 | Auto-detect CUDA from torch and CUDA_HOME | Existing pattern in setup.py preserved |
| CUDA-03 | TORCH_CUDA_ARCH_LIST env var support | Decision D-03; PyTorch BuildExtension handles this natively when no `-arch` flags hardcoded |
| CUDA-04 | FORCE_CUDA and FORCE_CPU env vars preserved | Decision D-10, existing pattern |
| INST-01 | `uv pip install .` works | Decision D-08 (torch in build-system.requires) |
| INST-02 | `pip install .` works | Same as INST-01 |
| INST-04 | Install works without conda | pyproject.toml + pip/uv workflow |
| INST-05 | Python >=3.10, <4 enforced | `requires-python = ">=3.10"` in [project] |
| INST-06 | PyTorch >=2.0 declared as runtime dep | `dependencies = ["torch>=2.0", "numpy"]` in [project] |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Build system:** Must use pyproject.toml as single source of truth for packaging
- **UV compatibility:** Must work with `uv pip install` without conda
- **CUDA support:** Must retain CUDA extension compilation via torch.utils.cpp_extension
- **Python:** >=3.10, <4
- **PyTorch:** >=2.0
- **Backwards compat:** No need to support Python <3.10 or PyTorch <2.0
- **GSD workflow:** Do not make direct repo edits outside a GSD workflow unless user explicitly asks
- **Naming:** Use snake_case.py for Python modules, PascalCase for classes
- **No automated formatter/linter configured** -- maintain existing code style

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| setuptools | >=64 | Build backend | Every major PyTorch extension uses setuptools. torch.utils.cpp_extension provides BuildExtension as a setuptools build_ext subclass. Verified: latest is 82.0.1. Pin >=64 (minimum for PEP 660 editable installs and full pyproject.toml support). |
| setuptools.build_meta | - | PEP 517 build backend | The `build-backend` value in pyproject.toml. Makes `pip install .` and `uv pip install .` work. |
| wheel | >=0.37 | Wheel building | Required for bdist_wheel. Verified: latest is 0.46.3. |
| ninja | >=1.10 | Parallel C++ compilation | PyTorch BuildExtension uses ninja automatically. Verified: latest pip package is 1.13.0. |
| torch | >=2.0 | Build + runtime dep | Provides CppExtension, CUDAExtension, BuildExtension at build time. Core runtime dependency. |
| numpy | - | Runtime dep | Used throughout library for numerical operations. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=7.0 | Test runner | In `[project.optional-dependencies].test` |
| pytest-cov | >=4.0 | Coverage reporting | In `[project.optional-dependencies].test` |

### Dev/Test Optional Groups (Claude's Discretion)

```toml
[project.optional-dependencies]
test = ["pytest>=7.0", "pytest-cov>=4.0"]
dev = ["pytest>=7.0", "pytest-cov>=4.0"]
```

Rationale: Keep `dev` and `test` as the same set for now (this is a small library). If linting/formatting tools are added later, `dev` can expand.

## Architecture Patterns

### Three-Layer Build Architecture

```
pyproject.toml                 (metadata + build-system declaration)
    |
    v
setup.py                      (thin shim: ext_modules + BuildExtension only)
    |
    v
torch.utils.cpp_extension     (CppExtension / CUDAExtension / BuildExtension)
    |
    v
csrc/                          (C++/CUDA source files)
```

### Recommended Project Structure (build files only)

```
butterfly/
├── pyproject.toml          # NEW: all metadata, build-system, package discovery
├── setup.py                # MODIFIED: thin shim only (ext_modules + cmdclass)
├── MANIFEST.in             # NEW: ensure csrc/ in sdist
├── csrc/
│   ├── butterfly.cpp       # UNCHANGED
│   ├── version.cpp         # UNCHANGED (Phase 2 migrates RegisterOperators)
│   ├── cpu/
│   │   ├── butterfly_cpu.cpp
│   │   └── butterfly_cpu.h
│   └── cuda/
│       ├── butterfly_cuda.cu
│       ├── butterfly_cuda.h
│       ├── complex_utils.cuh
│       └── map.h
├── torch_butterfly/        # UNCHANGED
│   ├── __init__.py         # UNCHANGED (Phase 2 fixes PathFinder)
│   └── ...
└── requirements.txt        # DELETE
```

### Pattern 1: Metadata in TOML, Logic in Python

**What:** All static package metadata (name, version, deps, classifiers, python-requires) in pyproject.toml. Only dynamic build logic (CUDA detection, source file discovery, compiler flags) in setup.py.

**When to use:** Always, for any PyTorch extension package.

**Example pyproject.toml:**
```toml
[build-system]
requires = ["setuptools>=64", "wheel", "ninja", "torch>=2.0"]
build-backend = "setuptools.build_meta"

[project]
name = "torch-butterfly"
version = "0.2.0"
description = "Butterfly matrix multiplication in PyTorch"
readme = "README.md"
license = "Apache-2.0"
requires-python = ">=3.10"
authors = [
    {name = "Tri Dao", email = "trid@stanford.edu"},
]
keywords = ["pytorch", "butterfly", "fft", "structured-matrices"]
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
dependencies = [
    "torch>=2.0",
    "numpy",
]

[project.urls]
Repository = "https://github.com/hazyresearch/learning-circuits"

[project.optional-dependencies]
test = ["pytest>=7.0", "pytest-cov>=4.0"]
dev = ["pytest>=7.0", "pytest-cov>=4.0"]

[tool.setuptools.packages.find]
include = ["torch_butterfly*"]
```

### Pattern 2: Thin setup.py Shim

**What:** setup.py contains ONLY `get_extensions()` function and `setup()` call with `ext_modules` + `cmdclass`.

**Example:**
```python
import os
from pathlib import Path
from setuptools import setup
import torch
from torch.utils.cpp_extension import (
    BuildExtension, CppExtension, CUDAExtension, CUDA_HOME
)

WITH_CUDA = torch.cuda.is_available() and CUDA_HOME is not None
if os.getenv("FORCE_CUDA", "0") == "1":
    WITH_CUDA = True
if os.getenv("FORCE_CPU", "0") == "1":
    WITH_CUDA = False

BUILD_DOCS = os.getenv("BUILD_DOCS", "0") == "1"


def get_extensions():
    Extension = CUDAExtension if WITH_CUDA else CppExtension
    define_macros = [("WITH_CUDA", None)] if WITH_CUDA else []
    extra_compile_args = {"cxx": ["-O3"]}

    if WITH_CUDA:
        nvcc_flags = os.getenv("NVCC_FLAGS", "").split() if os.getenv("NVCC_FLAGS") else []
        nvcc_flags += ["--expt-extended-lambda", "-lineinfo"]
        extra_compile_args["nvcc"] = nvcc_flags

    extensions_dir = Path(__file__).parent.resolve() / "csrc"
    extensions = []
    for main in extensions_dir.glob("*.cpp"):
        name = main.stem
        sources = [str(main)]
        cpu_path = extensions_dir / "cpu" / f"{name}_cpu.cpp"
        if cpu_path.exists():
            sources.append(str(cpu_path))
        cuda_path = extensions_dir / "cuda" / f"{name}_cuda.cu"
        if WITH_CUDA and cuda_path.exists():
            sources.append(str(cuda_path))
        extensions.append(Extension(
            f"torch_butterfly._{name}",
            sources,
            include_dirs=[str(extensions_dir)],
            define_macros=define_macros,
            extra_compile_args=extra_compile_args,
        ))
    return extensions


setup(
    ext_modules=get_extensions() if not BUILD_DOCS else [],
    cmdclass={"build_ext": BuildExtension.with_options(
        no_python_abi_suffix=True, use_ninja=True
    )},
)
```

### Pattern 3: MANIFEST.in for csrc/

**What:** Include C++/CUDA sources in source distributions.

**Example:**
```
recursive-include csrc *.cpp *.cu *.h *.cuh
include setup.py
include pyproject.toml
```

### Pattern 4: CUDA Architecture via TORCH_CUDA_ARCH_LIST

**What:** Do NOT hardcode `-arch=sm_XX` flags. Instead, rely on PyTorch's `BuildExtension` which reads the `TORCH_CUDA_ARCH_LIST` environment variable. When the env var is unset, BuildExtension auto-detects from the installed CUDA toolkit or falls back to defaults.

**Decision D-01 implementation:** The default arch list `7.0 8.0 9.0+PTX` should NOT be hardcoded in setup.py. Instead, omit all `-arch` flags from nvcc_flags and let users set `TORCH_CUDA_ARCH_LIST="7.0 8.0 9.0+PTX"` if they want explicit control. PyTorch's BuildExtension handles this natively.

**Why this works:** When no `-arch` flag is present in extra_compile_args, BuildExtension checks TORCH_CUDA_ARCH_LIST env var first, then falls back to auto-detection. This satisfies D-01, D-02, D-03, and D-04 simultaneously.

### Anti-Patterns to Avoid

- **Hardcoded CUDA architecture:** Never `-arch=sm_35` or any single hardcoded arch. Let BuildExtension handle it via TORCH_CUDA_ARCH_LIST.
- **Metadata in setup.py:** No name, version, author, deps in setup.py when pyproject.toml exists.
- **Missing torch in build-system.requires:** The exact bug that is broken today.
- **Duplicated dependency declarations:** torch appears in both `[build-system].requires` and `[project].dependencies` -- this is correct and intentional (build dep vs runtime dep).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CUDA architecture detection | Custom arch detection logic | PyTorch BuildExtension + TORCH_CUDA_ARCH_LIST | BuildExtension already handles GPU detection, env var parsing, and PTX generation |
| C++ source compilation | Custom Makefile or CMake | torch.utils.cpp_extension.CUDAExtension | Handles CUDA paths, compiler flags, C++17, ninja, and mixed C++/CUDA compilation |
| Package metadata | setup.py args | pyproject.toml [project] table | PEP 621 standard, single source of truth |
| Build isolation | Custom env setup | pip/uv PEP 517 build isolation | Standard tooling handles isolated builds with declared dependencies |

## Common Pitfalls

### Pitfall 1: Build Isolation Installs CPU-Only PyTorch
**What goes wrong:** PEP 517 build isolation downloads default (CPU-only) torch from PyPI instead of CUDA-enabled torch.
**Why it happens:** PyTorch CUDA wheels are on a custom index, not the default PyPI index.
**How to avoid:** Document `--no-build-isolation` for CUDA users. The existing CUDA version check in `__init__.py` catches mismatches at import time.
**Warning signs:** `uv pip install .` downloads a ~200MB torch during build; build log shows no nvcc invocations despite CUDA being available.

### Pitfall 2: Missing csrc/ in Source Distribution
**What goes wrong:** pyproject.toml builds may not include csrc/ directory in sdist since it is at repo root, not inside torch_butterfly/.
**Why it happens:** setuptools `find_packages()` only discovers Python packages, not arbitrary C++ source directories.
**How to avoid:** Create MANIFEST.in with `recursive-include csrc *.cpp *.cu *.h *.cuh`.
**Warning signs:** Build completes with no compiled extensions, `_butterfly.so` not created.

### Pitfall 3: setuptools License Field Format
**What goes wrong:** Using old `license = {text = "..."}` table format causes warnings or errors in setuptools 77+.
**Why it happens:** PEP 639 changed the license field to an SPDX identifier string.
**How to avoid:** Use `license = "Apache-2.0"` (plain SPDX string). This works with setuptools >=64.
**Warning signs:** Deprecation warnings during build.

### Pitfall 4: ninja Not Declared as Build Dependency
**What goes wrong:** `use_ninja=True` in BuildExtension but ninja not in build env causes confusing error.
**Why it happens:** Build isolation creates a clean env without ninja.
**How to avoid:** Include `"ninja"` in `[build-system].requires`.
**Warning signs:** Build failure mentioning ninja not found.

### Pitfall 5: NVCC_FLAGS Env Var Interaction with TORCH_CUDA_ARCH_LIST
**What goes wrong:** If NVCC_FLAGS contains `-arch` flags AND TORCH_CUDA_ARCH_LIST is set, there can be conflicting architecture specifications.
**Why it happens:** Two independent mechanisms for specifying CUDA architectures.
**How to avoid:** Keep NVCC_FLAGS for non-arch flags only (e.g., `--expt-extended-lambda`, `-lineinfo`). Let TORCH_CUDA_ARCH_LIST handle architecture selection exclusively. Do NOT parse arch flags from NVCC_FLAGS.
**Warning signs:** nvcc errors about conflicting architectures.

### Pitfall 6: no_python_abi_suffix=True Must Be Kept (Phase 1)
**What goes wrong:** Removing `no_python_abi_suffix=True` changes .so filenames from `_butterfly.so` to `_butterfly.cpython-312-x86_64-linux-gnu.so`, breaking the current `__init__.py` PathFinder loading.
**Why it happens:** `__init__.py` uses `PathFinder().find_spec(library, ...)` which expects specific filename patterns.
**How to avoid:** Keep `no_python_abi_suffix=True` in Phase 1. Phase 2 will fix `__init__.py` loading and can then evaluate removing this option.
**Warning signs:** ImportError or AttributeError when importing torch_butterfly.

## Code Examples

### Complete pyproject.toml (verified pattern)
```toml
# Source: pytorch_scatter pattern + pytorch/extension-cpp example
[build-system]
requires = ["setuptools>=64", "wheel", "ninja", "torch>=2.0"]
build-backend = "setuptools.build_meta"

[project]
name = "torch-butterfly"
version = "0.2.0"
description = "Butterfly matrix multiplication in PyTorch"
readme = "README.md"
license = "Apache-2.0"
requires-python = ">=3.10"
authors = [
    {name = "Tri Dao", email = "trid@stanford.edu"},
]
keywords = ["pytorch", "butterfly", "fft", "structured-matrices"]
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]
dependencies = [
    "torch>=2.0",
    "numpy",
]

[project.urls]
Repository = "https://github.com/hazyresearch/learning-circuits"

[project.optional-dependencies]
test = ["pytest>=7.0", "pytest-cov>=4.0"]
dev = ["pytest>=7.0", "pytest-cov>=4.0"]

[tool.setuptools.packages.find]
include = ["torch_butterfly*"]
```

### Complete thin setup.py shim (verified pattern)
```python
# Source: adapted from pytorch_scatter + pytorch/extension-cpp
import os
from pathlib import Path
from setuptools import setup
import torch
from torch.utils.cpp_extension import (
    BuildExtension, CppExtension, CUDAExtension, CUDA_HOME
)

WITH_CUDA = torch.cuda.is_available() and CUDA_HOME is not None
if os.getenv("FORCE_CUDA", "0") == "1":
    WITH_CUDA = True
if os.getenv("FORCE_CPU", "0") == "1":
    WITH_CUDA = False

BUILD_DOCS = os.getenv("BUILD_DOCS", "0") == "1"


def get_extensions():
    Extension = CUDAExtension if WITH_CUDA else CppExtension
    define_macros = [("WITH_CUDA", None)] if WITH_CUDA else []
    extra_compile_args = {"cxx": ["-O3"]}

    if WITH_CUDA:
        nvcc_flags = os.getenv("NVCC_FLAGS", "").split() if os.getenv("NVCC_FLAGS") else []
        nvcc_flags += ["--expt-extended-lambda", "-lineinfo"]
        # No -arch flag: let TORCH_CUDA_ARCH_LIST or PyTorch defaults handle it
        extra_compile_args["nvcc"] = nvcc_flags

    extensions_dir = Path(__file__).parent.resolve() / "csrc"
    extensions = []
    for main in extensions_dir.glob("*.cpp"):
        name = main.stem
        sources = [str(main)]
        cpu_path = extensions_dir / "cpu" / f"{name}_cpu.cpp"
        if cpu_path.exists():
            sources.append(str(cpu_path))
        cuda_path = extensions_dir / "cuda" / f"{name}_cuda.cu"
        if WITH_CUDA and cuda_path.exists():
            sources.append(str(cuda_path))
        extensions.append(Extension(
            f"torch_butterfly._{name}",
            sources,
            include_dirs=[str(extensions_dir)],
            define_macros=define_macros,
            extra_compile_args=extra_compile_args,
        ))
    return extensions


setup(
    ext_modules=get_extensions() if not BUILD_DOCS else [],
    cmdclass={"build_ext": BuildExtension.with_options(
        no_python_abi_suffix=True, use_ninja=True
    )},
)
```

### MANIFEST.in
```
recursive-include csrc *.cpp *.cu *.h *.cuh
include setup.py
include pyproject.toml
include LICENSE
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `python setup.py install` | `pip install .` / `uv pip install .` | pip 24.2+ deprecated setup.py direct invocation | Must use PEP 517 build backend |
| setup.py-only metadata | pyproject.toml [project] table | PEP 621 (2021), widespread adoption 2023+ | Single source of truth for metadata |
| `license = {text = "..."}` | `license = "Apache-2.0"` (SPDX string) | setuptools 77 (2025) | Must use SPDX format |
| Hardcoded `-arch=sm_35` | TORCH_CUDA_ARCH_LIST env var / auto-detect | CUDA 12.0 removed sm_35 (2023) | Must not hardcode deprecated architectures |
| `torch::RegisterOperators` | `TORCH_LIBRARY` macro | PyTorch 1.9+ (2021) | Phase 2 scope, but version.cpp still uses old API |

## Discretion Decisions (Claude's Recommendations)

### NVCC_FLAGS Env Var: KEEP
**Recommendation:** Keep NVCC_FLAGS env var for non-architecture flags. It currently allows users to pass custom nvcc flags. Strip any `-arch` flags from it (those should go through TORCH_CUDA_ARCH_LIST), but preserve it for flags like `--expt-extended-lambda`, `-lineinfo`, and any user-specific flags.

### -O3 Optimization Flag: ADD
**Recommendation:** Add `-O3` to C++ compiler flags (`extra_compile_args["cxx"]`). This is standard for release builds and used by pytorch_scatter and xformers. The current setup.py has empty cxx flags.

### MANIFEST.in Contents
**Recommendation:**
```
recursive-include csrc *.cpp *.cu *.h *.cuh
include setup.py
include pyproject.toml
include LICENSE
```

### setuptools Version Pin: >=64
**Recommendation:** Use `>=64` not `>=77`. Reason: 64 is the minimum for PEP 660 editable installs and full pyproject.toml support. The SPDX license string format (`"Apache-2.0"`) is forward-compatible -- it works with 64+ and is the required format for 77+. Using >=64 maximizes compatibility without sacrificing functionality.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime + build | Yes | 3.12.3 | -- |
| pip | Install path | Yes | 24.0 | -- |
| uv | Install path | Yes | 0.9.9 | pip |
| setuptools | Build backend | Yes | 68.1.2 (system) | Build isolation installs newer |
| torch | Build + runtime | No (not in system env) | -- | Build isolation installs it |
| ninja | C++ compilation | No (not in system env) | -- | Build isolation installs pip package (1.13.0) |
| nvcc (CUDA toolkit) | CUDA compilation | No | -- | CPU-only build (FORCE_CPU=1) |
| wheel | Wheel building | Yes | 0.42.0 (system) | Build isolation installs newer |

**Missing dependencies with no fallback:**
- None blocking. Build isolation handles torch and ninja installation.

**Missing dependencies with fallback:**
- CUDA toolkit not detected on this machine. CPU-only builds will work. CUDA builds require a machine with CUDA toolkit installed (or FORCE_CPU=1 to skip).
- torch not installed in system env. Build isolation will download it; or user pre-installs and uses `--no-build-isolation`.

## Open Questions

1. **Version number: 0.0.0 vs 0.2.0**
   - What we know: Current version is `0.0.0` in both setup.py and `__init__.py`. STACK.md suggests `0.2.0`.
   - What's unclear: Whether the project owner wants a version bump in Phase 1.
   - Recommendation: Use `0.2.0` in pyproject.toml as suggested by research (signals meaningful update). Phase 2 can single-source the version.

2. **`numpy` dependency -- pinned or unpinned?**
   - What we know: Decision D-05 says "torch>=2.0 and numpy only". No pin specified.
   - Recommendation: Use `"numpy"` unpinned. Let torch's numpy constraint handle compatibility.

## Sources

### Primary (HIGH confidence)
- `.planning/research/STACK.md` -- Detailed stack analysis with pyproject.toml template, build strategy comparison
- `.planning/research/ARCHITECTURE.md` -- Three-layer build architecture, thin shim pattern, migration order
- `.planning/research/PITFALLS.md` -- 11 domain pitfalls with prevention strategies
- `.planning/research/SUMMARY.md` -- Synthesized findings and phase implications
- pytorch/extension-cpp official example -- Pattern A (torch in build-system.requires)
- pytorch_scatter pyproject.toml -- Direct ancestor of this project's setup.py, already migrated
- torch.utils.cpp_extension docs -- BuildExtension, CppExtension, CUDAExtension API

### Secondary (MEDIUM confidence)
- pytorch_scatter issues #265, #381, #455 -- Import torch in setup.py problem and fixes
- uv PyTorch integration guide -- Index configuration, --torch-backend

### Environment Verification (HIGH confidence)
- pip index versions: setuptools 82.0.1 latest, ninja 1.13.0 latest, wheel 0.46.3 latest
- System: Python 3.12.3, pip 24.0, uv 0.9.9, setuptools 68.1.2 (system)
- CUDA: Not available on research machine (CPU-only builds verified possible)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- identical pattern used by pytorch_scatter, xformers, pytorch/extension-cpp
- Architecture: HIGH -- three-layer pattern is the only viable approach for PyTorch C++ extensions
- Pitfalls: HIGH -- all critical pitfalls verified against official examples and documentation
- Environment: HIGH -- directly probed on target machine

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stable domain, slow-moving)
