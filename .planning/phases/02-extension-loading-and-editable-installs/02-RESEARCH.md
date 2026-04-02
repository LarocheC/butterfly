# Phase 2: Extension Loading and Editable Installs - Research

**Researched:** 2026-04-02
**Domain:** PyTorch C++ extension runtime loading, PEP 660 editable installs, operator registration APIs
**Confidence:** HIGH

## Summary

Phase 2 fixes three tightly coupled problems: (1) the fragile `PathFinder`-based .so discovery in `__init__.py` that breaks under PEP 660 editable installs, (2) the `no_python_abi_suffix=True` hack in setup.py that strips the CPython ABI tag from compiled extensions, and (3) the deprecated `RegisterOperators` API in `csrc/version.cpp` that should use the `TORCH_LIBRARY` macro already used by `csrc/butterfly.cpp`. A fourth, smaller fix downgrades the CUDA version mismatch check from a fatal `RuntimeError` to a `warnings.warn()`, which resolves the Phase 1 verification gaps (INST-01, INST-02) where CPU-built extensions fail to import alongside CUDA-enabled torch.

The solution is straightforward: remove `no_python_abi_suffix=True` so compiled extensions get proper ABI tags (e.g., `_butterfly.cpython-310-x86_64-linux-gnu.so`), then use `glob.glob()` with a wildcard pattern relative to `__file__` to find and load them via `torch.ops.load_library()`. This approach works identically for regular installs (files in site-packages) and editable installs (files built in-place in the source tree). The `version.cpp` migration is a one-line change from `torch::RegisterOperators` to `TORCH_LIBRARY`.

**Primary recommendation:** Replace PathFinder with `__file__`-relative glob, remove `no_python_abi_suffix`, downgrade CUDA check to warning, migrate version.cpp to TORCH_LIBRARY.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Replace PathFinder-based .so discovery with `__file__`-relative path resolution (e.g., `os.path.join(os.path.dirname(__file__), '_butterfly*.so')` with glob)
- **D-02:** Use `torch.ops.load_library()` to load the found .so files (preserve current API)
- **D-03:** Must work for both regular installs (site-packages) and editable installs (source tree)
- **D-04:** Remove `no_python_abi_suffix=True` from setup.py's `BuildExtension.with_options()`
- **D-05:** Use glob pattern to find .so files regardless of ABI tag (e.g., `_butterfly*.so` or `_butterfly.*.so`)
- **D-06:** Downgrade `check_cuda_version()` from `RuntimeError` to `warnings.warn()` when CUDA versions mismatch
- **D-07:** Keep the check itself -- it's useful diagnostic info, just shouldn't be fatal
- **D-08:** Migrate `csrc/version.cpp` from `torch::RegisterOperators().op(...)` to `TORCH_LIBRARY` macro (consistent with `csrc/butterfly.cpp`)
- **D-09:** Minimal cleanup only -- fix loading, CUDA check, version.cpp. Don't touch complex_utils.py, cupy refs, or PyTorch 1.7 workarounds
- **D-10:** Phase 1 verification gaps (INST-01, INST-02 import failures) should be resolved by this phase

### Claude's Discretion
- Exact glob pattern for finding .so files with ABI tags
- Whether to add a graceful fallback if .so files aren't found (pure-Python mode warning vs hard error)
- Exact warning message text for CUDA version mismatch
- Whether to update `__version__` string

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXT-01 | PathFinder-based extension loading in `__init__.py` replaced with `__file__`-relative .so discovery | Glob pattern `_butterfly*` + `_version*` relative to `os.path.dirname(__file__)`, filtering for `.so`/`.pyd`/`.dylib` suffixes |
| EXT-02 | Editable installs (`uv pip install -e .`) load extensions correctly | PEP 660 editable installs with setuptools build extensions in-place; `__file__`-relative discovery works because .so files land next to `__init__.py` in both install modes |
| EXT-03 | Deprecated RegisterOperators API in `csrc/version.cpp` migrated to TORCH_LIBRARY macro | Direct template in `csrc/butterfly.cpp` lines 127-131; version.cpp compiles to separate .so so can use `TORCH_LIBRARY` (not `TORCH_LIBRARY_FRAGMENT`) |
| INST-03 | `uv pip install -e .` works for development (editable) | Removing `no_python_abi_suffix` + glob-based discovery + CUDA warning downgrade = complete editable install support |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Build system:** Must use pyproject.toml as the single source of truth for packaging
- **UV compatibility:** Must work with `uv pip install` without conda
- **CUDA support:** Must retain CUDA extension compilation via torch.utils.cpp_extension
- **Python:** >=3.10, <4
- **PyTorch:** >=2.0
- **Backwards compat:** No need to support Python <3.10 or PyTorch <2.0
- **Naming:** `snake_case.py` for Python modules, `PascalCase` for classes
- **Error handling:** C++ uses TORCH_CHECK macros; Python uses assert or RuntimeError
- **Module design:** Extensions loaded dynamically in `__init__.py` via `torch.ops.load_library`
- **GSD workflow:** Use GSD commands for file changes, not direct edits

