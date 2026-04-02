# Domain Pitfalls

**Domain:** PyTorch C++/CUDA extension packaging migration (setup.py to pyproject.toml)
**Project:** torch_butterfly build system modernization
**Researched:** 2026-04-02

## Critical Pitfalls

Mistakes that cause broken installs, silent build failures, or require rearchitecting the approach.

### Pitfall 1: Build Isolation Installs Wrong PyTorch Variant

**What goes wrong:** PEP 517 build isolation creates a fresh virtual environment for the build. If `torch` is listed in `[build-system] requires`, pip/uv downloads the default PyTorch wheel from PyPI -- which is the CPU-only variant. Your C++ extensions then compile against CPU-only PyTorch headers, producing binaries incompatible with the user's CUDA-enabled PyTorch.

**Why it happens:** PyTorch distributes CUDA variants through a custom index (`https://download.pytorch.org/whl/cuXXX`), not PyPI. A bare `requires = ["torch"]` in pyproject.toml does not carry index information and pip's isolated build env fetches from PyPI by default.

**Consequences:** Extensions silently compile without CUDA support even when the user has a CUDA-capable PyTorch installed. At runtime, CUDA ops crash or fall back to CPU without clear error messages. The CUDA version mismatch check in `__init__.py` (lines 13-31) would catch some cases but not all.

