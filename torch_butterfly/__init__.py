import os
import glob
import warnings

import torch

__version__ = '0.0.0'

# Load compiled C++/CUDA extensions
_ext_dir = os.path.dirname(os.path.abspath(__file__))


def _load_extension(name):
    """Load a compiled C++ extension library by name prefix.

    Searches for shared libraries matching the name prefix in the package
    directory, handling platform-specific suffixes (.so, .pyd, .dylib)
    and CPython ABI tags (e.g., .cpython-310-x86_64-linux-gnu.so).
    """
    for suffix in ['*.so', '*.pyd', '*.dylib']:
        pattern = os.path.join(_ext_dir, f'{name}{suffix}')
        matches = glob.glob(pattern)
        if matches:
            torch.ops.load_library(matches[0])
            return
    raise ImportError(
        f"Could not find compiled extension '{name}' in {_ext_dir}. "
        f"Please reinstall: pip install --no-build-isolation -e ."
    )


# Load order matters: _version must load before _butterfly
# so check_cuda_version() can call torch.ops.torch_butterfly.cuda_version()
_load_extension('_version')
_load_extension('_butterfly')


def check_cuda_version():
    if torch.version.cuda is not None:
        cuda_version = torch.ops.torch_butterfly.cuda_version()

        if cuda_version == -1:
            major = minor = 0
        elif cuda_version < 10000:
            major, minor = int(str(cuda_version)[0]), int(str(cuda_version)[2])
        else:
            major, minor = int(str(cuda_version)[0:2]), int(str(cuda_version)[3])
        t_major, t_minor = [int(x) for x in torch.version.cuda.split('.')]

        if t_major != major or t_minor != minor:
            warnings.warn(
                f'Detected that PyTorch and torch_butterfly were compiled with '
                f'different CUDA versions. PyTorch has CUDA version '
                f'{t_major}.{t_minor} and torch_butterfly has CUDA version '
                f'{major}.{minor}. Please reinstall the torch_butterfly that '
                f'matches your PyTorch install.',
                UserWarning,
                stacklevel=2,
            )


check_cuda_version()
from .butterfly import Butterfly, ButterflyUnitary, ButterflyBmm  # noqa
from .butterfly_base4 import ButterflyBase4  # noqa
from .multiply import butterfly_multiply  # noqa
from . import combine
from . import complex_utils
from . import diagonal
from . import permutation
from . import special
from . import multiply_base4

__all__ = [
    'Butterfly',
    'ButterflyUnitary',
    'ButterflyBmm',
    'ButterflyBase4',
    'butterfly_multiply',
    '__version__',
]