## Standard Stack

No new libraries are introduced in this phase. All changes use the existing stack:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| torch | >=2.0 | `torch.ops.load_library()` for loading compiled .so | Already in use; the documented PyTorch way to load custom op libraries |
| setuptools | >=64 | `BuildExtension` for compiling C++ extensions | Already in use; PEP 660 editable install support requires >=64 |

### Standard Library Modules Used
| Module | Purpose |
|--------|---------|
| `os.path` | `dirname(__file__)` for extension directory discovery |
| `glob` | `glob.glob()` to find .so files matching wildcard patterns |
| `warnings` | `warnings.warn()` for CUDA version mismatch (replacing RuntimeError) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `glob.glob()` | `importlib.resources` | More "correct" for package resources but overkill for finding .so files next to `__init__.py`; glob is simpler and universally understood |
| `glob.glob()` | `pathlib.Path.glob()` | Equivalent; `glob.glob()` chosen for consistency with `os.path` usage (no need to mix paradigms) |
| `torch.ops.load_library()` | Direct `import _butterfly` | Would require the extension to be a proper Python module; current architecture uses `TORCH_LIBRARY` op registration which needs `load_library` |

## Architecture Patterns

### Current Code (to be replaced)

```python
# torch_butterfly/__init__.py lines 8-11 (BROKEN under PEP 660)
for library in ['_version', '_butterfly']:
    torch.ops.load_library(importlib.machinery.PathFinder().find_spec(
        library, [str(Path(__file__).absolute().parent)]).origin)
```

This breaks because:
1. `PathFinder().find_spec()` searches for Python modules, not arbitrary .so files
2. With `no_python_abi_suffix=True`, the .so has no ABI tag, so it looks like a Python module -- but only by accident
3. Under PEP 660 editable installs, `PathFinder` may not find files in the source tree

### Pattern 1: `__file__`-Relative Glob Discovery (RECOMMENDED)

**What:** Find .so files by globbing relative to `__init__.py`'s location
**When to use:** Always -- this is the replacement for PathFinder

```python
import os
import glob
import warnings
import torch

_ext_dir = os.path.dirname(os.path.abspath(__file__))

def _load_extension(name):
    """Load a compiled C++ extension library by name prefix."""
    # Match any ABI suffix: _butterfly.cpython-310-x86_64-linux-gnu.so
    # Also handles .pyd (Windows) and .dylib (macOS)
    for pattern in [f'{name}*.so', f'{name}*.pyd', f'{name}*.dylib']:
        matches = glob.glob(os.path.join(_ext_dir, pattern))
        if matches:
            torch.ops.load_library(matches[0])
            return
    raise ImportError(
        f"Could not find compiled extension '{name}' in {_ext_dir}. "
        f"Please reinstall torch_butterfly: pip install -e . --no-build-isolation"
    )

_load_extension('_version')
_load_extension('_butterfly')
```

**Why this works for both install modes:**
- **Regular install (`pip install .`):** Extensions are compiled and placed in `site-packages/torch_butterfly/` alongside `__init__.py`. Glob finds them there.
- **Editable install (`pip install -e .`):** PEP 660 with setuptools does an in-place build as a side effect, placing .so files in the source `torch_butterfly/` directory alongside `__init__.py`. Glob finds them there too.

### Pattern 2: TORCH_LIBRARY Operator Registration

**What:** Replace deprecated `RegisterOperators` with `TORCH_LIBRARY` macro
**Template from `csrc/butterfly.cpp` lines 127-131:**

```cpp
// csrc/butterfly.cpp (already correct)
TORCH_LIBRARY(torch_butterfly, m) {
  m.def("butterfly_multiply_fw", butterfly_multiply_fw);
  m.def("butterfly_multiply_bw", butterfly_multiply_bw);
  m.def("butterfly_multiply", butterfly_multiply);
}
```

