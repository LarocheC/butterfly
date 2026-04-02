# Coding Conventions

**Analysis Date:** 2026-04-02

## Naming Patterns

**Files:**
- Use `snake_case.py` for all Python modules: `butterfly.py`, `complex_utils.py`, `multiply_base4.py`
- Test files follow `test_{module}.py` pattern: `test_butterfly.py`, `test_multiply.py`
- Benchmark files use `benchmark_` prefix or `speed_test.py` style: `benchmark_utils.py`, `benchmark_linear.py`
- C++ source files use `snake_case.cpp` / `snake_case.cu`: `butterfly.cpp`, `butterfly_cpu.cpp`, `butterfly_cuda.cu`

**Classes:**
- Use `PascalCase` for all classes: `Butterfly`, `ButterflyUnitary`, `ButterflyBmm`, `ButterflyBase4`
- nn.Module subclasses use descriptive names: `FixedPermutation`, `Diagonal`, `TensorProduct`, `Real2Complex`, `Complex2Real`
- Test classes use `{Feature}Test` suffix: `ButterflyTest`, `ButterflyPermutationTest`, `MultiplyBase4Test`
- Custom autograd functions use `PascalCase`: `ComplexMatmul`, `IndexLastDim`, `Real2ComplexFn`

**Functions:**
- Use `snake_case` for all functions: `butterfly_multiply`, `bitreversal_permutation`, `diagonal_butterfly`
- Factory functions that return nn.Module use lowercase: `fft()`, `ifft()`, `hadamard()`, `circulant()`, `toeplitz()`
- Internal/torch JIT functions use `_fw` / `_bw` suffixes: `butterfly_multiply_fw`, `butterfly_multiply_bw`
- Pure-Python reference implementations use `_torch` suffix: `butterfly_multiply_torch`, `butterfly_multiply_base4_torch`
- Conversion utilities use `x2y` or `x_to_y` style: `twiddle_base2_to_base4`, `perm2butterfly`, `real2complex`

**Variables:**
- Short mathematical names preferred for tensor variables: `n`, `log_n`, `twiddle`, `phi`, `alpha`, `psi`, `chi`
- Prefix `d_` for gradient tensors: `d_twiddle`, `d_input`
- Dimension sizes use descriptive short names: `batch_size`, `nstacks`, `nblocks`, `in_size`, `out_size`
- Booleans use descriptive names: `increasing_stride`, `br_first`, `diag_first`, `normalized`, `separate_diagonal`

**Parameters:**
- `complex` (bool) for complex/real flag (shadows Python builtin, but used consistently)
- `dtype` derived from `complex` flag: `torch.float32 if not complex else torch.complex64`

## Code Style

**Formatting:**
- No automated formatter configured (no `.flake8`, `pyproject.toml`, `.prettierrc`, or similar)
- Line length varies (some lines exceed 100 characters, particularly in test files)
- 4-space indentation (Python standard)

**Linting:**
- No linter configured
- No type checking (no `mypy.ini` or `pyproject.toml` with mypy config)

**Imports:**
- Standard library first, blank line, then third-party, blank line, then local
- Example from `torch_butterfly/butterfly.py`:
```python
import math
import numbers

import torch
from torch import nn
import torch.nn.functional as F

import torch_butterfly
from torch_butterfly.multiply import butterfly_multiply
from torch_butterfly.complex_utils import real_dtype_to_complex, complex_reshape
```

**Import Style:**
- `import torch` (always top-level)
- `from torch import nn` (preferred over `import torch.nn as nn`)
- `import torch.nn.functional as F` (standard alias)
- `from torch.nn import functional as F` (also used, inconsistent)
- Local package imports use explicit relative or absolute: `from torch_butterfly.multiply import butterfly_multiply`
- `# noqa` comments used on re-exports in `__init__.py`

## nn.Module Patterns

**Constructor pattern:**
- Always call `super().__init__()` first
- Store all config as instance attributes: `self.in_size`, `self.log_n`, `self.n`, etc.
- Use `nn.Parameter()` for learnable tensors
- Use `self.register_parameter('bias', None)` for optional parameters when disabled
- Use `self.register_buffer()` for non-learnable persistent state (e.g., permutations)
- Custom flags on parameters: `self.twiddle._is_structured = True  # Flag to avoid weight decay`
- Separate `reset_parameters()` method for initialization logic

**Forward method:**
- Always include docstring with Parameters/Return sections
- Input/output shape documented in docstring: `input: (batch, *, in_size)`, `output: (batch, *, out_size)`

**extra_repr pattern:**
- Return formatted string of constructor args:
```python
def extra_repr(self):
    s = 'in_size={}, out_size={}, bias={}, complex={}'.format(
        self.in_size, self.out_size, self.bias is not None, self.complex)
    return s
```

## Custom Autograd Functions

