# Architecture Patterns

**Domain:** PyTorch C++/CUDA extension package build system modernization
**Researched:** 2026-04-02

## Recommended Architecture

The build system has three layers: a **declarative metadata layer** (pyproject.toml), a **programmatic build layer** (setup.py as a thin shim), and the **compilation layer** (torch.utils.cpp_extension). All package metadata lives in pyproject.toml. The only reason setup.py survives is that `torch.utils.cpp_extension.BuildExtension` is a setuptools `build_ext` subclass -- there is no way to declaratively specify ext_modules with dynamic CUDA detection in pure TOML.

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

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `pyproject.toml` | Package name, version, Python/PyTorch version constraints, build-system requires, project metadata, optional dependencies | pip/uv build frontend, setuptools backend |
| `setup.py` | Programmatic ext_modules definition (CUDA detection, source file discovery, compiler flags), BuildExtension cmdclass | pyproject.toml (implicitly, via setuptools backend), torch.utils.cpp_extension |
| `torch.utils.cpp_extension` | Compiler flag injection (C++17, CUDA paths), ninja build backend, mixed C++/CUDA compilation | setup.py (called by), system compiler toolchain, CUDA toolkit |
| `csrc/` | C++/CUDA source code for butterfly multiply kernels | Compiled by torch.utils.cpp_extension, loaded at runtime by `torch_butterfly/__init__.py` |

### Data Flow (Build Time)

1. User runs `uv pip install .` (or `pip install .`)
2. Build frontend reads `pyproject.toml` `[build-system]` to determine backend (`setuptools.build_meta`) and build dependencies
3. Build frontend creates isolated environment with `setuptools` and `torch` installed (see "Build Isolation" section below)
4. Build frontend invokes setuptools backend, which executes `setup.py`
5. `setup.py` imports `torch.utils.cpp_extension`, detects CUDA availability, discovers source files from `csrc/`
6. `BuildExtension` compiles C++/CUDA sources with appropriate flags (uses ninja when available)
7. Compiled `.so` files are placed alongside the `torch_butterfly/` package
8. Package is installed into the target environment

### Data Flow (Runtime)

1. `import torch_butterfly` triggers `__init__.py`
2. `__init__.py` uses `torch.ops.load_library()` to load compiled `_version.so` and `_butterfly.so`
3. Native ops registered via `TORCH_LIBRARY` become available as `torch.ops.torch_butterfly.*`
4. Python multiply functions call native ops; fall back to pure-PyTorch if extension not available

## The Two Viable Build Strategies

### Strategy A: torch in build-system.requires (RECOMMENDED)

```toml
[build-system]
requires = ["setuptools>=77", "torch>=2.0"]
build-backend = "setuptools.build_meta"
```

**This is the official PyTorch pattern.** The pytorch/extension-cpp reference repository uses exactly this approach. When pip/uv builds the package, it installs torch into the isolated build environment, then runs setup.py which imports torch for compilation.

**Pros:**
- Standard PEP 517 compliant -- `pip install .` and `uv pip install .` work without flags
- No user-facing complexity (no `--no-build-isolation` needed)
- Matches the official pytorch/extension-cpp example

**Cons:**
- Build isolation installs a fresh torch into the build env (large download, ~2GB)
- Risk of CUDA version mismatch between build-env torch and runtime torch
- Build takes longer due to torch download

**Mitigation for CUDA mismatch:** The existing CUDA version check in `__init__.py` catches mismatches at import time with a clear error message. For source installs (the only kind this project supports), the user's environment torch is used for both build and runtime when `--no-build-isolation` is passed.

### Strategy B: torch NOT in build-system.requires (flash-attn pattern)

```toml
[build-system]
requires = ["setuptools>=77"]
build-backend = "setuptools.build_meta"
```

Requires: `uv pip install --no-build-isolation .` or `pip install --no-build-isolation .`

**Pros:**
- No redundant torch download
- Guaranteed same torch version for build and runtime
- Faster builds

**Cons:**
- Requires `--no-build-isolation` flag -- breaks `uv pip install .` without flags
- Not PEP 517 compliant (setup.py imports torch which is not declared as build dep)
- Users must know to pass the flag

### Recommendation: Strategy A

Use Strategy A because the project goal is explicitly "a single `uv pip install .` that just works." Strategy B requires extra flags and user knowledge. The CUDA version mismatch risk is acceptable because:
1. The existing CUDA version check catches it at import time
2. For development, users can always add `--no-build-isolation` to use their local torch
3. The project does not distribute pre-built wheels, so builds always happen against the user's CUDA toolkit

