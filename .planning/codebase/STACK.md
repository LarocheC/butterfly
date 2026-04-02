# Technology Stack

**Analysis Date:** 2026-04-02

## Languages

**Primary:**
- Python >=3.6 - All training scripts, model definitions, library code
- C++ (C++14) - Custom PyTorch operator implementations in `csrc/`

**Secondary:**
- CUDA C++ - GPU kernel implementations in `csrc/cuda/`
- Cython - Legacy matrix multiplication extension in `learning_transforms/ABCD_mult.pyx`

## Runtime

**Environment:**
- Python >=3.6 (Dockerfile uses 3.8)
- NVIDIA CUDA 10.1 (per Dockerfile base image `nvidia/cuda:10.1-cudnn7-runtime-ubuntu18.04`)
- cuDNN 7

**Package Manager:**
- pip (primary)
- conda (used in Docker and development environment setup)
- Lockfile: not present

## Frameworks

**Core:**
- PyTorch >=1.8 - Deep learning framework, the foundation for the entire project
- PyTorch Lightning >=1.0.3 - Training loop abstraction used in `convolution/` experiments

**Configuration:**
- Hydra >=1.0.0 - Configuration management for `convolution/` training scripts
- OmegaConf - Config resolution (used via Hydra)

**Distributed Training:**
- Ray >=0.6.5 (pinned to 1.0.1 in Docker) - Distributed hyperparameter tuning and training
- Ray Tune - Hyperparameter search with `AsyncHyperBandScheduler`

**Build/Dev:**
- setuptools - Package building via `setup.py`
- torch.utils.cpp_extension (CppExtension, CUDAExtension) - Compiles C++/CUDA extensions
- ninja - Build system used by PyTorch's BuildExtension
- Cython - Builds `learning_transforms/ABCD_mult.pyx`

## Key Dependencies

**Critical:**
- `torch` (>=1.8) - Core tensor operations, autograd, nn.Module base, JIT scripting, custom C++ operator dispatch
- `numpy` - Numerical operations throughout the codebase
- `scipy` - Used in `gumbel-sinkhorn/my_sinkhorn_ops.py` for `linear_sum_assignment`

**Training Infrastructure:**
- `pytorch-lightning` (>=1.0.3) - Training loop, callbacks, logging in `convolution/`
- `pytorch-lightning-bolts` (>=0.2.5) - Additional utilities for Lightning
- `ray[tune]` (>=1.0.0) - Distributed experiment execution in `cnn/` and `convolution/`
- `hydra-core` (>=1.0.0) - YAML-based configuration in `convolution/`
- `munch` - Dict-to-object utility in `convolution/ray_runner.py`

**Experiment Tracking:**
- `wandb` (==0.9.7 in Docker) - Weights & Biases experiment logging (referenced in `convolution/cfg/config.yaml` project: `butterflynas`)

**Other:**
- `scikit-learn` - Referenced in Docker install, utility functions
- `torchvision` - Image datasets and transforms for CNN experiments
- `matplotlib` (3.0.2) - Visualization in `gumbel-sinkhorn/`

## Configuration

**Environment:**
- `FORCE_CUDA=1` / `FORCE_CPU=1` - Override CUDA detection in `setup.py`
- `NVCC_FLAGS` - Custom NVCC compiler flags in `setup.py`
- `BUILD_DOCS=1` - Skip building C++ extensions in `setup.py`
- `PYTHONPATH` - Must include project root and `fairseq/` for Ray workers

**Build:**
- `setup.py` - Main package build (torch_butterfly with C++/CUDA extensions)
- `butterfly/factor_multiply/setup.py` - Legacy CUDA extension build
- `butterfly/factor_multiply_fast/setup.py` - Legacy fast CUDA extension build
- `learning_transforms/setup.py` - Cython extension build
- `convolution/cfg/config.yaml` - Hydra root config for convolution experiments
- `convolution/cfg/` - Full Hydra config tree (model, optimizer, dataset, runner, lr_scheduler)

## C++/CUDA Extensions

**Main Extension (`torch_butterfly`):**
- Source: `csrc/butterfly.cpp` (dispatch), `csrc/cpu/butterfly_cpu.cpp`, `csrc/cuda/butterfly_cuda.cu`
- Registers custom ops via `TORCH_LIBRARY(torch_butterfly, m)`:
  - `butterfly_multiply_fw` - Forward pass
  - `butterfly_multiply_bw` - Backward pass
  - `butterfly_multiply` - Combined with autograd
- CUDA architecture: sm_35 minimum
- Loaded at runtime via `torch.ops.load_library()` in `torch_butterfly/__init__.py`

**Legacy Extensions:**
- `butterfly/factor_multiply/` - Factor multiply CUDA extension (sm_70 for V100)
- `butterfly/factor_multiply_fast/` - Fast butterfly multiply CUDA extension (sm_30 minimum)

## Platform Requirements

**Development:**
- Linux (Ubuntu 18.04 in Docker)
- NVIDIA GPU with CUDA support (optional, CPU fallback exists)
- CUDA toolkit 10.1+ with cuDNN
- C++ compiler supporting C++14
- conda or pip

**Production:**
- Same as development; this is a research library, not a deployed service
- GPU strongly recommended for practical performance

---

*Stack analysis: 2026-04-02*
