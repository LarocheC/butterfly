---
status: complete
phase: 02-extension-loading-and-editable-installs
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md, 01-03-SUMMARY.md, 02-01-SUMMARY.md]
started: 2026-04-02T20:30:00Z
updated: 2026-04-02T20:45:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Non-editable install with uv
expected: `FORCE_CPU=1 uv pip install . --no-build-isolation` exits 0 in a clean venv with torch pre-installed. No configuration errors.
result: pass

### 2. Import and forward pass (non-editable)
expected: After non-editable install, `cd /tmp && python -c "import torch_butterfly; import torch; y = torch_butterfly.Butterfly(8,8)(torch.randn(2,8)); print(y.shape)"` prints `torch.Size([2, 8])` with no errors.
result: pass

### 3. Editable install with uv
expected: `FORCE_CPU=1 uv pip install -e . --no-build-isolation` exits 0 in a clean venv. Extensions compile and install alongside source tree.
result: pass

### 4. Import and forward pass (editable)
expected: After editable install, `import torch_butterfly; import torch; y = torch_butterfly.Butterfly(8,8)(torch.randn(2,8)); print(y.shape)` prints `torch.Size([2, 8])`. Special transforms work: `torch_butterfly.special.fft(8)` returns an nn.Sequential.
result: pass

### 5. CUDA version mismatch produces warning not error
expected: When built with FORCE_CPU=1 but torch reports CUDA available, importing torch_butterfly logs a UserWarning about version mismatch instead of crashing with RuntimeError.
result: skipped
reason: CPU-only machine — no CUDA mismatch to trigger

### 6. No conda required
expected: The entire install and test process above uses only pip/uv. No conda commands needed at any step.
result: pass

## Summary

total: 6
passed: 5
issues: 0
pending: 0
skipped: 1
blocked: 0

## Gaps

[none]