## Target pyproject.toml Structure

```toml
[build-system]
requires = ["setuptools>=77", "torch>=2.0"]
build-backend = "setuptools.build_meta"

[project]
name = "torch-butterfly"
version = "0.1.0"
description = "Butterfly matrix multiplication in PyTorch"
readme = "README.md"
license = "Apache-2.0"
requires-python = ">=3.10"
authors = [
    { name = "Tri Dao", email = "trid@stanford.edu" },
]
keywords = ["pytorch", "butterfly", "fft", "structured-matrices"]
dependencies = [
    "torch>=2.0",
]

[project.optional-dependencies]
test = ["pytest"]

[tool.setuptools.packages.find]
include = ["torch_butterfly*"]
```

## Target setup.py Structure (Thin Shim)

The setup.py should contain ONLY the extension module logic that cannot be expressed in TOML:

```python
import os
from pathlib import Path
from setuptools import setup
import torch
from torch.utils.cpp_extension import (
    BuildExtension, CppExtension, CUDAExtension, CUDA_HOME
)

def get_extensions():
    WITH_CUDA = torch.cuda.is_available() and CUDA_HOME is not None
    if os.getenv("FORCE_CUDA", "0") == "1":
        WITH_CUDA = True
    if os.getenv("FORCE_CPU", "0") == "1":
        WITH_CUDA = False
    if os.getenv("BUILD_DOCS", "0") == "1":
        return []

    Extension = CUDAExtension if WITH_CUDA else CppExtension
    define_macros = [("WITH_CUDA", None)] if WITH_CUDA else []
    extra_compile_args = {"cxx": ["-O3"]}

    if WITH_CUDA:
        nvcc_flags = os.getenv("NVCC_FLAGS", "").split() if os.getenv("NVCC_FLAGS") else []
        nvcc_flags += ["--expt-extended-lambda", "-lineinfo"]
        # sm_50 is minimum for modern CUDA 12.x; sm_70+ for Volta and newer
        extra_compile_args["nvcc"] = nvcc_flags

    extensions_dir = Path(__file__).parent / "csrc"
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
    ext_modules=get_extensions(),
    cmdclass={"build_ext": BuildExtension.with_options(use_ninja=True)},
)
```

Key changes from current setup.py:
- **All metadata removed** -- lives in pyproject.toml now
- **No `name`, `version`, `packages`, etc.** -- only `ext_modules` and `cmdclass`
- **`no_python_abi_suffix=True` removed** -- evaluate whether this is still needed; it was for compatibility with older PyTorch loading patterns
- **`-arch=sm_35` removed** -- sm_35 is unsupported since CUDA 12.0; let PyTorch/NVCC choose defaults or use env var

## Patterns to Follow

### Pattern 1: Metadata in TOML, Logic in Python
**What:** All static package metadata (name, version, deps, classifiers) in pyproject.toml. Only dynamic build logic (extension compilation) in setup.py.
**When:** Always, for any PyTorch extension package.
**Why:** Single source of truth for metadata. setup.py is an implementation detail of the build, not a package description.

### Pattern 2: Environment Variable Override for CUDA
**What:** Preserve FORCE_CUDA, FORCE_CPU, NVCC_FLAGS, BUILD_DOCS environment variables.
**When:** During CI builds, cross-compilation, or documentation generation.
**Why:** Users and CI systems depend on these. They are the standard PyTorch extension convention.

### Pattern 3: Graceful Extension Fallback
**What:** If C++/CUDA extensions fail to compile or load, fall back to pure-PyTorch implementations.
**When:** CPU-only installs, missing CUDA toolkit, incompatible compiler.
**Why:** The library already has `butterfly_multiply_torch()` as a pure-Python fallback. This should be formalized so installation never fails -- only native acceleration is optional.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Metadata in setup.py
**What:** Putting name, version, author, dependencies in setup.py when pyproject.toml exists.
**Why bad:** Duplicated metadata, two sources of truth, confuses tooling.
**Instead:** All metadata in pyproject.toml. setup.py contains only `ext_modules` and `cmdclass`.