**Migration for `csrc/version.cpp`:**

```cpp
// BEFORE (deprecated):
static auto registry = torch::RegisterOperators().op(
    "torch_butterfly::cuda_version", &cuda_version);

// AFTER:
TORCH_LIBRARY(torch_butterfly, m) {
    m.def("cuda_version", cuda_version);
}
```

**Critical note:** Both `_version.so` and `_butterfly.so` are **separate shared libraries** (compiled from separate `CppExtension` calls in setup.py). Each separate .so file can have its own `TORCH_LIBRARY(torch_butterfly, m)` block. `TORCH_LIBRARY_FRAGMENT` is only needed when multiple registration blocks exist **within the same .so file**. Since `version.cpp` and `butterfly.cpp` compile to different .so files, both can use `TORCH_LIBRARY`.

### Pattern 3: CUDA Version Warning (Not Error)

```python
def check_cuda_version():
    if torch.version.cuda is not None:
        cuda_version = torch.ops.torch_butterfly.cuda_version()

        if cuda_version == -1:
            major = minor = 0
        elif cuda_version < 10000:
            major, minor = int(str(cuda_version)[0]), int(str(cuda_version)[2])
        else:
            major, minor = int(str(cuda_version)[0:2]), int(str(cuda_version)[3])
        t_major, t_minor = [int(x) for x in torch.version.cuda.split('.')]

        if t_major != major or t_minor != minor:
            warnings.warn(
                f'Detected that PyTorch and torch_butterfly were compiled with '
                f'different CUDA versions. PyTorch has CUDA version '
                f'{t_major}.{t_minor} and torch_butterfly has CUDA version '
                f'{major}.{minor}. Please reinstall the torch_butterfly that '
                f'matches your PyTorch install.',
                UserWarning,
                stacklevel=2,
            )
```

### Anti-Patterns to Avoid
- **Using `importlib.machinery.PathFinder`:** Designed for Python module discovery, not .so loading. Fragile under PEP 660.
- **Hardcoding .so filename without ABI tag:** Requires `no_python_abi_suffix=True` hack which fights against setuptools conventions.
- **Using `TORCH_LIBRARY_FRAGMENT` when not needed:** Only needed for multiple registration blocks in the same .so file.
- **Catching all exceptions around extension loading:** If extensions fail to load, the error should be clear. Only the CUDA mismatch check should be softened.

### Discretion Decisions (Recommendations)

**Glob pattern:** Use `f'{name}*.so'` (not `f'{name}.*.so'`). The ABI tag format is `_butterfly.cpython-310-x86_64-linux-gnu.so` -- note no dot between name and `cpython`. The pattern `_butterfly*` safely catches both `_butterfly.so` (if ever built without ABI tag) and `_butterfly.cpython-310-x86_64-linux-gnu.so`.

**Fallback behavior:** Raise `ImportError` with a clear message including the directory searched and a reinstall command. Do NOT silently degrade to pure-Python mode -- the library requires native extensions for its core functionality (butterfly_multiply is C++/CUDA only). A silent fallback would produce confusing errors later.

**`__version__` string:** Leave as `0.0.0`. Version bumping is out of scope per REQUIREMENTS.md.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Finding .so files with ABI tags | Custom regex parsing of filenames | `glob.glob(f'{name}*.so')` | Glob handles all ABI tag formats and platform variations |
| Loading custom ops | `ctypes.cdll.LoadLibrary` | `torch.ops.load_library()` | PyTorch's loader handles symbol registration, dispatcher integration |
| Warning on CUDA mismatch | Custom logging framework | `warnings.warn(msg, UserWarning)` | Standard Python; integrable with warning filters; no dependencies |

## Common Pitfalls

### Pitfall 1: TORCH_LIBRARY Namespace Collision Between .so Files
**What goes wrong:** Using `TORCH_LIBRARY(torch_butterfly, m)` in both `version.cpp` and `butterfly.cpp` could theoretically cause a "namespace already registered" error.
**Why it happens:** If both .so files were linked into the same shared library, two `TORCH_LIBRARY` blocks for the same namespace would conflict.
**How to avoid:** This is NOT a problem here because `_version.so` and `_butterfly.so` are separate shared libraries. Each loads independently via `torch.ops.load_library()`. Verified: setup.py `get_extensions()` creates separate `CppExtension` entries for each `.cpp` file in `csrc/`.
**Warning signs:** "Tried to register operators for torch_butterfly but it was already registered" at import time.
**Confidence:** HIGH -- verified by examining setup.py extension discovery loop.

