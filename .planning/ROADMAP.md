# Roadmap: torch_butterfly Build Modernization

## Milestones

- v1.0 Build System Modernization - Phases 1-2 (shipped 2026-04-02)
- v1.1 Repository Cleanup - Phase 3 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

<details>
<summary>v1.0 Build System Modernization (Phases 1-2) - SHIPPED 2026-04-02</summary>

- [x] **Phase 1: Build System Foundation** - pyproject.toml, PEP 621 metadata, CUDA arch fix, and working non-editable install (completed 2026-04-02)
- [x] **Phase 2: Extension Loading and Editable Installs** - Fix runtime .so discovery, modernize C++ registration, enable editable installs (completed 2026-04-02)

</details>

### v1.1 Repository Cleanup

- [ ] **Phase 3: Strip and Verify** - Remove all legacy code, experiments, and dead assets; verify tests pass

## Phase Details

<details>
<summary>v1.0 Build System Modernization (Phases 1-2) - SHIPPED 2026-04-02</summary>

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
**Plans**: 1 plan

Plans:
- [x] 01-01-PLAN.md -- pyproject.toml, setup.py shim, MANIFEST.in, CUDA arch fix

### Phase 2: Extension Loading and Editable Installs
**Goal**: Editable installs work reliably and the C++ extension loading mechanism is robust across install modes
**Depends on**: Phase 1
**Requirements**: EXT-01, EXT-02, EXT-03, INST-03
**Success Criteria** (what must be TRUE):
  1. Running `uv pip install -e .` succeeds and `import torch_butterfly` loads the compiled extensions
  2. After modifying Python source in an editable install, changes are reflected immediately without reinstall
  3. The deprecated RegisterOperators API in version.cpp is replaced with TORCH_LIBRARY macro
**Plans**: 1 plan

Plans:
- [x] 02-01-PLAN.md -- Fix extension loading, modernize version.cpp, soften CUDA check

</details>

### Phase 3: Strip and Verify
**Goal**: Repository contains only the core torch_butterfly library, build files, and tests -- all legacy and experiment code removed
**Depends on**: Phase 2
**Requirements**: LEGACY-01, LEGACY-02, LEGACY-03, LEGACY-04, EXP-01, EXP-02, EXP-03, EXP-04, CLEAN-01, CLEAN-02, CLEAN-03, CLEAN-04
**Success Criteria** (what must be TRUE):
  1. The directories `butterfly/`, `tests_old/`, `learning_transforms/`, `cnn/`, `convolution/`, `transformer/`, `gumbel-sinkhorn/`, and `data/` do not exist in the repository
  2. The files `ray_template.sh` and `.gitmodules` do not exist, and the `fairseq/` submodule is fully removed
  3. `build/` and `torch_butterfly.egg-info/` are listed in `.gitignore` and not tracked by git
  4. `pytest tests/` passes with all tests green after all removals
**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md -- Remove legacy dirs, experiment dirs, submodule, and dead files
- [x] 03-02-PLAN.md -- Clean .gitignore, modernize README, verify tests pass

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Build System Foundation | v1.0 | 1/1 | Complete | 2026-04-02 |
| 2. Extension Loading | v1.0 | 1/1 | Complete | 2026-04-02 |
| 3. Strip and Verify | v1.1 | 0/2 | Not started | - |
