# Architecture

**Analysis Date:** 2026-04-02

## Pattern Overview

**Overall:** Research library with a core reusable module (`torch_butterfly`) and multiple experiment/application directories that consume it. The core module follows a layered design: C++/CUDA kernels at the bottom, Python wrappers in the middle, and high-level nn.Module classes at the top.

**Key Characteristics:**
- PyTorch C++/CUDA extension pattern: native kernels registered via `torch.ops`, wrapped in Python `torch.jit.script` functions, consumed by `nn.Module` classes
- Two-generation codebase: a legacy `butterfly/` package (old interface) and the current `torch_butterfly/` package (new interface)
- Experiment directories (`cnn/`, `convolution/`, `transformer/`, `learning_transforms/`, `gumbel-sinkhorn/`) are standalone scripts that import from the core packages
- All transforms operate on power-of-2 sizes; inputs are zero-padded or trimmed internally

## Layers

**Native Kernel Layer (C++/CUDA):**
- Purpose: High-performance butterfly multiply forward and backward passes
- Location: `csrc/`
- Contains: `csrc/butterfly.cpp` (dispatch + autograd), `csrc/cpu/butterfly_cpu.cpp` (CPU impl), `csrc/cuda/butterfly_cuda.cu` (CUDA impl)
- Depends on: PyTorch C++ API (`torch/script.h`, `torch/extension.h`)
- Used by: `torch_butterfly/multiply.py` via `torch.ops.torch_butterfly.*`
- Key detail: Registers three ops via `TORCH_LIBRARY(torch_butterfly, m)`: `butterfly_multiply_fw`, `butterfly_multiply_bw`, `butterfly_multiply` (which wraps autograd)

**Core Multiply Layer (Python):**
- Purpose: Python-accessible butterfly multiplication with both native and pure-PyTorch fallback
- Location: `torch_butterfly/multiply.py`, `torch_butterfly/multiply_base4.py`
- Contains: `butterfly_multiply()` (calls native op), `butterfly_multiply_torch()` (pure PyTorch reference), `butterfly_multiply_base4_torch()`, `twiddle_base2_to_base4()`
- Depends on: Native kernel layer (for `butterfly_multiply`), PyTorch (for `_torch` variants)
- Used by: `torch_butterfly/butterfly.py`, `torch_butterfly/butterfly_base4.py`

**nn.Module Layer:**
- Purpose: User-facing modules compatible with `torch.nn.Linear`
- Location: `torch_butterfly/butterfly.py`
- Contains: `Butterfly` (main class), `ButterflyUnitary` (unitary-constrained variant), `ButterflyBmm` (batched variant)
- Depends on: Core multiply layer, `torch_butterfly/complex_utils.py`
- Used by: `torch_butterfly/special.py`, `torch_butterfly/combine.py`, experiment code

**Composition Layer:**
- Purpose: Combine butterfly matrices with diagonals, permutations, and other butterflies
- Location: `torch_butterfly/combine.py`, `torch_butterfly/permutation.py`, `torch_butterfly/diagonal.py`
- Contains: `diagonal_butterfly()`, `butterfly_product()`, `butterfly_kronecker()`, `TensorProduct`, `FixedPermutation`, `Diagonal`, `perm2butterfly()`
- Depends on: nn.Module layer
- Used by: `torch_butterfly/special.py`

**Special Transforms Layer:**
- Purpose: Factory functions that construct butterfly networks performing exact well-known transforms
- Location: `torch_butterfly/special.py`
- Contains: `fft()`, `ifft()`, `fft_unitary()`, `ifft_unitary()`, `dct()`, `dst()`, `circulant()`, `toeplitz()`, `hadamard()`, `hadamard_diagonal()`, `conv1d_circular_singlechannel()`, `conv1d_circular_multichannel()`
- Depends on: nn.Module layer, composition layer, permutation layer
- Used by: Tests, experiment code

**Legacy Interface:**
- Purpose: Original butterfly implementation (being replaced)
- Location: `butterfly/`
- Contains: `butterfly/butterfly.py` (old Butterfly class), `butterfly/butterfly_multiply.py` (old multiply with both C++ and pure-PyTorch), `butterfly/permutation.py`, `butterfly/complex_utils.py`
- Depends on: `butterfly/factor_multiply/` and `butterfly/factor_multiply_fast/` (old C++ extensions, separate `setup.py` each)
- Used by: `learning_transforms/`, `cnn/` experiment code

## Data Flow

**Forward Pass (Butterfly Multiply):**

1. Input tensor `(batch, *, in_size)` enters `Butterfly.forward()`
2. `pre_process()` reshapes to `(batch, nstacks, in_size)`, expanding for nstacks
3. `butterfly_multiply(twiddle, output, increasing_stride, output_size)` dispatches to C++/CUDA kernel
4. Kernel iterates over `nblocks` x `log_n` butterfly factors, each applying 2x2 twiddle matrices at varying strides
5. `post_process()` reshapes output to `(batch, *, out_size)`, trims, and adds bias

