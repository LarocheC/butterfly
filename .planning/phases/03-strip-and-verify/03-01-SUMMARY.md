---
phase: 03-strip-and-verify
plan: 01
subsystem: cleanup
tags: [legacy-removal, submodule, git-rm]

# Dependency graph
requires:
  - phase: 02-build-and-test
    provides: verified working torch_butterfly build and tests
provides:
  - Clean repo with only torch_butterfly/, csrc/, tests/, and build config
  - fairseq submodule fully deregistered
affects: [03-02, ci-cd, gitignore]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified: []

key-decisions:
  - "Single commit for all 11 removals -- atomic cleanup operation"

patterns-established: []

requirements-completed: [LEGACY-01, LEGACY-02, LEGACY-03, LEGACY-04, EXP-01, EXP-02, EXP-03, EXP-04, CLEAN-01, CLEAN-02]

# Metrics
duration: 1min
completed: 2026-04-03
---

# Phase 3 Plan 1: Strip Legacy Code Summary

**Removed 185 files across 11 legacy directories/assets -- butterfly/, tests_old/, learning_transforms/, fairseq submodule, cnn/, convolution/, transformer/, gumbel-sinkhorn/, data/, ray_template.sh**

## Performance

- **Duration:** 46s
- **Started:** 2026-04-03T09:22:51Z
- **Completed:** 2026-04-03T09:23:37Z
- **Tasks:** 2
- **Files deleted:** 185

## Accomplishments
- Removed legacy butterfly/ package (replaced by torch_butterfly/)
- Removed 5 experiment directories (cnn/, convolution/, transformer/, gumbel-sinkhorn/, learning_transforms/)
- Fully deregistered fairseq git submodule (removed .gitmodules and .git/modules/fairseq)
- Removed dead assets (data/, ray_template.sh, tests_old/)

## Task Commits

Each task was committed atomically:

1. **Task 1+2: Remove legacy code, experiments, and dead assets** - `3a23597` (chore)

**Plan metadata:** (pending -- docs commit)

## Files Created/Modified
- All 185 files were deletions -- no files created or modified

## Decisions Made
- Combined Task 1 and Task 2 into a single commit as specified by the plan ("Commit all removals from Task 1 and Task 2 together")

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Force-removed .gitmodules after git rm fairseq staged changes to it**
- **Found during:** Task 1
- **Issue:** `git rm fairseq` modified .gitmodules in the staging area, so `git rm .gitmodules` required `-f` flag
- **Fix:** Used `git rm -f .gitmodules` instead of `git rm .gitmodules`
- **Files modified:** .gitmodules
- **Verification:** File removed, git status clean
- **Committed in:** 3a23597

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Trivial git flag adjustment. No scope creep.

## Issues Encountered
None beyond the .gitmodules force flag noted above.

## Known Stubs
None -- this plan only removed files.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Repo is stripped to core: torch_butterfly/, csrc/, tests/, build config, and .planning/
- Ready for plan 03-02 (build artifact cleanup and verification)

---
*Phase: 03-strip-and-verify*
*Completed: 2026-04-03*

## Self-Check: PASSED
