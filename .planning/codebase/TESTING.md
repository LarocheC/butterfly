# Testing Patterns

**Analysis Date:** 2026-04-02

## Test Framework

**Runner:**
- `unittest` (Python standard library) - no third-party test framework
- Config: None (no `pytest.ini`, `setup.cfg`, `tox.ini`, or `conftest.py`)
- Note: `setup.py` has commented-out `pytest-runner` and `pytest` dependencies (lines 57-59), suggesting pytest was considered but not adopted

**Assertion Library:**
- `unittest.TestCase` built-in assertions: `self.assertTrue`, `self.assertEqual`
- `torch.allclose` for numerical comparison (wrapped in `self.assertTrue`)
- `np.allclose` and `np.all` for numpy-based comparisons

**Run Commands:**
```bash
python -m unittest discover tests/          # Run all tests in tests/
python -m unittest tests/test_butterfly.py  # Run specific test file
python tests/test_butterfly.py              # Run directly (each file has __main__ guard)
```

## Test File Organization

**Location:**
- Primary tests: `tests/` directory (separate from source)
- Legacy tests: `tests_old/` directory (older versions, not maintained)
- Scattered test files: `learning_transforms/test_factor_multiply.py`, `convolution/models/test_kops.py`

**Naming:**
- Pattern: `test_{module_name}.py`
- Maps 1:1 to source modules in `torch_butterfly/`:

| Test File | Source Module |
|-----------|--------------|
| `tests/test_butterfly.py` | `torch_butterfly/butterfly.py` |
| `tests/test_multiply.py` | `torch_butterfly/multiply.py` |
| `tests/test_multiply_base4.py` | `torch_butterfly/multiply_base4.py` |
| `tests/test_special.py` | `torch_butterfly/special.py` |
| `tests/test_combine.py` | `torch_butterfly/combine.py` |
| `tests/test_complex_utils.py` | `torch_butterfly/complex_utils.py` |
| `tests/test_permutation.py` | `torch_butterfly/permutation.py` |
| `tests/test_butterfly_base4.py` | `torch_butterfly/butterfly_base4.py` |

**Structure:**
```
tests/
├── test_butterfly.py         # 310 lines - Butterfly, ButterflyUnitary, ButterflyBmm
├── test_special.py           # 376 lines - FFT, DCT, DST, circulant, toeplitz, hadamard, wavelet
├── test_combine.py           #  98 lines - diagonal_butterfly, butterfly_product, kronecker
├── test_multiply.py          #  95 lines - butterfly_multiply forward/backward
├── test_permutation.py       #  85 lines - permutation factorization
├── test_complex_utils.py     #  60 lines - complex_matmul, index_last_dim
├── test_multiply_base4.py    #  48 lines - base-4 multiply
├── test_butterfly_base4.py   #  42 lines - ButterflyBase4 module
```

## Test Structure

**Suite Organization:**
```python
class ButterflyTest(unittest.TestCase):

    def setUp(self):
        self.rtol = 1e-3
        self.atol = 1e-5

    def test_butterfly(self):
        # ... test code

    def test_fft_init(self):
        # ... test code

if __name__ == "__main__":
    unittest.main()
```

**Key patterns:**
- One test class per file
- `setUp()` defines shared tolerances: `self.rtol = 1e-3`, `self.atol = 1e-5`
- Every file ends with `if __name__ == "__main__": unittest.main()`
- No `tearDown()` methods used

**Assertion Style:**
- Primary assertion: `self.assertTrue(torch.allclose(output, expected, rtol=self.rtol, atol=self.atol))`
- Debug info passed as second arg to `assertTrue` for failure diagnostics:
```python
self.assertTrue(torch.allclose(output, output_torch, rtol=self.rtol, atol=self.atol),
                ((output - output_torch).abs().max().item(), device, complex, increasing_stride))
```
- Shape checks: `self.assertTrue(output.shape == (batch_size, out_size), (output.shape, ...))`

## Test Strategy: Exhaustive Parameter Sweeps

**The dominant testing pattern is nested loops over parameter combinations:**
```python
def test_butterfly(self):
    batch_size = 10
    for device in ['cpu'] + ([] if not torch.cuda.is_available() else ['cuda']):
        for in_size, out_size in [(7, 15), (15, 7)]:
            for complex in [False, True]:
                for increasing_stride in [True, False]:
                    for init in ['randn', 'ortho', 'identity']:
                        for nblocks in [1, 2, 3]:
                            b = Butterfly(in_size, out_size, True, complex,
                                          increasing_stride, init, nblocks=nblocks).to(device)
                            # ... assertions
```

**Standard parameter dimensions swept:**
- `device`: `['cpu']` + `['cuda']` if available
- `complex`: `[False, True]`
- `increasing_stride`: `[True, False]`
- `nblocks`: `[1, 2, 3]`
- `init`: `['randn', 'ortho', 'identity']`
- `in_size, out_size`: non-power-of-2 sizes like `(7, 15), (15, 7)` to test padding
- `normalized`: `[False, True]` for transform tests
- `br_first`: `[True, False]` for FFT decomposition variants

## Correctness Verification Patterns

**Pattern 1: C++ vs Python reference implementation**
Compare optimized C++ kernel output against pure-Python reference:
```python
# From tests/test_multiply.py
output = torch_butterfly.butterfly_multiply(twiddle, input, increasing_stride)
output_torch = torch_butterfly.multiply.butterfly_multiply_torch(twiddle, input, increasing_stride)
self.assertTrue(torch.allclose(output, output_torch, rtol=self.rtol, atol=self.atol))
```