**Twiddle Factor Shape:**
- Base-2: `(nstacks, nblocks, log_n, n//2, 2, 2)` - log_n stages of n//2 2x2 butterfly factors
- Base-4: `(nstacks, nblocks, log_n//2, n//4, 4, 4)` - fuses pairs of stages for efficiency
- Unitary: `(nstacks, nblocks, log_n, n//2, 4)` - parameterized by (phi, alpha, psi, chi) angles to enforce unitarity

**Special Transform Construction (e.g., FFT):**

1. Compute exact twiddle factors analytically (e.g., roots of unity for FFT)
2. Stack factors into twiddle tensor of shape `(1, 1, log_n, n//2, 2, 2)`
3. Initialize a `Butterfly` module with this twiddle tensor
4. Optionally compose with `FixedPermutation` (bit-reversal) via `nn.Sequential`

**State Management:**
- All learnable state is in `nn.Parameter` tensors: `twiddle` (or `twiddle4`/`twiddle2` for base-4), `bias`, `diagonal`
- `twiddle._is_structured = True` flag used to exclude from weight decay during training
- Permutations stored as `register_buffer` (not learnable)

## Key Abstractions

**Butterfly (nn.Module):**
- Purpose: Product of log(N) butterfly factors, drop-in replacement for `nn.Linear`
- Examples: `torch_butterfly/butterfly.py` (lines 15-208)
- Pattern: Parameterized by a single twiddle tensor; forward pass calls into C++/CUDA; supports transpose, conjugate, subtwiddle

**ButterflyUnitary:**
- Purpose: Butterfly constrained to be unitary via angle parameterization
- Examples: `torch_butterfly/butterfly.py` (lines 210-308)
- Pattern: Inherits from Butterfly but overrides twiddle to use 4 angle parameters per 2x2 block, constructs unitary matrix on the fly in forward()

**FixedPermutation (nn.Module):**
- Purpose: Apply a fixed (non-learnable) permutation to the last dimension
- Examples: `torch_butterfly/permutation.py` (lines 55-78)
- Pattern: Stores permutation as buffer; uses custom autograd for complex backward compatibility

**Diagonal (nn.Module):**
- Purpose: Element-wise multiplication by a learnable diagonal
- Examples: `torch_butterfly/diagonal.py`
- Pattern: Simple wrapper around `input * self.diagonal`

**diagonal_butterfly (function):**
- Purpose: Fuse a diagonal matrix into a butterfly's twiddle factors (avoids separate diagonal module)
- Examples: `torch_butterfly/combine.py` (lines 11-53)
- Pattern: Modifies the first or last twiddle factor in-place to absorb the diagonal

## Entry Points

**Package Installation:**
- Location: `setup.py`
- Triggers: `python setup.py install`
- Responsibilities: Compiles C++/CUDA extensions from `csrc/`, installs `torch_butterfly` package

**Package Import:**
- Location: `torch_butterfly/__init__.py`
- Triggers: `import torch_butterfly`
- Responsibilities: Loads compiled native libraries (`_version`, `_butterfly`), checks CUDA version compatibility, exports `Butterfly`, `ButterflyUnitary`, `ButterflyBmm`, `ButterflyBase4`, `butterfly_multiply`

**Tests:**
- Location: `tests/test_butterfly.py`, `tests/test_special.py`, etc.
- Triggers: pytest
- Responsibilities: Verify correctness of butterfly multiply, special transforms, permutation decomposition

## Error Handling

**Strategy:** Assertions and PyTorch TORCH_CHECK macros. No custom exception hierarchy.

**Patterns:**
- C++ layer uses `TORCH_CHECK` macros for shape/device validation in `csrc/butterfly.cpp`
- Python layer uses `assert` statements for shape, size, and parameter validation
- CUDA version mismatch raises `RuntimeError` at import time in `torch_butterfly/__init__.py`
- Power-of-2 size requirements enforced via assertion: `assert n == 1 << log_n, 'n must be a power of 2'`

## Cross-Cutting Concerns

**Logging:** No structured logging. Uses standard Python print where needed in experiment scripts.

**Validation:** Input size validation happens at both C++ level (`CHECK_SHAPE`, `CHECK_DIM`, `CHECK_DEVICE`) and Python level (asserts on tensor shapes). Inputs not power-of-2 are automatically padded with zeros.

**Complex Number Support:** Extensive complex tensor support throughout. Custom autograd functions in `torch_butterfly/complex_utils.py` work around PyTorch 1.7 limitations (e.g., `IndexLastDim`, `ComplexMatmul`, `Real2ComplexFn`). Optional cupy integration for faster complex matmul on GPU.

**Device Dispatch:** C++ dispatch in `csrc/butterfly.cpp` routes to CPU or CUDA implementations based on input device. Pure-PyTorch fallback available via `butterfly_multiply_torch()`.

---

*Architecture analysis: 2026-04-02*