**Pattern used throughout `torch_butterfly/complex_utils.py`:**
```python
class ComplexMatmul(torch.autograd.Function):
    @staticmethod
    def forward(ctx, X, Y):
        ctx.save_for_backward(X, Y)
        # ... computation
        return result

    @staticmethod
    def backward(ctx, grad):
        X, Y = ctx.saved_tensors
        # ... gradient computation
        return grad_X, grad_Y
```
- Use `ctx.save_for_backward()` for tensors needed in backward
- Check `ctx.needs_input_grad[i]` before computing gradients
- Provide a module-level function wrapping the `.apply` call: `complex_matmul = ComplexMatmul.apply` or `real2complex = Real2ComplexFn.apply`

## Error Handling

**Patterns:**
- Use `assert` statements for preconditions (not exceptions). This is used pervasively:
```python
assert n == 1 << log_n, 'n must be a power of 2'
assert butterfly.nstacks == 1
assert butterfly.bias is None
assert init in ['empty', 'randn', 'ortho', 'identity', 'fft_no_br', 'ifft_no_br']
```
- C++ extensions use `TORCH_CHECK` macros for runtime validation:
```cpp
#define CHECK_DEVICE(x) TORCH_CHECK(x.device().type() == torch::kCPU || x.device().type() == torch::kCUDA, ...)
#define CHECK_DIM(x, y) TORCH_CHECK(x.dim() == y, ...)
#define CHECK_SHAPE(x, ...) TORCH_CHECK(x.sizes() == torch::IntArrayRef({__VA_ARGS__}), ...)
```
- `RuntimeError` raised for CUDA version mismatch in `torch_butterfly/__init__.py`
- No try/except blocks in the core library code

## Logging

**Framework:** None. No logging framework used.
- Commented-out `print` statements appear in test files for debugging (see `tests/test_multiply.py` lines 48-54)
- No production logging

## Comments

**When to Comment:**
- Inline comments explain mathematical reasoning: `# Sampling from the Haar measure on U(2) is a bit subtle.`
- Reference external papers/resources: `# Using the parameterization here: http://home.lu.lv/~sd20008/papers/essays/...`
- Warn about tricky code: `# Warning: All this dimension manipulation (transpose and unsqueeze) is super tricky.`
- Explain workarounds: `# Pytorch 1.7 doesn't support complex reshape backward for non-contiguous tensors`
- Commented-out alternative implementations are common (kept for reference)

**Docstrings:**
- Present on public classes and key functions
- Use plain text format (not Sphinx/NumPy/Google style)
- Parameter sections use `Parameters:` / `Parameter:` and `Return:` / `Returns:` headings
- Shape annotations included: `input: (batch, *, in_size)`
- Example from `torch_butterfly/combine.py`:
```python
def diagonal_butterfly(butterfly: Butterfly,
                       diagonal: torch.Tensor,
                       diag_first: bool,
                       inplace: bool = True) -> Butterfly:
    """
    Combine a Butterfly and a diagonal into another Butterfly.
    Only support nstacks==1 for now.
    Parameters:
        butterfly: Butterfly(in_size, out_size)
        diagonal: size (in_size,) if diag_first, else (out_size,).
        diag_first: If True, the map is input -> diagonal -> butterfly.
        inplace: whether to modify the input Butterfly
    """
```

## Function Design

**Size:** Functions are compact, typically under 50 lines. Largest modules are `special.py` (805 lines) and `permutation.py` (433 lines), but they contain many small independent functions.

**Parameters:**
- Type annotations used sparingly: present on some function signatures (`combine.py`), absent on most
- Return type annotations used with `-> nn.Module` or `-> Butterfly` on factory/combination functions
- `torch.jit.script` decorators on performance-critical functions in `torch_butterfly/multiply.py`

**Return Values:**
- Factory functions return `nn.Module` or `nn.Sequential`
- Tensor operations return `torch.Tensor`
- In-place operations return `self` (e.g., `__imul__`)

## Module Design

**Exports:**
- `torch_butterfly/__init__.py` defines `__all__` with public API: `Butterfly`, `ButterflyUnitary`, `ButterflyBmm`, `ButterflyBase4`, `butterfly_multiply`
- Submodules imported as namespace: `from . import combine`, `from . import special`
- No barrel files beyond `__init__.py`

**C++ Extensions:**
- Loaded dynamically in `__init__.py` via `torch.ops.load_library`
- Registered as TorchScript custom ops: `torch.ops.torch_butterfly.butterfly_multiply_fw`
- CPU/CUDA dispatch handled in C++ with `#ifdef WITH_CUDA` guards

**torch.no_grad() Usage:**
- Consistently used when modifying parameters outside of training:
```python
with torch.no_grad():
    twiddle.copy_(...)
```

---

*Convention analysis: 2026-04-02*
