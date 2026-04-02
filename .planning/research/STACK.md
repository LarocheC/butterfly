# Technology Stack

**Project:** torch_butterfly build system modernization
**Researched:** 2026-04-02
**Overall confidence:** HIGH

## Recommended Stack

### Build System

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| setuptools | >=64 | Build backend | Industry standard for PyTorch C++/CUDA extensions. Every major PyTorch extension library (flash-attention, xformers, pytorch_scatter, PyG libs) uses setuptools. Not scikit-build-core, not meson, not hatch -- setuptools. The reason: `torch.utils.cpp_extension` provides `CppExtension`, `CUDAExtension`, and `BuildExtension` that are setuptools-native. Fighting this is pointless. | HIGH |
| setuptools.build_meta | - | PEP 517 build backend | The `build-backend` value in pyproject.toml. This is what makes `pip install .` and `uv pip install .` work with pyproject.toml. | HIGH |
| ninja | >=1.10 | Parallel C++ compilation | PyTorch's `BuildExtension` uses ninja automatically when available. Include in build-system.requires for guaranteed availability. Dramatically speeds up multi-file CUDA compilation. | HIGH |
| wheel | >=0.37 | Wheel building | Required for bdist_wheel. flash-attention had a bug (issue #1761) because they forgot to include it. Include it. | HIGH |

### Python & PyTorch

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | >=3.10, <4 | Runtime | Project requirement. 3.10 is minimum for modern typing features and is well within support window. | HIGH |
| PyTorch | >=2.0 | Core dependency + build dependency | Project requirement. Needed at build time for `torch.utils.cpp_extension`. NOT listed in build-system.requires (see Build Strategy below). | HIGH |

### CUDA Architecture Targets

| Architecture | Compute Capability | GPUs | Status |
|-------------|-------------------|------|--------|
| ~~sm_35~~ | ~~3.5~~ | ~~K40, K80~~ | **REMOVE** -- Kepler. Dropped by PyTorch 2.x and CUDA 12.x. Current setup.py hardcodes this. |
| sm_50 | 5.0 | GTX 9xx, Quadro M | Optional. Maxwell. Dropped from CUDA 12.8+ PyTorch builds but still compilable. |
| sm_70 | 7.0 | V100 | Include. Still widely used in cloud. |
| sm_75 | 7.5 | T4, RTX 20xx | Include. Minimum for current PyTorch 2.x binaries. |
| sm_80 | 8.0 | A100, A30 | Include. Primary data center GPU. |
| sm_86 | 8.6 | RTX 30xx, A40 | Include. Common consumer/workstation. |
| sm_89 | 8.9 | RTX 40xx, L40 | Include. Current gen consumer. |
| sm_90 | 9.0 | H100, H200 | Include. Current gen data center. Requires CUDA >= 11.8. |

**Recommendation:** Default to `sm_70;sm_75;sm_80;sm_86;sm_89;sm_90` with `TORCH_CUDA_ARCH_LIST` env var override. Drop sm_35 entirely. Let users opt into older architectures via env var if needed.

### Dev/Test Dependencies

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| pytest | >=7.0 | Testing | Standard. Already used in the project. |
| pytest-cov | >=4.0 | Coverage | Nice to have for CI. |

## The Build Strategy: Hybrid pyproject.toml + setup.py

This is the critical architectural decision. There are two viable patterns in the ecosystem:

### Pattern A: torch in build-system.requires (pytorch_scatter approach)

```toml
[build-system]
requires = ["setuptools>=64", "wheel", "ninja", "torch>=2.0"]
build-backend = "setuptools.build_meta"
```

**Pros:** Clean `pip install .` / `uv pip install .` just works. Build isolation fetches torch automatically.
**Cons:** pip/uv will download a second copy of PyTorch (~2GB) into the isolated build environment. May fetch wrong CUDA variant (CPU-only torch from PyPI by default). Slow. Wasteful.

### Pattern B: torch NOT in build-system.requires (flash-attention approach)

```toml
[build-system]
requires = ["setuptools>=64", "wheel", "ninja"]
build-backend = "setuptools.build_meta"
```

Install with: `pip install --no-build-isolation .` or `uv pip install --no-build-isolation .`

**Pros:** Uses the user's existing PyTorch (correct CUDA version guaranteed). Fast. No duplicate download.
**Cons:** Requires `--no-build-isolation` flag. User must have torch pre-installed. More error-prone for naive users.

### Recommendation: Pattern A (torch in build-system.requires)

**Use Pattern A.** Rationale:

1. **This is a small library.** flash-attention avoids torch-in-requires because their build takes 30+ minutes and needs exact CUDA version matching. torch_butterfly compiles in seconds -- the 2GB torch download overhead is acceptable for correctness.

2. **UV compatibility is a project goal.** Pattern A means `uv pip install .` works out of the box. Pattern B requires the user to know about `--no-build-isolation`, which defeats the "just works" goal.

3. **pytorch_scatter uses this exact pattern.** The project this setup.py was adapted from has already migrated to `[build-system] requires = ["setuptools", "torch"]`. Follow the upstream.

4. **CUDA variant issue is solvable.** For `uv`, users configure PyTorch index in their own pyproject.toml or use `--torch-backend=auto`. For pip, pre-installing torch with CUDA and using `--no-build-isolation` remains an option for power users. Document both paths.

**Confidence:** HIGH -- this is the pattern used by pytorch_scatter (the direct ancestor of this setup.py) and is the simplest path to the project's stated goal.

### Why NOT These Alternatives

| Alternative | Why Not |
|-------------|---------|
| scikit-build-core (CMake) | Overkill. torch_butterfly has 3 source files, not a complex CMake project. torch.utils.cpp_extension handles everything. scikit-build-core is for projects like RAPIDS (cudf, cuml) that have massive CMake builds. |
| meson-python | No integration with torch.utils.cpp_extension. Would require reimplementing all the PyTorch compiler flag detection. |
| hatchling | No ext_modules support at all. Pure Python only. |
| flit | No ext_modules support. Pure Python only. |
| poetry | No native C extension support. Would still need setup.py. |
| Declarative ext-modules in pyproject.toml | Experimental in setuptools as of Oct 2025 (issue #5096). Not stable. Cannot express custom cmdclass (BuildExtension). Still requires setup.py for anything non-trivial. |
| JIT compilation only | Eliminates the build step entirely but requires CUDA toolkit on every user's machine at runtime, not just install time. Slower first-run. Not standard for distributed packages. |

## File Structure

The modernized project needs exactly two build files:

### pyproject.toml (source of truth for metadata)

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
]

[project.urls]
Repository = "https://github.com/hazyresearch/learning-circuits"

[project.optional-dependencies]
dev = ["pytest>=7.0", "pytest-cov>=4.0"]

[tool.setuptools.packages.find]
include = ["torch_butterfly*"]
```

### setup.py (ONLY for ext_modules and cmdclass)

```python
import os
from pathlib import Path
from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CppExtension, CUDAExtension, CUDA_HOME

import torch

WITH_CUDA = torch.cuda.is_available() and CUDA_HOME is not None
if os.getenv("FORCE_CUDA", "0") == "1":
    WITH_CUDA = True
if os.getenv("FORCE_CPU", "0") == "1":
    WITH_CUDA = False

BUILD_DOCS = os.getenv("BUILD_DOCS", "0") == "1"


def get_extensions():
    Extension = CppExtension
    define_macros = []
    extra_compile_args = {"cxx": ["-O3"]}

    if WITH_CUDA:
        Extension = CUDAExtension
        define_macros += [("WITH_CUDA", None)]
        nvcc_flags = os.getenv("NVCC_FLAGS", "")
        nvcc_flags = [] if nvcc_flags == "" else nvcc_flags.split(" ")
        nvcc_flags += ["--expt-extended-lambda", "-lineinfo"]
        # No hardcoded -arch flag. Let TORCH_CUDA_ARCH_LIST or
        # PyTorch defaults handle architecture selection.
        extra_compile_args["nvcc"] = nvcc_flags

    extensions_dir = Path(__file__).absolute().parent / "csrc"
    extensions = []
    for main in extensions_dir.glob("*.cpp"):
        name = main.stem
        sources = [str(main)]
        path = extensions_dir / "cpu" / f"{name}_cpu.cpp"
        if path.exists():
            sources.append(str(path))
        path = extensions_dir / "cuda" / f"{name}_cuda.cu"
        if WITH_CUDA and path.exists():
            sources.append(str(path))
        extension = Extension(
            "torch_butterfly._" + name,
            sources,
            include_dirs=[str(extensions_dir)],
            define_macros=define_macros,
            extra_compile_args=extra_compile_args,
        )
        extensions.append(extension)
    return extensions


setup(
    ext_modules=get_extensions() if not BUILD_DOCS else [],
    cmdclass={
        "build_ext": BuildExtension.with_options(
            no_python_abi_suffix=True, use_ninja=True
        )
    },
)
```

**Key changes from current setup.py:**
1. All metadata moved to pyproject.toml (name, version, author, dependencies, python_requires)
2. setup.py reduced to ONLY ext_modules + cmdclass (the parts that cannot be declarative)
3. Removed hardcoded `-arch=sm_35` -- let PyTorch/TORCH_CUDA_ARCH_LIST handle it
4. Added `-O3` to C++ compiler flags
5. Removed empty install_requires, setup_requires, tests_require (now in pyproject.toml)

## Installation Commands

```bash
# Standard install (downloads torch into build env if needed)
uv pip install .

# Editable install for development
uv pip install -e ".[dev]"

# With pre-installed torch (faster, uses your CUDA version)
uv pip install --no-build-isolation .

# Force CUDA build even without GPU present
FORCE_CUDA=1 uv pip install .

# Force CPU-only build
FORCE_CPU=1 uv pip install .

# Target specific CUDA architectures
TORCH_CUDA_ARCH_LIST="8.0;9.0" uv pip install .
```

## Sources

- [pytorch_scatter pyproject.toml](https://github.com/rusty1s/pytorch_scatter) -- `[build-system] requires = ["setuptools", "torch"]` (direct ancestor of this project's setup.py) -- HIGH confidence
- [flash-attention setup.py](https://github.com/Dao-AILab/flash-attention) -- Complex CUDA build with NinjaBuildExtension, deliberately excludes torch from build-system.requires -- HIGH confidence
- [xformers pyproject.toml](https://github.com/facebookresearch/xformers) -- `[build-system] requires = ["setuptools >= 64", "torch >= 2.10"]` -- HIGH confidence
- [PyTorch torch.utils.cpp_extension docs](https://docs.pytorch.org/docs/stable/cpp_extension.html) -- Official API for CppExtension, CUDAExtension, BuildExtension -- HIGH confidence
- [uv PyTorch integration guide](https://docs.astral.sh/uv/guides/integration/pytorch/) -- Index configuration, --torch-backend=auto -- HIGH confidence
- [setuptools ext-modules experimental status](https://github.com/pypa/setuptools/issues/5096) -- Declarative ext_modules still experimental as of Oct 2025 -- HIGH confidence
- [PyTorch CUDA architecture deprecation](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128) -- sm_35 dropped, sm_75 minimum for current binaries -- MEDIUM confidence
- [setuptools pyproject.toml configuration](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html) -- setuptools >= 64 for full pyproject.toml support -- HIGH confidence
