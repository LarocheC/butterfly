# Roadmap: torch_butterfly Build Modernization

## Overview

Modernize torch_butterfly from a broken setup.py-only build to a pyproject.toml-based package that installs cleanly with `uv pip install .` (and pip). Phase 1 creates the entire build system foundation including CUDA compatibility fixes. Phase 2 fixes runtime extension loading for editable installs and modernizes deprecated C++ APIs. Two phases because the work splits cleanly at a build-time vs. runtime boundary.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Build System Foundation** - pyproject.toml, PEP 621 metadata, CUDA arch fix, and working non-editable install (completed 2026-04-02)
- [ ] **Phase 2: Extension Loading and Editable Installs** - Fix runtime .so discovery, modernize C++ registration, enable editable installs

## Phase Details

### Phase 1: Build System Foundation
**Goal**: Users can install torch_butterfly from source with `uv pip install .` or `pip install .` and get a working package with CUDA support
**Depends on**: Nothing (first phase)
**Requirements**: BUILD-01, BUILD-02, BUILD-03, BUILD-04, BUILD-05, BUILD-06, CUDA-01, CUDA-02, CUDA-03, CUDA-04, INST-01, INST-02, INST-04, INST-05, INST-06
**Success Criteria** (what must be TRUE):
  1. Running `uv pip install .` in a fresh virtual environment succeeds without errors
  2. Running `pip install .` in a fresh virtual environment succeeds without errors
  3. After install, `import torch_butterfly` works and CUDA extensions load on a CUDA-capable machine
  4. The build succeeds without conda -- only pip/uv and a system CUDA toolkit are needed
  5. Setting `FORCE_CUDA=1` or `FORCE_CPU=1` controls whether CUDA extensions are compiled
**Plans**: TBD

Plans:
- [x] 01-01: TBD
- [ ] 01-02: TBD

### Phase 2: Extension Loading and Editable Installs
**Goal**: Editable installs work reliably and the C++ extension loading mechanism is robust across install modes
**Depends on**: Phase 1
**Requirements**: EXT-01, EXT-02, EXT-03, INST-03
**Success Criteria** (what must be TRUE):
  1. Running `uv pip install -e .` succeeds and `import torch_butterfly` loads the compiled extensions
  2. After modifying Python source in an editable install, changes are reflected immediately without reinstall
  3. The deprecated RegisterOperators API in version.cpp is replaced with TORCH_LIBRARY macro
**Plans**: TBD

Plans:
- [ ] 02-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Build System Foundation | 1/1 | Complete   | 2026-04-02 |
| 2. Extension Loading and Editable Installs | 0/0 | Not started | - |