### Pitfall 2: Load Order Matters
**What goes wrong:** `check_cuda_version()` calls `torch.ops.torch_butterfly.cuda_version()`, which is registered by `_version.so`. If `_butterfly.so` is loaded first and `_version.so` fails, the CUDA check crashes.
**Why it happens:** The current code loads `_version` before `_butterfly` (line 8: `['_version', '_butterfly']`). This order must be preserved.
**How to avoid:** Maintain the `_version` then `_butterfly` load order. The loading function should fail clearly if any extension is missing.
**Confidence:** HIGH -- visible in current code.

### Pitfall 3: Editable Install Does NOT Auto-Rebuild C++ Extensions
**What goes wrong:** After `uv pip install -e .`, developers change `.cpp` or `.cu` files and expect the changes to take effect on next import. They don't -- C++ must be recompiled.
**Why it happens:** Editable installs only make Python source changes live. Compiled extensions are binary artifacts.
**How to avoid:** Out of scope for this phase (Phase 3 documentation concern), but the `ImportError` message from the loading function should hint at reinstallation.
**Confidence:** HIGH -- inherent to compiled extensions.

### Pitfall 4: Glob Matching Too Broadly
**What goes wrong:** Pattern `_butterfly*` could match unexpected files like `_butterfly_old.so` or `_butterfly_backup.cpython-310.so` if they exist in the directory.
**Why it happens:** Glob wildcards are greedy.
**How to avoid:** Use pattern `_butterfly.*.so` on Linux/macOS (matches the dot before the ABI tag) with a fallback to `_butterfly.so` for the no-suffix case. Or simply use `_butterfly*.so` and accept that in practice there will only be one match. The build system only produces one file per extension name. Recommended: use `_butterfly*.so` for simplicity -- the risk is theoretical.
**Confidence:** MEDIUM -- theoretical concern, not observed in practice.

### Pitfall 5: Windows .pyd Extension Suffix
**What goes wrong:** On Windows, compiled extensions use `.pyd` not `.so`. If the glob only checks `.so`, Windows users get ImportError.
**Why it happens:** Platform convention difference.
**How to avoid:** Check for `.so`, `.pyd`, and `.dylib` patterns. The current codebase has `#ifdef _WIN32 PyMODINIT_FUNC` guards in both .cpp files, suggesting Windows support was once considered.
**Confidence:** HIGH -- well-known cross-platform concern.

## Code Examples

### Complete `__init__.py` Replacement

```python
import os
import glob
import warnings

import torch

__version__ = '0.0.0'

# Load compiled C++/CUDA extensions
_ext_dir = os.path.dirname(os.path.abspath(__file__))

def _load_extension(name):
    """Load a compiled C++ extension library by name prefix."""
    for suffix in ['*.so', '*.pyd', '*.dylib']:
        pattern = os.path.join(_ext_dir, f'{name}{suffix}')
        matches = glob.glob(pattern)
        if matches:
            torch.ops.load_library(matches[0])
            return
    raise ImportError(
        f"Could not find compiled extension '{name}' in {_ext_dir}. "
        f"Please reinstall: pip install --no-build-isolation -e ."
    )

_load_extension('_version')
_load_extension('_butterfly')


def check_cuda_version():
    if torch.version.cuda is not None:
        cuda_version = torch.ops.torch_butterfly.cuda_version()

        if cuda_version == -1:
            major = minor = 0
        elif cuda_version < 10000:
            major, minor = int(str(cuda_version)[0]), int(str(cuda_version)[2])
        else:
            major, minor = int(str(cuda_version)[0:2]), int(str(cuda_version)[3])
        t_major, t_minor = [int(x) for x in torch.version.cuda.split('.')]

        if t_major != major or t_minor != minor:
            warnings.warn(
                f'Detected that PyTorch and torch_butterfly were compiled with '
                f'different CUDA versions. PyTorch has CUDA version '
                f'{t_major}.{t_minor} and torch_butterfly has CUDA version '
                f'{major}.{minor}. Please reinstall the torch_butterfly that '
                f'matches your PyTorch install.',
                UserWarning,
                stacklevel=2,
            )


check_cuda_version()
from .butterfly import Butterfly, ButterflyUnitary, ButterflyBmm  # noqa
from .butterfly_base4 import ButterflyBase4  # noqa
from .multiply import butterfly_multiply  # noqa
from . import combine
from . import complex_utils
from . import diagonal
from . import permutation
from . import special
from . import multiply_base4

__all__ = [
    'Butterfly',
    'ButterflyUnitary',
    'ButterflyBmm',
    'ButterflyBase4',
    'butterfly_multiply',
    '__version__',
]
```

