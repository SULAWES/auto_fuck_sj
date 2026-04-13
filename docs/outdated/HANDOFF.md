# Windows Handoff

## Purpose

This repository is an MVP for a Windows-local coursework C++ solving orchestrator.

Primary goal:

- read a coursework problem statement
- generate one or more required source files with Codex
- compile with `g++`
- run the candidate program against `demo.exe`
- compare outputs with `txt_compare.exe`
- keep all intermediate artifacts in a per-run workspace

## Current Status

Implemented:

- repository skeleton and CLI entrypoint
- numbered workspace creation
- PDF text extraction through `pdftotext` when available
- best-effort text decoding for Chinese course materials
- grouped testcase parsing fallback for local development
- Codex structured JSON generation flow
- compile / run / compare orchestration skeleton
- hard-constraint inference and basic style checks
- solver prompt enrichment with demo output observations
- UTF-8-safe `codex exec` prompt submission
- binary stdout capture for demo/candidate evaluation
- Windows `g++` charset flags to match local Chinese console output

Validated on this Windows machine:

- `get_input_data.exe --all_group test_data.txt` works
- `5-b15-demo.exe` runs correctly with grouped test input
- `txt_compare.exe` success/failure strings were confirmed
- `codex exec --output-schema` works in the Windows shell environment
- end-to-end run for `5-b15.cpp` passed on `workspaces/000008`

Known remaining limits:

- PDF extraction is still best-effort only
- the sample PDF contains multiple subproblems, but the current flow is still best run one subproblem at a time
- successful output matching currently depends on Windows-local encoding behavior and `g++` charset flags
- constraint inference is still shallow for rules like `no scanf/printf`, `no class`, `no struct`, and per-subproblem exceptions

## Important Files

Read these first:

1. `需求.md`
2. `方案.md`
3. `README.md`
4. `src/auto_fuck_sj/cli.py`
5. `src/auto_fuck_sj/orchestrator.py`
6. `src/auto_fuck_sj/codex_adapter.py`
7. `src/auto_fuck_sj/constraints.py`

For the latest validated sample run, also read:

1. `workspaces/000008/outputs/attempt_01/evaluation_summary.json`
2. `workspaces/000008/final/5-b15.cpp`

## Current Sample Inputs

Repository root currently contains:

- `24252-050109-W1201.第05模块 作业 - PART4 - 字符数组与string类 - II.pdf`
- `test_data.txt`
- `5-b15-demo.exe`
- `get_input_data.exe`
- `txt_compare.exe`

Notes:

- `test_data.txt` was detected as `gb18030`
- the current sample PDF includes multiple subproblems, not just one
- the current orchestrator is better suited to one subproblem at a time

## Latest Progress

The previous handoff recommended doing the first real Windows end-to-end run. That work is now done.

What changed in code:

- the orchestrator now writes `testcases/demo_observations.json` before solving, using real `demo.exe` outputs from selected provided cases
- the solver prompt now reads those observations so it can align prompt text and output formatting without guessing
- `codex exec` is now fed UTF-8 explicitly, which prevents retry prompts with Chinese feedback from failing on stdin encoding
- evaluation now captures demo and candidate stdout as raw bytes before writing files, avoiding text re-encoding corruption
- `g++` is invoked with `-finput-charset=UTF-8` and `-fexec-charset=GBK` so UTF-8 source literals produce Windows-local Chinese output bytes compatible with `txt_compare.exe`

What was validated:

- a one-attempt run for `5-b15.cpp` now returns `"status": "passed"`
- `evaluation_summary.json` for `workspaces/000008` reports `all_passed: true`
- the previous failure modes were reproduced and understood:
  - no PDF extractor led the solver to guess output format
  - retry prompts with Chinese compare output broke `codex exec` stdin decoding
  - UTF-8 source literals produced mismatched bytes versus the Windows-local `demo.exe` output

## Behavior Expectations

The user clarified the intended style target:

- not over-engineered
- still shows basic computer science training
- no meaningless names like `a`, `b`, `c`, `d` for core logic variables
- no pinyin identifiers
- preserve correctness first

The user also clarified:

- first version should optimize for “most likely to run”
- Windows compile target is `g++`
- final outputs should keep intermediate artifacts
- problems often include hard restrictions
- `get_input_data.exe` is the main default, while some assignments may specifically require `get_input_data2.exe`

## Recommended Next Step On Windows

1. Run the same flow on another single subproblem such as `5-b16.cpp` to verify the current fixes are not specific to `5-b15`.
2. Install and validate a PDF text extractor on Windows, preferably `pdftotext`, so the solver can read real problem text instead of leaning on demo observations.
3. Tighten constraint extraction for rules such as `no string`, `no scanf/printf`, `no struct/class`, and per-subproblem exceptions.
4. Decide whether charset conversion should stay compiler-flag based or move to a more explicit output-encoding strategy.
5. Improve retry feedback summarization so solver attempts receive smaller, cleaner failure signals than full compare dumps.

## Suggested Prompt For A New Codex Window

```text
Read HANDOFF.md first, then read 需求.md, 方案.md, README.md, src/auto_fuck_sj/cli.py, and src/auto_fuck_sj/orchestrator.py.
This repo is a Windows-local coursework C++ solving orchestrator MVP.
Windows validation has now been done for `5-b15.cpp`, including real execution of `get_input_data.exe`, `demo.exe`, `txt_compare.exe`, and `codex exec --output-schema`.
Continue from there by generalizing beyond `5-b15`, improving PDF extraction, and tightening constraint handling.
```





