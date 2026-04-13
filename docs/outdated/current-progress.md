# Current Progress

## Project Position

`auto_fuck_sj` is now a Windows-local MVP that can solve coursework-style C++ subproblems with Codex, verify behavior against `demo.exe`, and preserve the full process in a numbered workspace.

The main flow already exists:

- read a problem file
- create a numbered workspace
- load provided grouped testcases
- call Codex to generate candidate C++ files
- compile with `g++`
- run both candidate and `demo.exe`
- compare outputs with `txt_compare.exe`
- keep all artifacts in the workspace

## What Has Been Implemented

- CLI entrypoint for single-run orchestration
- `run-regression` command driven by a checked-in JSON spec
- workspace layout generation
- best-effort text extraction for problem materials
- local fallback parser for grouped testcase files
- provided testcase filtering by active subproblem prefix
- explicit `demo.exe` argument support through CLI, run manifest, regression spec, demo observations, and evaluation
- Codex JSON-schema based generation flow
- compile / run / compare loop
- basic constraint inference and style checks
- post-pass humanization flow
- demo observation capture before solving
- structured retry feedback with compact previews instead of raw compare dumps
- UTF-8-safe prompt submission to `codex exec`
- binary stdout capture during evaluation
- Windows-local output encoding alignment through `g++` charset flags

## What Has Been Validated

Validated on the current Windows machine:

- `get_input_data.exe --all_group test_data.txt` works
- `5-b15-demo.exe` and `5-b16-demo.exe` run correctly with provided grouped input
- `5-b16-demo.exe` produces different required outputs for `--sub1`, `--sub2`, `--sub3`, and `--sub4`
- `txt_compare.exe` success/failure behavior was confirmed
- `codex --version` works from the current VS Code extension installation
- grouped testcase selection correctly keeps only the active subproblem prefix
- `run-regression` executed a real 5-job validation run and passed all jobs

Reference validated regression run:

- `workspaces/000014`: `5-b15.cpp`, passed, tested cases = `5`
- `workspaces/000015`: `5-b16.cpp --sub1`, passed, tested cases = `1`
- `workspaces/000016`: `5-b16.cpp --sub2`, passed, tested cases = `1`
- `workspaces/000017`: `5-b16.cpp --sub3`, passed, tested cases = `1`
- `workspaces/000018`: `5-b16.cpp --sub4`, passed, tested cases = `1`

## Important Validation Rule

`5-b16` must be validated with an explicit demo subproblem flag. A bare `5-b16-demo.exe` invocation is not authoritative for this assignment. Use one of:

- `--sub1`
- `--sub2`
- `--sub3`
- `--sub4`

## Key Problems Already Solved

- When the PDF text could not be extracted, the solver used to guess prompt text and output format.
- Retry attempts with Chinese feedback used to break because `codex exec` prompt stdin was not forced to UTF-8.
- Candidate output used to mismatch `demo.exe` because Windows-local Chinese output encoding was not aligned.
- Text re-encoding during evaluation used to corrupt compare inputs.
- Unrelated grouped testcases used to leak into the active subproblem run.
- Solver retries used to receive oversized raw compare logs instead of compact failure summaries.
- `5-b16` subproblem validation used to ignore required `demo.exe` flags.

## Current Limits

- PDF extraction is still best-effort only.
- The sample PDF contains multiple subproblems, but the workflow still depends on manually specifying the correct `demo.exe` sub-flag.
- Constraint inference is still shallow for many hard bans.
- `5-b16` currently has only one provided grouped testcase in `test_data.txt`, so regression breadth is still limited.
- Live validation still depends on the local Codex binary and API/network path being usable at run time.