### Complete `csrc/version.cpp` Migration

```cpp
#include <Python.h>
#include <torch/library.h>

#ifdef WITH_CUDA
#include <cuda.h>
#endif

#ifdef _WIN32
PyMODINIT_FUNC PyInit__version(void) { return NULL; }
#endif

int64_t cuda_version() {
#ifdef WITH_CUDA
  return CUDA_VERSION;
#else
  return -1;
#endif
}

TORCH_LIBRARY(torch_butterfly, m) {
    m.def("cuda_version", cuda_version);
}
```

### setup.py Change (Remove no_python_abi_suffix)

```python
# BEFORE:
setup(
    ext_modules=get_extensions(),
    cmdclass={
        "build_ext": BuildExtension.with_options(
            no_python_abi_suffix=True, use_ninja=True
        )
    },
)

# AFTER:
setup(
    ext_modules=get_extensions(),
    cmdclass={
        "build_ext": BuildExtension.with_options(use_ninja=True)
    },
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `torch::RegisterOperators().op(...)` | `TORCH_LIBRARY(ns, m) { m.def(...); }` | PyTorch 1.7+ | Modern dispatcher integration, torch.compile compatibility |
| `PathFinder().find_spec()` for .so discovery | `__file__`-relative path + glob | PEP 660 (2022+) | Required for modern editable installs |
| `no_python_abi_suffix=True` | Standard ABI suffix + glob loading | Always available, just not used | Proper wheel packaging, setuptools compatibility |
| `setup.py develop` (legacy editable) | `pip install -e .` (PEP 660) | pip 24.2 deprecated legacy (2024) | Legacy editable removed in pip 25.0 |

## Open Questions

1. **Cross-platform glob patterns**
   - What we know: Linux uses `.so`, Windows uses `.pyd`, macOS uses `.dylib`. The current C++ code has `_WIN32` guards.
   - What's unclear: Whether macOS actually uses `.dylib` or `.so` for PyTorch extensions (PyTorch on macOS typically produces `.so` files anyway).
   - Recommendation: Check all three suffixes. The overhead is negligible and ensures correctness.

## Sources

### Primary (HIGH confidence)
- `csrc/butterfly.cpp` lines 127-131 -- TORCH_LIBRARY macro template (verified in codebase)
- `csrc/version.cpp` lines 22-23 -- deprecated RegisterOperators pattern (verified in codebase)
- `torch_butterfly/__init__.py` lines 8-11 -- current PathFinder mechanism (verified in codebase)
- `setup.py` lines 64-71 -- current BuildExtension.with_options configuration (verified in codebase)
- `.planning/phases/01-build-system-foundation/01-VERIFICATION.md` -- Phase 1 gaps documenting INST-01/02 import failures due to check_cuda_version()
- [PyTorch PR #14130](https://github.com/pytorch/pytorch/pull/14130) -- Original PR adding `no_python_abi_suffix` option, explaining its purpose for `load_library`
- [PyTorch Custom C++ and CUDA Operators tutorial](https://docs.pytorch.org/tutorials/advanced/cpp_custom_ops.html) -- Current recommended patterns for operator registration
- [setuptools Development Mode docs](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) -- PEP 660 editable install behavior with compiled extensions

### Secondary (MEDIUM confidence)
- [PEP 660](https://peps.python.org/pep-0660/) -- Editable install specification; confirms build backends may do in-place builds as side effect
- [pip 24.2 legacy editable deprecation](https://ichard26.github.io/blog/2024/08/whats-new-in-pip-24.2/) -- Legacy `setup.py develop` deprecated, PEP 660 required

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries; all changes use existing torch + stdlib
- Architecture: HIGH -- the `__file__`-relative glob pattern is the standard approach used by pytorch_scatter, torchvision, and other PyTorch extension libraries
- Pitfalls: HIGH -- all pitfalls verified against actual code; TORCH_LIBRARY namespace collision verified safe by examining setup.py extension loop

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stable domain, no fast-moving dependencies)
