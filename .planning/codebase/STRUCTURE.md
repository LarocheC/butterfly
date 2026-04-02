# Codebase Structure

**Analysis Date:** 2026-04-02

## Directory Layout

```
butterfly/                          # Project root (repo name)
├── torch_butterfly/                # NEW core package (installed via setup.py)
│   ├── __init__.py                 # Package init, loads native libs, exports public API
│   ├── butterfly.py                # Butterfly, ButterflyUnitary, ButterflyBmm nn.Modules
│   ├── butterfly_base4.py          # ButterflyBase4 - fused base-4 variant
│   ├── multiply.py                 # Python wrappers for native butterfly_multiply ops
│   ├── multiply_base4.py           # Base-4 multiply (pure PyTorch) + base2-to-base4 conversion
│   ├── special.py                  # Factory functions: fft, ifft, dct, dst, hadamard, circulant, conv1d, etc.
│   ├── combine.py                  # Composition: diagonal_butterfly, butterfly_product, kronecker, TensorProduct
│   ├── permutation.py              # FixedPermutation, bitreversal, wavelet permutation, perm2butterfly
│   ├── diagonal.py                 # Diagonal nn.Module
│   ├── complex_utils.py            # Complex number utilities, cupy bridge, custom autograd
│   ├── benchmark_utils.py          # CUDA benchmark timing helpers
│   └── input_padding_benchmark.py  # Benchmark script for input padding
├── csrc/                           # C++/CUDA native extensions (new interface)
│   ├── butterfly.cpp               # Main dispatch + autograd wrapper + TORCH_LIBRARY registration
│   ├── version.cpp                 # CUDA version query op
│   ├── cpu/
│   │   ├── butterfly_cpu.h         # CPU forward/backward declarations
│   │   └── butterfly_cpu.cpp       # CPU butterfly multiply implementation
│   └── cuda/
│       ├── butterfly_cuda.h        # CUDA forward/backward declarations
│       ├── butterfly_cuda.cu       # CUDA butterfly multiply kernels
│       ├── complex_utils.cuh       # CUDA complex number helpers
│       └── map.h                   # CUDA map utility
├── butterfly/                      # OLD core package (legacy interface, being replaced)
│   ├── __init__.py                 # Exports old Butterfly class
│   ├── butterfly.py                # Old Butterfly nn.Module
│   ├── butterfly_multiply.py       # Old multiply with C++ and pure-PyTorch paths
│   ├── complex_utils.py            # Old complex utilities
│   ├── permutation.py              # Old permutation utilities
│   ├── permutation_multiply.py     # Old permutation multiply
│   ├── utils.py                    # Old utility functions
│   ├── benchmark.py                # Old benchmarks
│   ├── benchmark_linear.py         # Linear layer benchmarks
│   ├── factor_multiply/            # Old C++ extension (separate setup.py)
│   │   ├── setup.py
│   │   ├── factor_multiply.cpp
│   │   └── factor_multiply_cuda.cu
│   └── factor_multiply_fast/       # Old fast C++ extension (separate setup.py)
│       ├── setup.py
│       ├── butterfly_multiply.cpp
│       ├── butterfly_multiply_cuda.cu
│       └── map.h
├── tests/                          # Tests for new torch_butterfly package
│   ├── test_butterfly.py           # Core butterfly multiply tests
│   ├── test_butterfly_base4.py     # Base-4 variant tests
│   ├── test_combine.py             # Composition function tests
│   ├── test_complex_utils.py       # Complex utility tests
│   ├── test_multiply.py            # Multiply function tests
│   ├── test_multiply_base4.py      # Base-4 multiply tests
│   ├── test_permutation.py         # Permutation tests
│   └── test_special.py             # Special transform tests (FFT, DCT, etc.)
├── tests_old/                      # Tests for legacy butterfly package
│   ├── test_butterfly.py
│   ├── test_butterfly_multiply.py
│   ├── test_permutation.py
│   └── test_permutation_multiply.py
├── learning_transforms/            # Experiment: learning structured linear transforms
│   ├── __init__.py
│   ├── learning_fft.py             # Learn FFT via butterfly factorization
│   ├── learning_transforms.py      # General transform learning
│   ├── learning_circulant.py       # Learn circulant transforms
│   ├── learning_hadamard.py        # Learn Hadamard transforms
│   ├── learning_legendre.py        # Learn Legendre transforms
│   ├── learning_vandermonde.py     # Learn Vandermonde transforms
│   ├── target_matrix.py            # Target matrix generation
│   ├── training.py                 # Training loop
│   ├── ops.py                      # Operations
│   ├── butterfly_factor.py         # Factor utilities
│   ├── permutation_factor.py       # Permutation factor utilities
│   ├── baselines.py                # Baseline comparisons
│   ├── semantic_loss.py            # Loss functions
│   ├── tune.py                     # Hyperparameter tuning (uses Ray)
│   ├── profile.py                  # Profiling
│   ├── inference.py                # Inference benchmarks
│   ├── speed_test.py               # Speed testing
│   ├── run_exp.sh                  # Shell script to run experiments
│   └── old/                        # Older experiment code
├── cnn/                            # Experiment: CNN with butterfly layers
│   ├── cifar_experiment.py         # CIFAR training with butterfly layers
│   ├── imagenet_experiment.py      # ImageNet training
│   ├── imagenet_finetune.py        # ImageNet fine-tuning
│   ├── imagenet_model_surgery.py   # Replace layers with butterfly layers
│   ├── permuted_experiment.py      # Permuted experiments
│   ├── distill_experiment.py       # Knowledge distillation
│   ├── distill_cov_experiment.py   # Covariance distillation
│   ├── teacher.py                  # Teacher model for distillation
│   ├── models/                     # CNN model definitions
│   │   ├── __init__.py
│   │   ├── butterfly_conv.py       # Butterfly convolution layer
│   │   ├── circulant1x1conv.py     # Circulant 1x1 convolution
│   │   ├── toeplitzlike1x1conv.py  # Toeplitz-like 1x1 convolution
│   │   ├── resnet.py               # ResNet variants
│   │   ├── resnet_imagenet.py      # ResNet for ImageNet
│   │   ├── mobilenet.py            # MobileNet
│   │   ├── shufflenet.py           # ShuffleNet
│   │   └── ...                     # Other CNN architectures
│   └── imagenet/                   # ImageNet utilities
├── convolution/                    # Experiment: butterfly convolution (newer, uses Hydra)
│   ├── train.py                    # Training entry point
│   ├── tasks.py                    # Task definitions
│   ├── pl_runner.py                # PyTorch Lightning runner
│   ├── ray_runner.py               # Ray runner
│   ├── lr_schedulers.py            # Learning rate schedulers
│   ├── utils.py                    # Utilities
│   ├── models/                     # Model definitions
│   │   ├── __init__.py
│   │   ├── butterflenet.py         # ButterfleNet model
│   │   ├── cnn5_butterfly.py       # CNN5 with butterfly
│   │   ├── cnn5.py                 # CNN5 baseline
│   │   ├── resnet_cifar.py         # ResNet for CIFAR
│   │   ├── resnet.py               # ResNet
│   │   ├── lenet.py                # LeNet
│   │   ├── kops.py                 # Kaleidoscope operations
│   │   └── lops.py                 # Linear operations
│   ├── datamodules/                # Data loading
│   │   ├── __init__.py
│   │   └── cifar.py
│   ├── cfg/                        # Hydra configuration
│   │   ├── dataset/
│   │   ├── model/
│   │   ├── optimizer/
│   │   ├── lr_scheduler/
│   │   └── runner/
│   ├── scripts/                    # Run scripts
│   ├── docker/                     # Docker configs
│   └── requirements.txt
├── transformer/                    # Experiment: transformer with butterfly layers
│   ├── dynamic_conv_experiment.py  # Dynamic convolution experiment
│   └── dynamic_conv_compression.sh # Compression shell script
├── fairseq/                        # Empty directory (likely a git submodule placeholder)
├── gumbel-sinkhorn/                # Experiment: Gumbel-Sinkhorn network
│   ├── my_sinkhorn_ops.py          # Sinkhorn operations
│   ├── my_sorting_model.py         # Sorting model
│   ├── my_sorting_train.py         # Training script
│   ├── my_sinkhorn_eval.py         # Evaluation
│   └── trained_model.pkl           # Pre-trained weights
├── data/                           # Data directory
│   └── tiny-imagenet-200/          # Tiny ImageNet dataset
├── setup.py                        # Package installer (compiles csrc/, installs torch_butterfly)
├── requirements.txt                # python>=3.6, pytorch>=1.8, ray>=0.6.5, numpy
├── README.md                       # Project documentation
├── LICENSE                         # Apache license
├── ray_template.sh                 # Ray cluster template
├── .gitmodules                     # Git submodules config
└── .gitignore
```

