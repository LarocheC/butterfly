# torch_butterfly

PyTorch implementation of butterfly matrices for efficient structured linear transforms, from the papers [Learning Fast Algorithms for Linear Transforms Using Butterfly Factorizations](https://arxiv.org/abs/1903.05895) and [Kaleidoscope: An Efficient, Learnable Representation For All Structured Linear Maps](https://openreview.net/forum?id=BkgrBgSYDS).

## What is this?

Butterfly matrices are a class of structured matrices that can represent many fast linear transforms -- FFT, inverse FFT, discrete cosine transform (DCT), discrete sine transform (DST), Hadamard transform, circulant and Toeplitz matrix multiplications, and convolutions -- using O(N log N) parameters instead of O(N^2). This library provides GPU-accelerated butterfly matrix multiplication via custom C++/CUDA kernels, wrapped in familiar `torch.nn.Module` interfaces that serve as drop-in replacements for `nn.Linear`.

## Requirements

- Python >= 3.10
- PyTorch >= 2.0
- numpy
- A C++ compiler supporting C++14 (for building extensions)
- CUDA toolkit (optional, for GPU acceleration)

## Installation

**With uv (recommended):**

```bash
uv pip install .
```

**With pip:**

```bash
pip install .
```

**Development install:**

```bash
uv pip install -e ".[dev]"
```

### CUDA support

CUDA extensions are compiled automatically when a CUDA toolkit is detected. To override auto-detection:

```bash
FORCE_CUDA=1 uv pip install .   # Force CUDA compilation
FORCE_CPU=1 uv pip install .    # Force CPU-only build
```

You can also set `TORCH_CUDA_ARCH_LIST` to target specific GPU architectures (e.g., `"7.0 8.0 9.0+PTX"`).

## Usage

The `Butterfly` module is a drop-in replacement for `nn.Linear`:

```python
from torch_butterfly import Butterfly

layer = Butterfly(in_size=1024, out_size=1024)
```

The file `torch_butterfly/special.py` contains factory functions that construct butterfly matrices performing exact well-known transforms:

```python
from torch_butterfly.special import fft, ifft, dct, dst, hadamard, circulant
```

See `tests/test_special.py` for examples verifying that these butterfly matrices exactly perform the corresponding operations.

## Citation

If you use this codebase, please cite:

```bibtex
@inproceedings{dao2019learning,
  title={Learning Fast Algorithms for Linear Transforms Using Butterfly Factorizations},
  author={Dao, Tri and Gu, Albert and Eichhorn, Matthew and Rudra, Atri and R{\'e}, Christopher},
  booktitle={International Conference on Machine Learning},
  year={2019}
}

@inproceedings{dao2020kaleidoscope,
  title={Kaleidoscope: An Efficient, Learnable Representation For All Structured Linear Maps},
  author={Dao, Tri and Sohoni, Nimit and Gu, Albert and Eichhorn, Matthew and Blber, Amit and Rudra, Atri and R{\'e}, Christopher},
  booktitle={International Conference on Learning Representations},
  year={2020}
}
```

## License

Apache-2.0
