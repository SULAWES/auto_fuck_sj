# Development Goals

## Primary Goal

Build a reliable Windows-local orchestrator that can solve coursework-style C++ subproblems with Codex, verify behavior against `demo.exe`, and preserve the full solving process in a per-run workspace.

## Near-Term Goals

- keep the solving loop stable across multiple validated subproblems
- make `demo.exe` subproblem selection explicit and repeatable
- reduce solver dependence on guessed formatting
- improve failure feedback quality for retry attempts
- improve hard-constraint detection for course-specific bans
- keep regression validation repeatable from a checked-in spec

## Mid-Term Goals

- add stronger PDF extraction on Windows, preferably via `pdftotext`
- reduce manual handoff knowledge such as required `demo.exe` flags
- make encoding behavior explicit and repeatable across more assignments
- improve humanization while preserving correctness
- expand regression coverage with more real coursework samples

## Quality Targets

- repeated end-to-end success on `5-b15` and `5-b16 --sub1..--sub4`
- low retry count on common assignments
- workspace artifacts remain readable and useful for debugging
- constraint violations are surfaced before final output
- final code remains correct and still looks like normal coursework

## Non-Goals For Now

- multi-problem batch processing at large scale
- a full free-form multi-agent architecture
- GUI or web interface
- broad compiler/toolchain compatibility beyond the current Windows `g++` target

## Recommended Next Development Focus

1. Install and verify `pdftotext` on this Windows machine.
2. Improve extraction of hard bans and subproblem-specific rules from the PDF.
3. Add a stable fallback strategy for locating a runnable `codex.exe`.
4. Expand regression coverage beyond the current single grouped testcase for `5-b16`.
5. Decide whether compiler-flag charset conversion should remain the long-term strategy.
