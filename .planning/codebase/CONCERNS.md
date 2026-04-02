# Codebase Concerns

**Analysis Date:** 2026-04-02

## Tech Debt

**Dual/Legacy Code Paths (Old vs New Interface):**
- Issue: The codebase maintains two parallel implementations of butterfly operations: a legacy `butterfly/` package and the newer `torch_butterfly/` package. The README explicitly states the old interface is "being rewritten" and advises using the new one, yet the old code remains fully present.
- Files: `butterfly/butterfly.py`, `butterfly/butterfly_multiply.py`, `butterfly/complex_utils.py`, `butterfly/permutation.py`, `butterfly/permutation_multiply.py`
- Impact: Confusion about which implementation to use. Both are importable. `butterfly/__init__.py` still exports the old `Butterfly` class.
- Fix approach: Remove or clearly deprecate the `butterfly/` directory. Update all downstream code (`cnn/`, `learning_transforms/`) to use `torch_butterfly`.

**Old Test Directory:**
- Issue: `tests_old/` directory contains 871 lines of tests for the legacy `butterfly/` interface, alongside the current `tests/` directory.
- Files: `tests_old/test_butterfly_multiply.py` (601 lines), `tests_old/test_butterfly.py`, `tests_old/test_permutation_multiply.py`, `tests_old/test_permutation.py`
- Impact: Unclear which tests are canonical. Old tests may not pass against the current codebase.
- Fix approach: Either remove `tests_old/` or migrate valuable test cases into `tests/`.

**Old Learning Transforms Code:**
- Issue: Files explicitly named "old" still present and importable.
- Files: `learning_transforms/old/learning_fft_old.py` (972 lines), `learning_transforms/butterfly_old.py` (786 lines)
- Impact: Dead code increasing maintenance burden and confusion.
- Fix approach: Remove old files after verifying no active code depends on them.

**Hardcoded Apex Dependency in Old Interface:**
- Issue: `butterfly/butterfly_multiply.py` lines 37-41 unconditionally raise `ImportError` if NVIDIA Apex is not installed, even though Apex is not needed for the new `torch_butterfly` interface. This blocks importing the old butterfly module entirely without Apex.
- Files: `butterfly/butterfly_multiply.py`
- Impact: Users importing the old interface hit a hard failure. Apex is largely superseded by PyTorch's native AMP.
- Fix approach: Make the Apex import optional with a graceful fallback, or remove the dependency if old interface is dropped.

**Stale Commented-Out Code:**
- Issue: Extensive commented-out code throughout, especially in `torch_butterfly/complex_utils.py` (lines 42-43, 52-53, 67-72, 81-86) and setup files.
- Files: `torch_butterfly/complex_utils.py`, `butterfly/factor_multiply_fast/setup.py`, `butterfly/factor_multiply/setup.py`
- Impact: Reduces readability, creates confusion about what is active.
- Fix approach: Remove commented-out code; rely on git history for prior approaches.

## Known Bugs

**NameError in ComplexLinear.reset_parameters:**
- Symptoms: `ComplexLinear.reset_parameters()` references bare `weight` instead of `self.weight` on line 170, causing a `NameError` at initialization time.
- Files: `torch_butterfly/complex_utils.py` line 170
- Trigger: Instantiating `ComplexLinear` (i.e. `ComplexLinear(4, 8)`) will crash.
- Workaround: None; the class is broken as-is.

**Potential Memory Leak (Unresolved):**
- Symptoms: Acknowledged in TODO comments but never resolved.
- Files: `learning_transforms/ops.py` line 202, `learning_transforms/learning_ops.py` line 163
- Trigger: Unknown; the investigation code is commented out.
- Workaround: None documented.

## Security Considerations

**Bare Except Clauses (Silent Failures):**
- Risk: 20+ bare `except:` clauses silently swallow all exceptions including `KeyboardInterrupt` and `SystemExit`. This masks real errors and makes debugging difficult.
- Files: `butterfly/butterfly_multiply.py` line 31, `butterfly/permutation_multiply.py` line 11, `torch_butterfly/complex_utils.py` line 13, `cnn/cifar_experiment.py` line 260, `cnn/distill_experiment.py` lines 66/225, `cnn/permuted_experiment.py` line 407, `convolution/ray_runner.py` lines 153/160, `learning_transforms/learning_transforms.py` lines 159/263, `learning_transforms/robust_pca.py` line 50, `cnn/imagenet/training.py` lines 461/474
- Current mitigation: None.
- Recommendations: Replace all bare `except:` with specific exception types (e.g., `except ImportError:`, `except RuntimeError:`).