**Warning signs:**
- `uv pip install .` downloads a 200MB torch wheel during build (should not happen if reusing the user's torch)
- Build log shows no nvcc invocations despite CUDA being available
- `torch.ops.torch_butterfly.cuda_version()` returns -1 after install

**Prevention:** Use `--no-build-isolation` or uv's `no-build-isolation-package` setting. The official PyTorch extension-cpp example README instructs users to run `pip install --no-build-isolation -e .`. For uv, configure in the consuming project's pyproject.toml:
```toml
[tool.uv]
no-build-isolation-package = ["torch_butterfly"]
```

Alternatively, list torch in `[build-system] requires` AND document that users must install from the correct PyTorch index first. The pyproject.toml should still declare torch as a build dependency for metadata correctness -- the no-build-isolation flag just prevents re-downloading it.

**Phase:** Phase 1 (core pyproject.toml creation). This is the first and most fundamental decision.

**Confidence:** HIGH -- verified against PyTorch's own extension-cpp example and uv documentation.

---

### Pitfall 2: `import torch` at setup.py Parse Time Breaks Standard pip Install

**What goes wrong:** The current `setup.py` (line 7) does `import torch` at the module level. Standard `pip install .` (with build isolation) fails immediately with `ModuleNotFoundError: No module named 'torch'` because the isolated build environment does not yet have torch installed when setup.py is first parsed.

**Why it happens:** PEP 517 build isolation installs `[build-system] requires` packages, then runs setup.py. But if setup.py imports torch at the top level, the import happens during initial setup.py loading, which races with the build dependency installation in some tooling.

**Consequences:** Completely broken install for any user who does not already have torch in their environment. This is the exact bug that torch_butterfly has today and the primary motivation for the migration.

**Warning signs:**
- `pip install .` fails with `ModuleNotFoundError: No module named 'torch'`
- Users must `pip install torch` first, then `pip install .` separately

**Prevention:** Keep setup.py alongside pyproject.toml (the official PyTorch pattern), but ensure `[build-system] requires = ["setuptools", "torch"]` is set. With build isolation, pip installs torch into the build env before executing setup.py. Without build isolation, torch must already be in the user's env. Both paths work as long as pyproject.toml declares the build dependency.

The pytorch/extension-cpp example uses exactly this pattern: pyproject.toml with `requires = ["setuptools", "torch"]` plus a setup.py that imports torch.

**Phase:** Phase 1 (core pyproject.toml creation).

**Confidence:** HIGH -- this is the documented pattern from pytorch/extension-cpp and the root cause documented in pytorch_scatter issue #265 and #381.

---

### Pitfall 3: `torch.ops.load_library` with `PathFinder` Breaks Under Modern Editable Installs

**What goes wrong:** The current `__init__.py` (lines 8-11) uses `importlib.machinery.PathFinder().find_spec()` to locate compiled `.so` files by searching the package directory. With modern PEP 660 editable installs (setuptools >= 64), the package may be served through a custom finder/loader rather than being physically present in the source tree. `PathFinder().find_spec()` bypasses this mechanism and returns `None`, causing an `AttributeError: 'NoneType' object has no attribute 'origin'`.

**Why it happens:** Legacy `python setup.py develop` (now deprecated in pip 24.2+) created a `.egg-link` and put the source directory on `sys.path` directly, so `.so` files built in-place were findable. Modern PEP 660 editable installs use import hooks instead, and compiled extensions may be placed in a build directory rather than the source tree.

**Consequences:** `import torch_butterfly` crashes immediately on editable installs. Development workflow is broken.

**Warning signs:**
- `AttributeError: 'NoneType' object has no attribute 'origin'` on import
- `.so` files exist in `build/` but not in `torch_butterfly/`
- Import works after `pip install .` (non-editable) but fails with `pip install -e .`

**Prevention:** Replace the `PathFinder` hack with standard `importlib.resources` or simply use `torch.ops.load_library()` with a path computed relative to `__file__`:
```python
import os
_ext_dir = os.path.dirname(__file__)
for lib_name in ['_version', '_butterfly']:
    # Find .so files in the same directory as __init__.py
    for ext in ['.so', '.pyd', '.dylib']:
        lib_path = os.path.join(_ext_dir, lib_name + ext)
        if os.path.exists(lib_path):
            torch.ops.load_library(lib_path)
            break
```

Or, switch to the modern `torch.library` / custom ops pattern where PyTorch handles library loading automatically. However, that is a larger refactor.

**Phase:** Phase 2 (after pyproject.toml is in place, fix the import machinery).

**Confidence:** MEDIUM -- the PathFinder approach is fragile and known to cause issues, but the exact failure mode depends on which setuptools editable install backend is active. Needs testing.

---

### Pitfall 4: `sm_35` CUDA Architecture is Removed from Modern CUDA Toolkits

**What goes wrong:** The current setup.py hardcodes `-arch=sm_35` (line 29). SM 3.5 (Kepler) was deprecated in CUDA 11 and removed in CUDA 12. PyTorch 2.x ships with CUDA 12.x. Compilation fails with an error like `Unknown CUDA arch sm_35` or `nvcc fatal: Unsupported gpu architecture 'compute_35'`.

**Why it happens:** The code was written for CUDA 10.1 era GPUs. SM 3.5 corresponds to Tesla K40, which is ancient by 2026 standards.

**Consequences:** Build fails entirely on any modern CUDA toolkit. Since PyTorch 2.8+, even Maxwell (sm_50) and Pascal (sm_60) support has been dropped from CUDA 12.8/12.9 builds.

**Warning signs:**
- nvcc error mentioning unsupported architecture
- Build failure only when CUDA is detected (CPU-only builds work fine)

**Prevention:** Do not hardcode a single architecture. Use PyTorch's `TORCH_CUDA_ARCH_LIST` environment variable or auto-detect from `torch.cuda.get_arch_list()`. Reasonable default for PyTorch 2.x with CUDA 12:
```python
nvcc_flags += ['-arch=sm_70']  # Volta minimum, safe for 2024+ GPUs
```
Or better, use `torch.utils.cpp_extension`'s built-in architecture detection by not specifying `-arch` at all -- `CUDAExtension` sets appropriate defaults based on the installed CUDA toolkit and PyTorch build.

**Phase:** Phase 1 (fix during initial pyproject.toml creation, as it blocks any CUDA build).

**Confidence:** HIGH -- sm_35 removal from CUDA 12 is documented by NVIDIA, and PyTorch 2.8+ release notes confirm Maxwell/Pascal removal.

---

### Pitfall 5: `version.cpp` Uses Deprecated `torch::RegisterOperators` API

**What goes wrong:** `csrc/version.cpp` (line 22-23) uses `torch::RegisterOperators().op(...)` which is the legacy operator registration API. While it still compiles in PyTorch 2.x, it may be removed in future versions and does not integrate with `torch.compile` or the modern dispatcher.

**Why it happens:** The code predates the `TORCH_LIBRARY` macro (which `butterfly.cpp` already uses correctly). The two files use inconsistent registration patterns.

**Consequences:** Not an immediate build failure, but:
- Deprecation warnings during compilation
- The `cuda_version` op may not be visible to `torch.compile` or `torch.export`
- Future PyTorch version could remove the API entirely, breaking the build

**Warning signs:**
- Compiler warnings about deprecated API usage
- `torch.ops.torch_butterfly.cuda_version` not found in some contexts

**Prevention:** Migrate `version.cpp` to use `TORCH_LIBRARY` like `butterfly.cpp` already does:
```cpp
TORCH_LIBRARY(torch_butterfly, m) {
    m.def("cuda_version", cuda_version);
}
```
Note: this changes the registration from a static global to the `TORCH_LIBRARY` block. If `butterfly.cpp` already declares `TORCH_LIBRARY(torch_butterfly, m)`, you need to use `TORCH_LIBRARY_FRAGMENT` in `version.cpp` instead (only one `TORCH_LIBRARY` per namespace per shared library, but since these compile to separate `.so` files, each can have its own `TORCH_LIBRARY`).

**Phase:** Phase 1 or 2 (low effort, high value).

**Confidence:** MEDIUM -- `RegisterOperators` still works in PyTorch 2.11 but is documented as legacy. The `TORCH_LIBRARY` macro is the recommended replacement.

## Moderate Pitfalls

### Pitfall 6: `no_python_abi_suffix=True` Causes Extension Discovery Issues

**What goes wrong:** The current setup.py uses `BuildExtension.with_options(no_python_abi_suffix=True)`, which strips the CPython ABI tag from the `.so` filename (producing `_butterfly.so` instead of `_butterfly.cpython-310-x86_64-linux-gnu.so`). This was needed because `torch.ops.load_library()` loads by filename, not by Python import. But modern setuptools editable installs and wheel packaging expect the ABI-tagged filename.

**Prevention:** Since the extensions are loaded via `torch.ops.load_library()` (not `import _butterfly`), the `no_python_abi_suffix=True` is correct for the load_library path. However, if switching to a standard import-based loading mechanism, remove this option. Test both `pip install .` and `pip install -e .` to verify the `.so` files are discoverable. The PyTorch extension-cpp example no longer uses this option.

**Phase:** Phase 2 (when reworking the `__init__.py` import mechanism).

**Confidence:** MEDIUM.

---

### Pitfall 7: Editable Install Requires Rebuild After C++ Changes

**What goes wrong:** Developers modify `.cpp` or `.cu` files and expect the next `import torch_butterfly` to pick up changes. It does not. C++ extensions must be explicitly recompiled.

**Why it happens:** Editable installs only make Python source changes live. Compiled extensions are binary artifacts that require a build step.

**Prevention:** Document the development workflow clearly. After C++ changes:
```bash
uv pip install --no-build-isolation -e .
```
Or use a Makefile/task runner that wraps `python setup.py build_ext --inplace` (if setup.py is retained) for faster iteration. Consider JIT compilation via `torch.utils.cpp_extension.load()` for development, but keep the setuptools path for installation.

**Phase:** Phase 3 (developer experience / documentation).

**Confidence:** HIGH -- this is inherent to compiled extensions regardless of build system.

---

### Pitfall 8: UV Two-Phase Install Friction

**What goes wrong:** When using `uv sync` (not just `uv pip install`), the two-phase install for no-build-isolation packages creates friction. UV first resolves and installs all normal packages, then installs no-build-isolation packages. If torch is only in `[build-system] requires` and not in project dependencies, the first phase may not install it, causing the second phase to fail.

**Why it happens:** UV's `no-build-isolation-package` expects the build dependencies to be available in the project environment. If torch is not also a project dependency (just a build dependency), it may not be installed before the no-build-isolation build runs.

**Prevention:** Declare torch as BOTH a build dependency and a project dependency:
```toml
[build-system]
requires = ["setuptools", "torch"]

[project]
dependencies = ["torch>=2.0"]
```

Also configure the PyTorch index for uv:
```toml
[[tool.uv.index]]
name = "pytorch-cu124"
url = "https://download.pytorch.org/whl/cu124"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch-cu124" }
```

Or use `--torch-backend=auto` if available in the uv version.

**Phase:** Phase 1 (pyproject.toml creation must get this right from the start).

**Confidence:** MEDIUM -- uv's PyTorch integration is evolving. The `--torch-backend=auto` feature and `tool.uv.sources` pattern are relatively new. Verify against current uv docs at build time.

## Minor Pitfalls

### Pitfall 9: Missing `csrc/` Files in sdist/wheel

**What goes wrong:** pyproject.toml-based builds use `setuptools` file discovery, which may not include the `csrc/` directory in source distributions. The installed package then has no C++ sources and the build silently produces no extensions.

**Prevention:** Ensure `csrc/` is included. With setuptools, either:
- Use a `MANIFEST.in` with `recursive-include csrc *`
- Or configure in pyproject.toml:
```toml
[tool.setuptools.packages.find]
include = ["torch_butterfly*"]

[tool.setuptools.package-data]
torch_butterfly = ["*.so", "*.pyd"]
```

The `csrc/` directory is at the repo root (not inside `torch_butterfly/`), so setuptools `find_packages()` will NOT discover it. The setup.py `get_extensions()` function reads from `csrc/` using `Path(__file__).parent / 'csrc'`, which works at build time but the sources must be present in the sdist.

**Phase:** Phase 1.

**Confidence:** HIGH.

---

### Pitfall 10: `setuptools>=77` License Field Format Change

**What goes wrong:** setuptools 77+ changed the `license` field format. The old string-based `license='Apache'` in setup.py works, but when migrating to pyproject.toml's `[project]` table, using the deprecated table format `license = {text = "Apache-2.0"}` will become an error.

**Prevention:** Use the SPDX identifier format in pyproject.toml:
```toml
[project]
license = "Apache-2.0"
```

**Phase:** Phase 1.

**Confidence:** HIGH -- documented in setuptools changelog.

---

### Pitfall 11: `use_ninja=True` May Fail in Minimal Build Environments

**What goes wrong:** The current setup.py passes `use_ninja=True` to `BuildExtension`. If ninja is not installed in the build environment, the build fails with a confusing error about ninja not being found.

**Prevention:** Either add `ninja` to `[build-system] requires`:
```toml
[build-system]
requires = ["setuptools", "torch", "ninja"]
```
Or remove the explicit `use_ninja=True` -- modern PyTorch's `BuildExtension` already defaults to using ninja when available and falling back to make when not.

**Phase:** Phase 1.

**Confidence:** HIGH.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 1: pyproject.toml creation | Build isolation installs wrong PyTorch (#1) | Use no-build-isolation pattern from the start |
| Phase 1: pyproject.toml creation | sm_35 blocks CUDA build (#4) | Remove hardcoded arch, use torch defaults |
| Phase 1: pyproject.toml creation | csrc/ missing from sdist (#9) | Add MANIFEST.in or package-data config |
| Phase 1: pyproject.toml creation | UV two-phase install (#8) | Declare torch as both build and project dep |
| Phase 2: Import mechanism | PathFinder breaks editable install (#3) | Replace with __file__-relative path resolution |
| Phase 2: Import mechanism | no_python_abi_suffix discovery (#6) | Test both install modes, align with loading strategy |
| Phase 2: Import mechanism | RegisterOperators deprecated (#5) | Migrate version.cpp to TORCH_LIBRARY |
| Phase 3: DX polish | C++ rebuild workflow (#7) | Document rebuild step, consider JIT for dev |

## Summary: The Three Decisions That Determine Success or Failure

1. **Build isolation strategy** (Pitfall #1, #2, #8): The single most consequential decision. Choose `--no-build-isolation` with torch as both build and project dependency. Document this for consumers.

2. **Extension loading mechanism** (Pitfall #3, #6): The `PathFinder` + `no_python_abi_suffix` combo is fragile. Replace with `__file__`-relative loading or standard Python imports.

3. **CUDA architecture defaults** (Pitfall #4): Hard failure if not addressed. Remove sm_35, let PyTorch/CUDA toolkit determine defaults.

## Sources

- [PyTorch extension-cpp official example](https://github.com/pytorch/extension-cpp) -- HIGH confidence
- [pytorch_scatter issue #265: import torch in setup.py](https://github.com/rusty1s/pytorch_scatter/issues/265) -- HIGH confidence
- [pytorch_scatter issue #381: Removing import torch from setup.py](https://github.com/rusty1s/pytorch_scatter/issues/381) -- HIGH confidence
- [uv docs: Using uv with PyTorch](https://docs.astral.sh/uv/guides/integration/pytorch/) -- HIGH confidence
- [uv docs: Configuring projects (no-build-isolation-package)](https://docs.astral.sh/uv/concepts/projects/config/) -- HIGH confidence
- [PyTorch CUDA architecture support changes](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128) -- HIGH confidence
- [torch.utils.cpp_extension docs](https://docs.pytorch.org/docs/stable/cpp_extension.html) -- HIGH confidence
- [PEP 660: Editable installs for pyproject.toml](https://peps.python.org/pep-0660/) -- HIGH confidence
- [uv issue #10694: Two-stage uv sync for pytorch projects](https://github.com/astral-sh/uv/issues/10694) -- MEDIUM confidence
- [setuptools extension modules docs](https://setuptools.pypa.io/en/latest/userguide/ext_modules.html) -- HIGH confidence
- [Installing C++ extensions in pip's sandbox](https://discuss.pytorch.org/t/installing-c-extensions-in-pips-sandbox/164847) -- MEDIUM confidence