## Directory Purposes

**`torch_butterfly/`:**
- Purpose: The primary installable Python package providing butterfly matrix operations
- Contains: nn.Module classes, Python multiply wrappers, special transform factories, composition utilities
- Key files: `butterfly.py` (main module), `special.py` (transform constructors), `multiply.py` (kernel bridge)

**`csrc/`:**
- Purpose: C++/CUDA native extensions compiled via `setup.py`
- Contains: Dispatch code, CPU implementation, CUDA kernels
- Key files: `butterfly.cpp` (autograd + op registration), `cuda/butterfly_cuda.cu` (GPU kernels, ~37K lines)

**`butterfly/`:**
- Purpose: Legacy butterfly package (old interface, being replaced by `torch_butterfly/`)
- Contains: Old Butterfly nn.Module, old multiply code, old C++ extensions with separate setup.py files
- Key files: `butterfly.py` (old module), `butterfly_multiply.py` (old multiply with fallback)

**`tests/`:**
- Purpose: Test suite for `torch_butterfly` package
- Contains: pytest test files, one per module
- Key files: `test_butterfly.py` (core tests), `test_special.py` (transform correctness)

**`learning_transforms/`:**
- Purpose: Experiment code for the "Learning Fast Algorithms" paper
- Contains: Training scripts for learning various transforms (FFT, Hadamard, circulant, etc.)
- Key files: `learning_fft.py`, `learning_transforms.py`, `training.py`