**Disabled Warning for CuPy Fallback:**
- Risk: When CuPy import fails, the warning is commented out, so users have no indication they are running a slower code path.
- Files: `torch_butterfly/complex_utils.py` lines 15-16
- Current mitigation: None.
- Recommendations: Uncomment the warning or use `logging.debug`.

## Performance Bottlenecks

**CUDA sm_35/sm_30 Architecture Targets:**
- Problem: The CUDA code targets very old GPU architectures (sm_30, sm_35 dating to Kepler/Maxwell era ~2012-2014). Modern GPUs (Ampere sm_80, Hopper sm_90) do not benefit from these old targets.
- Files: `setup.py` line 29 (`-arch=sm_35`), `butterfly/factor_multiply_fast/setup.py` line 17 (`-arch=sm_30`)
- Cause: Hardcoded architecture flags never updated.
- Improvement path: Use `torch.cuda.get_device_capability()` dynamically or set a reasonable minimum (sm_70+). The fast multiply setup does conditionally add sm_70 but still defaults to sm_30.

**Float-Only CUDA Kernels:**
- Problem: CUDA kernels explicitly disable float64 support to "speed up compilation time" via a macro override.
- Files: `csrc/cuda/butterfly_cuda.cu` lines 7-22
- Cause: Deliberate tradeoff for compilation speed.
- Improvement path: Provide a build flag to optionally enable float64 support for users who need it.

**Pure PyTorch Fallback for Complex Matmul:**
- Problem: When CuPy is unavailable, complex matrix multiplication falls back to a manual real/imag decomposition that is slower than native PyTorch complex support (available since PyTorch 1.9+).
- Files: `torch_butterfly/complex_utils.py` lines 41-95
- Cause: Written for PyTorch 1.7 when complex backward was buggy. PyTorch has since fixed these issues.
- Improvement path: Remove the CuPy workaround and use native PyTorch complex operations, since the minimum requirement is already PyTorch >= 1.8.

## Fragile Areas

**C++ Extension Loading in __init__.py:**
- Files: `torch_butterfly/__init__.py` lines 8-11
- Why fragile: The package loads compiled C++ extensions at import time using `importlib.machinery.PathFinder`. If the extension is not compiled, the import fails entirely with an opaque error.
- Safe modification: Add a try/except around the extension loading with a clear error message pointing to `python setup.py install`.
- Test coverage: No test for graceful failure when extensions are missing.

**PyTorch Version-Specific Workarounds:**
- Files: `torch_butterfly/complex_utils.py` (lines 98-99: "Pytorch 1.7 doesn't support complex exp backward"), line 125 ("Pytorch 1.7 doesn't have indexing_backward for complex"), line 145 ("Pytorch 1.7 doesn't support complex reshape backward")
- Why fragile: Multiple custom autograd functions exist solely to work around PyTorch 1.7 bugs. Since the stated minimum is PyTorch >= 1.8, some of these may now be unnecessary, but removing them requires careful testing.
- Safe modification: Test each workaround against the minimum supported PyTorch version and remove if no longer needed.
- Test coverage: `tests/test_complex_utils.py` exists (60 lines) but coverage of edge cases is minimal.

**THCAtomics.cuh Usage (Deprecated PyTorch Header):**
- Files: `csrc/cuda/butterfly_cuda.cu` line 4
- Why fragile: `THC/THCAtomics.cuh` is from the legacy TH/THC C library in PyTorch which has been progressively removed. This header may not exist in future PyTorch versions.
- Safe modification: Replace with `<ATen/cuda/Atomic.cuh>` or equivalent modern ATen headers.
- Test coverage: Only tested implicitly through the test suite.

## Scaling Limits

**Power-of-2 Size Requirement:**
- Current capacity: Input/output sizes must be powers of 2 internally; non-power-of-2 sizes are padded.
- Limit: For very large non-power-of-2 inputs, padding waste can approach 50% (e.g., input size 513 gets padded to 1024).
- Scaling path: Documented as a known limitation. No easy fix given the butterfly structure.

**Single-Stack Memory:**
- Current capacity: When `out_size > n`, multiple stacks are used, each performing a full butterfly multiply.
- Limit: Memory usage scales linearly with `nstacks = ceil(out_size / n)`.
- Scaling path: Consider more memory-efficient approaches for very large output sizes.

## Dependencies at Risk

