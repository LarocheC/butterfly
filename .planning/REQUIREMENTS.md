# Requirements: torch_butterfly Build Modernization

**Defined:** 2026-04-02
**Core Value:** A single `uv pip install .` that just works — with CUDA support when available

## v1 Requirements

### Build System

- [ ] **BUILD-01**: Package uses pyproject.toml with `[build-system]` declaring torch, setuptools, ninja, wheel as build dependencies
- [ ] **BUILD-02**: Package metadata follows PEP 621 (`[project]` table with name, version, description, python-requires, etc.)
- [ ] **BUILD-03**: Package discovery excludes legacy `butterfly/` directory, only installs `torch_butterfly/`
- [ ] **BUILD-04**: MANIFEST.in includes `csrc/` source files so sdist contains C++/CUDA sources
- [ ] **BUILD-05**: Optional dependency groups defined for dev and test extras (`[project.optional-dependencies]`)
- [ ] **BUILD-06**: setup.py reduced to thin shim (only ext_modules and BuildExtension cmdclass)

### CUDA Compatibility

- [ ] **CUDA-01**: Hardcoded sm_35 CUDA architecture flag removed (broken on CUDA 12+)
- [ ] **CUDA-02**: Build auto-detects CUDA availability from torch and CUDA_HOME (existing behavior preserved and improved)
- [ ] **CUDA-03**: TORCH_CUDA_ARCH_LIST env var supported for user override of CUDA architecture targets
- [ ] **CUDA-04**: FORCE_CUDA and FORCE_CPU env vars preserved as manual overrides

### Extension Loading

- [ ] **EXT-01**: PathFinder-based extension loading in `__init__.py` replaced with `__file__`-relative .so discovery
- [ ] **EXT-02**: Editable installs (`uv pip install -e .`) load extensions correctly
- [ ] **EXT-03**: Deprecated RegisterOperators API in `csrc/version.cpp` migrated to TORCH_LIBRARY macro

### Install Experience

- [ ] **INST-01**: `uv pip install .` works from source checkout (non-editable)
- [ ] **INST-02**: `pip install .` works from source checkout (non-editable)
- [ ] **INST-03**: `uv pip install -e .` works for development (editable)
- [ ] **INST-04**: Install works without conda — pure pip/uv workflow
- [ ] **INST-05**: Python >=3.10, <4 enforced in metadata
- [ ] **INST-06**: PyTorch >=2.0 declared as runtime dependency

## v2 Requirements

### Distribution

- **DIST-01**: Pre-compiled wheels for common CUDA/Python version combinations
- **DIST-02**: CI matrix for automated wheel building
- **DIST-03**: Conda recipe for conda-forge distribution

### Extended Platform Support

- **PLAT-01**: ROCm (AMD GPU) support
- **PLAT-02**: Intel XPU support

## Out of Scope

| Feature | Reason |
|---------|--------|
| Pre-compiled wheel distribution | Library value unproven, packaging effort too high |
| Legacy butterfly/ package modernization | Focus on torch_butterfly/ only |
| Experiment directory updates (cnn/, convolution/, etc.) | Not part of core package |
| C++/CUDA kernel code changes | Only touching build plumbing |
| Version single-sourcing / bump from 0.0.0 | Nice-to-have, not core to install fix |
| C++ rebuild workflow docs | Can be added later |
| UV-specific documentation | Can be added later |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BUILD-01 | Phase 1 | Pending |
| BUILD-02 | Phase 1 | Pending |
| BUILD-03 | Phase 1 | Pending |
| BUILD-04 | Phase 1 | Pending |
| BUILD-05 | Phase 1 | Pending |
| BUILD-06 | Phase 1 | Pending |
| CUDA-01 | Phase 1 | Pending |
| CUDA-02 | Phase 1 | Pending |
| CUDA-03 | Phase 1 | Pending |
| CUDA-04 | Phase 1 | Pending |
| EXT-01 | Phase 2 | Pending |
| EXT-02 | Phase 2 | Pending |
| EXT-03 | Phase 2 | Pending |
| INST-01 | Phase 1 | Pending |
| INST-02 | Phase 1 | Pending |
| INST-03 | Phase 2 | Pending |
| INST-04 | Phase 1 | Pending |
| INST-05 | Phase 1 | Pending |
| INST-06 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0

---
*Requirements defined: 2026-04-02*
*Last updated: 2026-04-02 after initial definition*