**Pattern 2: Compare against known library (ground truth)**
Compare butterfly-based transforms against standard implementations:
```python
# From tests/test_special.py - FFT
out_torch = torch.fft.fft(input, norm='ortho')
b = torch_butterfly.special.fft(n, normalized=True, br_first=br_first)
out = b(input)
self.assertTrue(torch.allclose(out, out_torch, self.rtol, self.atol))

# DCT against scipy
out_sp = torch.tensor(scipy.fft.dct(input.numpy(), type=type, norm='ortho'))
b = torch_butterfly.special.dct(n, type=type, normalized=True)
out = b(input)
self.assertTrue(torch.allclose(out, out_sp, self.rtol, self.atol))
```

**Pattern 3: Gradient verification**
Verify autograd by comparing C++ backward against PyTorch autograd on reference:
```python
grad = torch.randn_like(output_torch)
d_twiddle, d_input = torch.autograd.grad(output, (twiddle, input), grad, retain_graph=True)
d_twiddle_torch, d_input_torch = torch.autograd.grad(output_torch, (twiddle, input), grad)
self.assertTrue(torch.allclose(d_twiddle, d_twiddle_torch, ...))
```

**Pattern 4: Property-based checks**
Verify mathematical properties (e.g., unitarity):
```python
# From tests/test_butterfly.py - test_butterfly_unitary
eye = torch.eye(size, dtype=torch.complex64)
twiddle_matrix_np = b(eye).t().detach().numpy()
self.assertTrue(np.allclose(twiddle_matrix_np @ twiddle_matrix_np.T.conj(),
                            np.eye(size), self.rtol, self.atol))
```

**Pattern 5: Optimization convergence**
Verify autograd works by checking training loss decreases:
```python
# From tests/test_butterfly.py - test_autograd
for i in range(niters):
    out = model(x)
    loss = F.mse_loss(out, y)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
self.assertTrue(loss.item() < inital_loss.item())
```

**Pattern 6: Equivalence between implementations**
Verify that two code paths produce the same result:
```python
# ButterflyBmm vs loop of Butterfly (tests/test_butterfly.py)
output = b_bmm(input)
output_loop = []
for i in range(matrix_batch):
    b = Butterfly(..., init=b_bmm.twiddle[i * b_bmm.nstacks:(i + 1) * b_bmm.nstacks], ...)
    output_loop.append(b(input[:, i]))
output_loop = torch.stack(output_loop, dim=1)
self.assertTrue(torch.allclose(output, output_loop))
```

## Mocking

**Framework:** None. No mocking is used.

**Approach:** Tests use real computations with random tensors. No external services to mock. CUDA tests are conditionally skipped with:
```python
for device in ['cpu'] + ([] if not torch.cuda.is_available() else ['cuda']):
```

Large batch sizes are skipped on CPU to avoid slow tests:
```python
if batch_size > 1024 and (device == 'cpu'):
    continue
```

## Test Data

**Random tensor generation:**
```python
batch_size = 10
n = 16
input = torch.randn(batch_size, n, dtype=torch.complex64)
twiddle = torch.randn((nstacks, nblocks, log_n, n // 2, 2, 2), dtype=dtype) * scaling
```

**Fixed inputs for deterministic tests:**
```python
input = torch.eye(n, dtype=dtype)  # Identity matrix for extracting columns
input = torch.arange(n, dtype=torch.float32)  # Sequential for permutation tests
```

**Typical sizes:**
- `batch_size`: 10 (standard), 1 (minimal), 8192 (stress/race condition)
- `n`: 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 4096
- Non-power-of-2: 7, 9, 13, 15, 27, 38 (to test padding)

**No fixture files or factories.** All test data is generated inline.

## Coverage

**Requirements:** None enforced. No coverage tool configured.

**Gaps:**
- `torch_butterfly/diagonal.py` has no dedicated test file (tested indirectly via `test_special.py`)
- `torch_butterfly/benchmark_utils.py` and `torch_butterfly/input_padding_benchmark.py` are untested
- `learning_transforms/` has one test file (`test_factor_multiply.py`) for a large module
- `butterfly/` (old package) has tests only in `tests_old/`
- `convolution/` has only `models/test_kops.py`
- No edge case tests for empty inputs, zero-size tensors, or error conditions

## Test Types

**Unit Tests:**
- All tests in `tests/` are numerical correctness tests
- Test individual modules against reference implementations or mathematical properties
- Gradient correctness verified via autograd comparison

**Integration Tests:**
- `test_butterfly_bmm_tensorproduct` in `tests/test_butterfly.py` tests composition of multiple Butterfly modules
- `test_conv2d_circular_multichannel` in `tests/test_special.py` tests full convolution pipeline

**E2E Tests:**
- Not present. No end-to-end training tests.

**Performance Tests:**
- `learning_transforms/speed_test.py` - benchmarks transform speeds
- `torch_butterfly/input_padding_benchmark.py` - benchmarks padding operations
- `torch_butterfly/benchmark_utils.py` - CUDA timing utilities
- These are standalone scripts, not part of the test suite

## Numerical Tolerance Handling

**Standard tolerances:**
```python
self.rtol = 1e-3  # Relative tolerance
self.atol = 1e-5  # Absolute tolerance
```

**Relaxed tolerances for known noisy cases:**
```python
# Large batch sizes on CUDA have race conditions in gradient accumulation
rtol=self.rtol * (10 if batch_size > 1024 else 1),
atol=self.atol * (10 if batch_size > 1024 else 1)
```

## Third-Party Test Dependencies

- `numpy` - array operations and `np.allclose`
- `scipy` - reference implementations (`scipy.linalg`, `scipy.fft`)
- `pywt` - wavelet reference implementation (PyWavelets)
- These are not declared in `requirements.txt` but are needed to run tests

---

*Testing analysis: 2026-04-02*