**NVIDIA Apex (Deprecated):**
- Risk: Apex mixed-precision training is superseded by PyTorch's native `torch.cuda.amp`. Apex is no longer actively maintained for new PyTorch versions.
- Impact: All ImageNet training scripts in `cnn/` depend on Apex. The old butterfly interface hard-fails without it.
- Migration plan: Replace `apex.amp` with `torch.cuda.amp.autocast` and `torch.cuda.amp.GradScaler`. Replace `apex.parallel.DistributedDataParallel` with `torch.nn.parallel.DistributedDataParallel`.
- Files: `butterfly/butterfly_multiply.py`, `cnn/imagenet_amp.py`, `cnn/imagenet_main.py`, `cnn/imagenet_finetune.py`, `cnn/teacher_covariance.py`, `cnn/imagenet/training.py`

**CuPy Optional Dependency:**
- Risk: Used as a performance optimization for complex matmul but likely unnecessary with modern PyTorch complex number support.
- Impact: Adds installation complexity. Silent performance degradation when missing (warning is commented out).
- Migration plan: Remove CuPy dependency entirely, rely on native PyTorch complex ops.
- Files: `torch_butterfly/complex_utils.py`

**Ray (Pinned to Old Version):**
- Risk: `requirements.txt` specifies `ray>=0.6.5`, but `convolution/docker/Dockerfile` pins `ray[tune]==1.0.1`. Ray's API has changed significantly across versions.
- Impact: Training scripts using Ray Tune may break with newer Ray versions.
- Migration plan: Update Ray usage to the modern API (2.x+) or pin a compatible version in requirements.
- Files: `requirements.txt`, `convolution/docker/Dockerfile`, `learning_transforms/tune.py`

**Outdated Docker Image:**
- Risk: Dockerfile uses `nvidia/cuda:10.1-cudnn7-runtime-ubuntu18.04` with PyTorch 1.7.0 and CUDA 10.1, all of which are end-of-life.
- Impact: Cannot build the Docker image with modern GPUs (Ampere+). Ubuntu 18.04 is past EOL.
- Migration plan: Update to CUDA 12.x, PyTorch 2.x, Ubuntu 22.04+.
- Files: `convolution/docker/Dockerfile`

## Missing Critical Features

**No CI/CD Pipeline:**
- Problem: No CI configuration files (GitHub Actions, CircleCI, Travis, etc.) detected.
- Blocks: No automated testing, no build verification on PRs, no way to catch regressions.

**No Type Checking:**
- Problem: No `mypy` or `pyright` configuration. Type hints are sparse and inconsistent.
- Blocks: Cannot catch type errors statically. The `ComplexLinear` bug (bare `weight` instead of `self.weight`) would have been caught.

**No Linting Configuration:**
- Problem: No `.flake8`, `.pylintrc`, `pyproject.toml` linting section, or `ruff.toml` found.
- Blocks: Code style is inconsistent across directories.

**Version Stuck at 0.0.0:**
- Problem: `setup.py` and `torch_butterfly/__init__.py` both hardcode version `0.0.0`.
- Blocks: Cannot distinguish installed versions or track compatibility.
- Files: `setup.py` line 62, `torch_butterfly/__init__.py` line 6

## Test Coverage Gaps

**No Tests for Experiment Scripts:**
- What's not tested: The entire `cnn/`, `learning_transforms/`, `transformer/`, `convolution/` directories have no automated tests.
- Files: `cnn/cifar_experiment.py`, `cnn/permuted_experiment.py`, `cnn/imagenet_amp.py`, `learning_transforms/tune.py`, etc.
- Risk: Training scripts could break silently with dependency updates.
- Priority: Low (these are research experiment scripts, not library code).

**No Tests for Old Butterfly Interface Against New:**
- What's not tested: No cross-validation between `butterfly/` and `torch_butterfly/` implementations.
- Files: `butterfly/butterfly.py` vs `torch_butterfly/butterfly.py`
- Risk: Behavioral differences between old and new interface go undetected.
- Priority: Medium (if old interface is still used by downstream code).

**ComplexLinear Untested:**
- What's not tested: `ComplexLinear` class has a bug in `reset_parameters` that indicates it has never been tested.
- Files: `torch_butterfly/complex_utils.py` lines 153-185
- Risk: Any user of `ComplexLinear` encounters a crash.
- Priority: High.

**Limited CUDA Testing:**
- What's not tested: Tests skip CUDA when not available (`if not torch.cuda.is_available()`). No CI means CUDA paths may not be regularly validated.
- Files: `tests/test_butterfly.py` line 26, similar patterns throughout `tests/`
- Risk: CUDA kernel bugs or compatibility issues go undetected.
- Priority: Medium.

---

*Concerns audit: 2026-04-02*
