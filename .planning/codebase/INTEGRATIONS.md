# External Integrations

**Analysis Date:** 2026-04-02

## APIs & External Services

**Experiment Tracking:**
- Weights & Biases (wandb) - Experiment logging and metric tracking
  - SDK/Client: `wandb==0.9.7`
  - Project: `butterflynas` (configured in `convolution/cfg/config.yaml`)
  - Note: wandb >=0.10.0 causes permission errors reading `~/.config` (documented in `convolution/docker/Dockerfile`)

**Distributed Computing:**
- Ray - Distributed hyperparameter tuning and training orchestration
  - SDK/Client: `ray[tune]>=1.0.0`
  - Configuration: `convolution/cfg/runner/ray.yaml`
  - Cluster management: `ray_template.sh` (head node + SSH to workers)
  - Used in: `cnn/cifar_experiment.py`, `cnn/distill_experiment.py`, `cnn/distill_cov_experiment.py`, `cnn/permuted_experiment.py`, `convolution/ray_runner.py`

## Data Storage

**Databases:**
- None - No database integration

**File Storage:**
- Local filesystem only
- Training data: `data/tiny-imagenet-200/` (Tiny ImageNet dataset stored locally)
- Results: `convolution/cfg/runner/ray.yaml` specifies `result_dir: ./results`
- Supports NFS for shared storage across Ray workers (`nfs: True` in ray config)

**Caching:**
- None

## Datasets

**Image Classification:**
- CIFAR-10 - Configured in `convolution/cfg/dataset/cifar10.yaml`, loaded via `torchvision`
- CIFAR-100 - Configured in `convolution/cfg/dataset/cifar100.yaml`, loaded via `torchvision`
- Tiny ImageNet-200 - Stored at `data/tiny-imagenet-200/`
- ImageNet - Full ImageNet experiments in `cnn/imagenet/`

## Authentication & Identity

**Auth Provider:**
- Not applicable - Research library, no auth system

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- stdout/stderr with tee capture (`convolution/tee.py` - `StdoutTee`, `StderrTee`)
- PyTorch Lightning built-in logging
- wandb for experiment metrics

## CI/CD & Deployment

**Hosting:**
- Not deployed as a service; research code run on GPU clusters

**CI Pipeline:**
- None detected

**Docker:**
- `convolution/docker/Dockerfile` - Based on `nvidia/cuda:10.1-cudnn7-runtime-ubuntu18.04`
  - Installs: Miniconda, Python 3.8, PyTorch 1.7.0, CUDA toolkit 10.1
  - Installs: pytorch-lightning, ray[tune], hydra-core, wandb, scikit-learn

## Environment Configuration

**Required env vars:**
- None strictly required for core library usage
- `FORCE_CUDA` / `FORCE_CPU` - Optional build-time overrides in `setup.py`
- `NVCC_FLAGS` - Optional custom CUDA compiler flags
- `PYTHONPATH` - Must include project root for Ray worker processes
- wandb credentials (if using experiment tracking)

**Secrets location:**
- No secrets management; wandb auth handled by wandb CLI login

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- wandb API calls for metric logging (when enabled)

## PyTorch Custom Operator Integration

**torch.ops registration:**
- The C++ extension registers custom operators under the `torch_butterfly` namespace via `TORCH_LIBRARY` macro in `csrc/butterfly.cpp`
- Operators are callable as `torch.ops.torch_butterfly.butterfly_multiply_fw(...)` etc.
- JIT-scripted Python wrappers in `torch_butterfly/multiply.py` using `@torch.jit.script`
- Version check operator: `torch.ops.torch_butterfly.cuda_version()` in `csrc/version.cpp`

## Third-Party Library Roles

| Library | Role | Used In |
|---------|------|---------|
| `torch` | Core tensor ops, autograd, nn.Module, JIT, C++ extensions | Everywhere |
| `numpy` | Array manipulation, test utilities | Throughout codebase |
| `scipy` | Hungarian algorithm (`linear_sum_assignment`) | `gumbel-sinkhorn/my_sinkhorn_ops.py` |
| `pytorch-lightning` | Training loop, callbacks, checkpointing | `convolution/` |
| `ray[tune]` | Distributed HPO, AsyncHyperBand scheduler | `cnn/`, `convolution/` |
| `hydra-core` | YAML config composition, CLI overrides | `convolution/train.py` |
| `wandb` | Experiment tracking, metric visualization | `convolution/` |
| `torchvision` | Image datasets (CIFAR-10/100), transforms | `cnn/`, `convolution/` |
| `munch` | Dict-to-attribute-access objects | `convolution/ray_runner.py` |
| `scikit-learn` | Utility functions | `cnn/` experiments |
| `Cython` | Build C extension for matrix multiply | `learning_transforms/setup.py` |

---

*Integration audit: 2026-04-02*
