# Milestones

## v1.0 Build System Modernization (Shipped: 2026-04-02)

**Phases completed:** 2 phases, 4 plans, 6 tasks

**Key accomplishments:**

- PEP 621 pyproject.toml with torch build isolation, thin setup.py shim with CUDA 7.0/8.0/9.0+PTX arch targeting, and MANIFEST.in for sdist
- Glob-based .so discovery replacing PathFinder, TORCH_LIBRARY macro in version.cpp, CUDA mismatch downgraded to warning

---
