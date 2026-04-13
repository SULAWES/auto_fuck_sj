# Action Tracker

This file tracks concrete work items. Mark each item when it is completed.

## Completed

- [x] Create the repository skeleton and CLI entrypoint.
- [x] Implement workspace creation and artifact layout.
- [x] Add grouped testcase loading.
- [x] Add local grouped testcase parsing fallback.
- [x] Add Codex JSON-schema based generation flow.
- [x] Add compile / run / compare orchestration.
- [x] Validate `get_input_data.exe` on Windows.
- [x] Validate `txt_compare.exe` behavior on Windows.
- [x] Validate `codex exec --output-schema` on Windows.
- [x] Run a real end-to-end Windows pass for `5-b15.cpp`.
- [x] Add demo observation capture before solver execution.
- [x] Fix UTF-8 prompt submission for retry attempts.
- [x] Preserve raw stdout bytes during evaluation.
- [x] Align candidate Chinese output encoding with Windows-local behavior.
- [x] Write project documentation under `docs/`.
- [x] Filter grouped testcases to the active subproblem prefix.
- [x] Replace raw compare dumps in retry feedback with structured summaries.
- [x] Add a regression-style command for repeated validation runs.
- [x] Document how to add new sample subproblems for regression coverage.
- [x] Add or obtain `5-b16-demo.exe`.
- [x] Add explicit `demo.exe` argument support to the run pipeline.
- [x] Run the full flow on `5-b16.cpp` with `--sub1`.
- [x] Run the full flow on `5-b16.cpp` with `--sub2`.
- [x] Run the full flow on `5-b16.cpp` with `--sub3`.
- [x] Run the full flow on `5-b16.cpp` with `--sub4`.
- [x] Check that the current prompt and encoding strategy generalize to another subproblem.
- [x] Validate `run-regression` with at least two real jobs.

## Next Actions

- [ ] Install `pdftotext` on the Windows machine.
- [ ] Verify extracted text quality on the current sample PDF.
- [ ] Improve constraint inference for bans such as `string`, `scanf/printf`, `class`, and `struct`.
- [ ] Add a stable way to locate a runnable `codex.exe` on this machine.
- [ ] Add a documented mapping from PDF subproblem descriptions to required `demo.exe` flags.
- [ ] Expand regression coverage beyond the single provided `5-b16` grouped testcase.

## Later Actions

- [ ] Evaluate whether compiler-flag based charset conversion should remain the long-term strategy.
- [ ] Improve humanizer safety checks and regression coverage.
- [ ] Explore support for multi-file submissions when the coursework actually requires them.
