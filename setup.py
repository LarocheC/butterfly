# Thin build shim -- all metadata lives in pyproject.toml.
# This file exists only because torch.utils.cpp_extension.BuildExtension
# is a setuptools build_ext subclass that cannot be declared in TOML.
#
# Adapted from https://github.com/pytorch/extension-cpp

import os
from pathlib import Path

from setuptools import setup

import torch
from torch.utils.cpp_extension import BuildExtension, CppExtension, CUDAExtension, CUDA_HOME


def get_extensions():
    WITH_CUDA = torch.cuda.is_available() and CUDA_HOME is not None
    if os.getenv("FORCE_CUDA", "0") == "1":
        WITH_CUDA = True
    if os.getenv("FORCE_CPU", "0") == "1":
        WITH_CUDA = False
    if os.getenv("BUILD_DOCS", "0") == "1":
        return []

    Extension = CUDAExtension if WITH_CUDA else CppExtension
    define_macros = [("WITH_CUDA", None)] if WITH_CUDA else []
    extra_compile_args = {"cxx": ["-O3"]}

    if WITH_CUDA:
        nvcc_flags = os.getenv("NVCC_FLAGS", "").split() if os.getenv("NVCC_FLAGS") else []
        nvcc_flags += ["--expt-extended-lambda", "-lineinfo"]

        # CUDA architecture targeting:
        # - Respect TORCH_CUDA_ARCH_LIST env var if set (standard PyTorch convention)
        # - Otherwise default to Volta (7.0), Ampere (8.0), Hopper (9.0) with PTX forward compat
        if not os.getenv("TORCH_CUDA_ARCH_LIST"):
            os.environ["TORCH_CUDA_ARCH_LIST"] = "7.0 8.0 9.0+PTX"

        extra_compile_args["nvcc"] = nvcc_flags

    extensions_dir = Path("csrc")
    extensions = []
    for main in extensions_dir.glob("*.cpp"):
        name = main.stem
        sources = [str(main)]
        cpu_path = extensions_dir / "cpu" / f"{name}_cpu.cpp"
        if cpu_path.exists():
            sources.append(str(cpu_path))
        cuda_path = extensions_dir / "cuda" / f"{name}_cuda.cu"
        if WITH_CUDA and cuda_path.exists():
            sources.append(str(cuda_path))
        extensions.append(
            Extension(
                f"torch_butterfly._{name}",
                sources,
                include_dirs=[str(extensions_dir)],
                define_macros=define_macros,
                extra_compile_args=extra_compile_args,
            )
        )
    return extensions


setup(
    ext_modules=get_extensions(),
    cmdclass={
        "build_ext": BuildExtension.with_options(
            use_ninja=True
        )
    },
)
