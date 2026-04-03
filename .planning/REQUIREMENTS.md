# Requirements: torch_butterfly

**Defined:** 2026-04-02
**Core Value:** A single `uv pip install .` that just works — with CUDA support when available

## v1.0 Requirements (Complete)

### Build System

- [x] **BUILD-01**: Package uses pyproject.toml with `[build-system]` declaring torch, setuptools, ninja, wheel as build dependencies
- [x] **BUILD-02**: Package metadata follows PEP 621 (`[project]` table with name, version, description, python-requires, etc.)
- [x] **BUILD-03**: Package discovery excludes legacy `butterfly/` directory, only installs `torch_butterfly/`
- [x] **BUILD-04**: MANIFEST.in includes `csrc/` source files so sdist contains C++/CUDA sources
- [x] **BUILD-05**: Optional dependency groups defined for dev and test extras (`[project.optional-dependencies]`)
- [x] **BUILD-06**: setup.py reduced to thin shim (only ext_modules and BuildExtension cmdclass)

### CUDA Compatibility

- [x] **CUDA-01**: Hardcoded sm_35 CUDA architecture flag removed (broken on CUDA 12+)
- [x] **CUDA-02**: Build auto-detects CUDA availability from torch and CUDA_HOME (existing behavior preserved and improved)
- [x] **CUDA-03**: TORCH_CUDA_ARCH_LIST env var supported for user override of CUDA architecture targets
- [x] **CUDA-04**: FORCE_CUDA and FORCE_CPU env vars preserved as manual overrides

### Extension Loading

- [x] **EXT-01**: PathFinder-based extension loading in `__init__.py` replaced with `__file__`-relative .so discovery
- [x] **EXT-02**: Editable installs (`uv pip install -e .`) load extensions correctly
- [x] **EXT-03**: Deprecated RegisterOperators API in `csrc/version.cpp` migrated to TORCH_LIBRARY macro

### Install Experience

- [x] **INST-01**: `uv pip install .` works from source checkout (non-editable)
- [x] **INST-02**: `pip install .` works from source checkout (non-editable)
- [x] **INST-03**: `uv pip install -e .` works for development (editable)
- [x] **INST-04**: Install works without conda — pure pip/uv workflow
- [x] **INST-05**: Python >=3.10, <4 enforced in metadata
- [x] **INST-06**: PyTorch >=2.0 declared as runtime dependency

## v1.1 Requirements

### Legacy Removal

- [x] **LEGACY-01**: Remove `butterfly/` package (old implementation replaced by `torch_butterfly/`)
- [x] **LEGACY-02**: Remove `tests_old/` directory (tests for old `butterfly/` package)
- [x] **LEGACY-03**: Remove `learning_transforms/` directory (Cython experiments)
- [x] **LEGACY-04**: Remove `fairseq/` git submodule and `.gitmodules` reference

### Experiment Removal

- [x] **EXP-01**: Remove `cnn/` directory (CIFAR/ImageNet experiment scripts)
- [x] **EXP-02**: Remove `convolution/` directory (Lightning/Hydra/Ray experiments)
- [x] **EXP-03**: Remove `transformer/` directory (dynamic conv experiments)
- [x] **EXP-04**: Remove `gumbel-sinkhorn/` directory (sorting network experiments)

### Cleanup

- [x] **CLEAN-01**: Remove `data/` directory (dataset files)
- [x] **CLEAN-02**: Remove `ray_template.sh`
- [x] **CLEAN-03**: Remove `build/` and `torch_butterfly.egg-info/` from tracking and add to `.gitignore`
- [x] **CLEAN-04**: All existing tests in `tests/` pass after cleanup

## Future Requirements

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
| Rewriting or updating experiment code | Removing, not fixing |
| C++/CUDA kernel code changes | Only touching build plumbing |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BUILD-01 | Phase 1 | Complete |
| BUILD-02 | Phase 1 | Complete |
| BUILD-03 | Phase 1 | Complete |
| BUILD-04 | Phase 1 | Complete |
| BUILD-05 | Phase 1 | Complete |
| BUILD-06 | Phase 1 | Complete |
| CUDA-01 | Phase 1 | Complete |
| CUDA-02 | Phase 1 | Complete |
| CUDA-03 | Phase 1 | Complete |
| CUDA-04 | Phase 1 | Complete |
| EXT-01 | Phase 2 | Complete |
| EXT-02 | Phase 2 | Complete |
| EXT-03 | Phase 2 | Complete |
| INST-01 | Phase 1 | Complete |
| INST-02 | Phase 1 | Complete |
| INST-03 | Phase 2 | Complete |
| INST-04 | Phase 1 | Complete |
| INST-05 | Phase 1 | Complete |
| INST-06 | Phase 1 | Complete |
| LEGACY-01 | Phase 3 | Complete |
| LEGACY-02 | Phase 3 | Complete |
| LEGACY-03 | Phase 3 | Complete |
| LEGACY-04 | Phase 3 | Complete |
| EXP-01 | Phase 3 | Complete |
| EXP-02 | Phase 3 | Complete |
| EXP-03 | Phase 3 | Complete |
| EXP-04 | Phase 3 | Complete |
| CLEAN-01 | Phase 3 | Complete |
| CLEAN-02 | Phase 3 | Complete |
| CLEAN-03 | Phase 3 | Complete |
| CLEAN-04 | Phase 3 | Complete |

**Coverage:**
- v1.0 requirements: 19 total, 19 complete
- v1.1 requirements: 12 total, 0 complete, 12 mapped to Phase 3
- Unmapped: 0

---
*Requirements defined: 2026-04-02*
*Last updated: 2026-04-03 -- v1.1 roadmap created, all requirements mapped to Phase 3*