**`cnn/`:**
- Purpose: Experiment code for CNN compression/acceleration using butterfly layers
- Contains: Training scripts for CIFAR/ImageNet, model definitions, distillation
- Key files: `cifar_experiment.py`, `imagenet_experiment.py`, `models/butterfly_conv.py`

**`convolution/`:**
- Purpose: Newer convolution experiments using Hydra config and PyTorch Lightning
- Contains: Training infrastructure, model definitions, Hydra configs
- Key files: `train.py` (entry point), `models/kops.py` (kaleidoscope ops)

## Key File Locations

**Entry Points:**
- `setup.py`: Package build and install (compiles C++ extensions)
- `torch_butterfly/__init__.py`: Package import entry, loads native libs
- `convolution/train.py`: Training entry point for convolution experiments
- `cnn/cifar_experiment.py`: CIFAR experiment entry point
- `cnn/imagenet_experiment.py`: ImageNet experiment entry point

**Configuration:**
- `setup.py`: Build configuration (CUDA flags, extension sources)
- `requirements.txt`: Dependencies
- `convolution/cfg/`: Hydra YAML configs for convolution experiments

**Core Logic:**
- `torch_butterfly/butterfly.py`: Main Butterfly, ButterflyUnitary, ButterflyBmm classes
- `torch_butterfly/multiply.py`: Bridge to native C++/CUDA multiply kernel
- `torch_butterfly/special.py`: All special transform constructors (FFT, DCT, Hadamard, etc.)
- `torch_butterfly/combine.py`: Composition functions (diagonal fusion, product, kronecker)
- `torch_butterfly/permutation.py`: Permutation utilities and perm-to-butterfly conversion
- `csrc/butterfly.cpp`: Native extension dispatch and autograd
- `csrc/cuda/butterfly_cuda.cu`: CUDA kernel implementation

**Testing:**
- `tests/test_butterfly.py`: Core module tests (17K lines - comprehensive)
- `tests/test_special.py`: Transform correctness tests (18K lines - comprehensive)
- `tests/test_multiply.py`: Multiply function tests
- `tests/test_combine.py`: Composition tests

## Naming Conventions

**Files:**
- Snake_case for all Python files: `butterfly_base4.py`, `complex_utils.py`
- Test files prefixed with `test_`: `test_butterfly.py`, `test_special.py`
- C++ files match Python module names: `butterfly.cpp` -> `torch_butterfly._butterfly`

**Directories:**
- Lowercase, underscore-separated: `torch_butterfly/`, `learning_transforms/`, `factor_multiply/`
- Experiment directories named by domain: `cnn/`, `convolution/`, `transformer/`

## Where to Add New Code

**New Transform (e.g., new special decomposition):**
- Add factory function to `torch_butterfly/special.py`
- Add tests to `tests/test_special.py`
- Use existing `Butterfly`, `FixedPermutation`, `Diagonal` building blocks

**New Butterfly Variant (e.g., new nn.Module):**
- Add class to `torch_butterfly/butterfly.py` (or new file in `torch_butterfly/`)
- Export from `torch_butterfly/__init__.py`
- Add tests to `tests/test_butterfly.py`

**New Composition Operator:**
- Add function to `torch_butterfly/combine.py`
- Add tests to `tests/test_combine.py`

**New C++/CUDA Kernel:**
- Add `.cpp` file to `csrc/` (dispatch + op registration)
- Add CPU impl to `csrc/cpu/`
- Add CUDA impl to `csrc/cuda/`
- `setup.py` auto-discovers new `.cpp` files in `csrc/` and their corresponding `_cpu.cpp`/`_cuda.cu`

**New Experiment:**
- Create new top-level directory (e.g., `my_experiment/`)
- Import from `torch_butterfly` or `butterfly` packages
- Add training scripts and model definitions

**New CNN Model:**
- Add to `cnn/models/` or `convolution/models/`
- Register in the corresponding `__init__.py`

## Special Directories

**`csrc/`:**
- Purpose: Native C++/CUDA code compiled at install time
- Generated: No (source files, but compiled .so files go elsewhere)
- Committed: Yes

**`data/`:**
- Purpose: Dataset storage
- Generated: Yes (downloaded datasets)
- Committed: Partially (directory structure committed, large data files likely gitignored)

**`tests_old/`:**
- Purpose: Tests for the legacy `butterfly/` package
- Generated: No
- Committed: Yes (kept for backward compatibility)

**`fairseq/`:**
- Purpose: Placeholder for fairseq git submodule (referenced in `.gitmodules`)
- Generated: No
- Committed: Yes (empty directory)

**`butterfly/factor_multiply/` and `butterfly/factor_multiply_fast/`:**
- Purpose: Legacy C++ extensions with their own `setup.py` files (installed separately)
- Generated: No (source)
- Committed: Yes

---

*Structure analysis: 2026-04-02*