### Anti-Pattern 2: Hardcoded CUDA Architecture
**What:** `-arch=sm_35` hardcoded in setup.py.
**Why bad:** sm_35 (Kepler) support was removed in CUDA 12.0. Modern PyTorch 2.x ships with CUDA 11.8+ or 12.x. Hardcoding an unsupported arch causes compilation failures.
**Instead:** Either omit `-arch` entirely (let PyTorch's BuildExtension and NVCC choose defaults based on detected GPU), or set a reasonable minimum like sm_50 (Maxwell) for CUDA 11.x or sm_70 (Volta) for CUDA 12.x. Allow override via NVCC_FLAGS env var.

### Anti-Pattern 3: Importing torch at Module Top Level in setup.py Without Build Declaration
**What:** `import torch` in setup.py without declaring torch in `[build-system].requires`.
**Why bad:** Breaks PEP 517 build isolation. `pip install` fails because torch is not available in the isolated build environment.
**Instead:** Declare torch in `[build-system].requires` so it is installed before setup.py runs.

## Migration Order (What to Change First)

The migration should proceed in this order to maintain a working build at each step:

### Step 1: Add pyproject.toml with build-system table
Create pyproject.toml with `[build-system]` and `[project]` tables. Keep setup.py unchanged. At this point both `pip install .` and `python setup.py install` work. This is the lowest-risk change.

### Step 2: Move metadata from setup.py to pyproject.toml
Remove name, version, author, url, description, keywords, license, python_requires, install_requires from setup.py. These now live in pyproject.toml `[project]`. setup.py retains only `ext_modules` and `cmdclass`.

### Step 3: Update CUDA architecture flags
Remove hardcoded `-arch=sm_35`. Either omit arch flags (recommended) or set a modern minimum. Test compilation on available hardware.

### Step 4: Update Python and PyTorch version constraints
Set `requires-python = ">=3.10"` and `dependencies = ["torch>=2.0"]` in pyproject.toml.

### Step 5: Clean up package discovery
Replace `packages=['torch_butterfly']` with `[tool.setuptools.packages.find]` in pyproject.toml with `include = ["torch_butterfly*"]`. This ensures subpackages are found automatically.

### Step 6: Test the full build matrix
- `uv pip install .` (with build isolation)
- `uv pip install -e .` (editable install)
- `uv pip install --no-build-isolation .` (using local torch)
- `FORCE_CUDA=1 uv pip install .`
- `FORCE_CPU=1 uv pip install .`

## Key Decision: no_python_abi_suffix

The current setup.py uses `BuildExtension.with_options(no_python_abi_suffix=True)`. This option removes the Python ABI tag from compiled extension filenames (e.g., `_butterfly.so` instead of `_butterfly.cpython-310-x86_64-linux-gnu.so`). This was historically needed because `torch.ops.load_library()` in `__init__.py` looks for a module by a simple name.

**Recommendation:** Test whether modern PyTorch's `load_library` / `importlib.machinery.PathFinder` handles ABI-tagged filenames. If it does, remove `no_python_abi_suffix=True` to follow standard Python extension conventions. If not, keep it.

## Key Decision: Editable Installs

For development workflow, `uv pip install -e .` is critical. With setuptools as backend, editable installs of packages with C extensions require that the extension is built in-place. The `--no-build-isolation` flag is often paired with `-e` for faster iteration:

```bash
uv pip install -e . --no-build-isolation
```

This uses the already-installed torch (no re-download) and links the source tree directly.

## Sources

- [pytorch/extension-cpp](https://github.com/pytorch/extension-cpp) -- Official PyTorch C++ extension example (HIGH confidence)
- [torch.utils.cpp_extension docs](https://docs.pytorch.org/docs/stable/cpp_extension.html) -- BuildExtension, CppExtension, CUDAExtension API (HIGH confidence)
- [Python Packaging: Writing pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) -- PEP 621 metadata standard (HIGH confidence)
- [pytorch_scatter issue #265](https://github.com/rusty1s/pytorch_scatter/issues/265) -- torch import in setup.py problem (MEDIUM confidence)
- [pytorch_scatter issue #455](https://github.com/rusty1s/pytorch_scatter/issues/455) -- torch as build-time dependency (MEDIUM confidence)
- [uv: Configuring projects](https://docs.astral.sh/uv/concepts/projects/config/) -- no-build-isolation-package config (HIGH confidence)
- [uv: Using uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/) -- PyTorch + uv integration guide (HIGH confidence)
- [Solving flash-attn issues with uv tools](https://sigridjin.medium.com/solving-flash-attn-issues-with-uv-tools-f3c8fafec0a4) -- flash-attn build strategy (MEDIUM confidence)
- [CUDA arch reference](https://arnon.dk/matching-sm-architectures-arch-and-gencode-for-various-nvidia-cards/) -- sm_35 removal in CUDA 12.0 (HIGH confidence)

---

*Architecture analysis: 2026-04-02*
