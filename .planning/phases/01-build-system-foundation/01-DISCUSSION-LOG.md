# Phase 1: Build System Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 01-build-system-foundation
**Areas discussed:** CUDA arch targets, Dependency scope, Build isolation, Legacy cleanup

---

## CUDA Arch Targets

| Option | Description | Selected |
|--------|-------------|----------|
| sm_70+ | Volta, Turing, Ampere, Ada, Hopper. Covers V100, RTX 20/30/40/50, A100, H100. | |
| sm_80+ | Ampere and newer only. Covers A100, RTX 30/40/50, H100. | |
| Auto-detect only | No default arch list. Let nvcc detect the current GPU. | |

**User's choice:** sm_70+ (Recommended)

### PTX Forward Compatibility

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, include PTX | Adds -gencode for highest arch with +PTX. Works on future GPUs. | |
| No PTX | Only compile for specific arch targets. | |

**User's choice:** Yes, include PTX (Recommended)

### NVCC_FLAGS Env Var

| Option | Description | Selected |
|--------|-------------|----------|
| Replace with TORCH_CUDA_ARCH_LIST | Standard PyTorch convention. Drop NVCC_FLAGS. | |
| Keep both | Support TORCH_CUDA_ARCH_LIST for arch and NVCC_FLAGS for other flags | |
| You decide | Claude's discretion | |

**User's choice:** You decide (Claude's discretion)

### Specific Architecture List

| Option | Description | Selected |
|--------|-------------|----------|
| 7.0 8.0 9.0+PTX | Covers Volta, Ampere, Hopper. PTX covers Ada and Blackwell. | |
| 7.0 7.5 8.0 8.6 8.9 9.0+PTX | Adds Turing, Ampere consumer, Ada explicitly. | |
| Let PyTorch decide | Use torch.cuda.get_arch_list() at build time. | |

**User's choice:** 7.0 8.0 9.0+PTX (Recommended)

---

## Dependency Scope

| Option | Description | Selected |
|--------|-------------|----------|
| torch + numpy only | Minimal. Only imports in torch_butterfly/ core. | |
| torch only | numpy comes with torch anyway. | |
| You decide | Claude's discretion | |

**User's choice:** torch + numpy only (Recommended)

### Optional Dependency Groups

| Option | Description | Selected |
|--------|-------------|----------|
| dev + test | Standard split. | |
| Just test | Single test group. | |
| You decide | Claude's discretion | |

**User's choice:** dev + test (Recommended)

---

## Build Isolation

| Option | Description | Selected |
|--------|-------------|----------|
| Document both paths | Default: uv pip install . works. Advanced: --no-build-isolation for exact CUDA match. | |
| Require --no-build-isolation | Don't put torch in build-requires. Simpler but breaks 'just works' goal. | |
| You decide | Claude's discretion | |

**User's choice:** Document both paths (Recommended)

---

## Legacy Cleanup

### requirements.txt

| Option | Description | Selected |
|--------|-------------|----------|
| Delete it | pyproject.toml is source of truth. | |
| Update it | Keep as convenience file. | |
| Leave as-is | For experiment scripts, not core package. | |

**User's choice:** Delete it (Recommended)

### Dockerfile and README

| Option | Description | Selected |
|--------|-------------|----------|
| Leave for now | Out of scope for Phase 1. | |
| Delete Dockerfile | Completely stale (CUDA 10.1, Ubuntu 18.04). | |
| Update both | Modern install instructions. | |

**User's choice:** Leave for now

---

## Claude's Discretion

- NVCC_FLAGS env var handling (keep, replace, or simplify)
- Exact dev vs test optional dependency group contents
- Whether to add -O3 optimization flag
- MANIFEST.in exact contents
- setuptools version pin

## Deferred Ideas

None — discussion stayed within phase scope
