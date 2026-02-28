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

Blocked in the current Linux environment:

- `demo.exe`
- `get_input_data.exe`
- `txt_compare.exe`

These files are Windows PE executables and cannot run directly on the current Ubuntu host.

## Important Files

Read these first:

1. `需求.md`
2. `方案.md`
3. `README.md`
4. `src/automatic_gc/cli.py`
5. `src/automatic_gc/orchestrator.py`
6. `src/automatic_gc/codex_adapter.py`
7. `src/automatic_gc/constraints.py`

For the current sample problem, also read:

1. `workspaces/000001/extracted/problem_context.md`
2. `workspaces/000001/testcases/provided_cases_local_parse.json`

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

1. Run a real end-to-end test with the Windows executables.
2. Start with a single subproblem such as `5-b15.cpp`.
3. Confirm the exact `txt_compare.exe` success/failure output strings.
4. Confirm `codex exec --output-schema` behavior in the Windows shell environment.
5. Tighten constraint extraction for rules such as `no string`, `no scanf/printf`, `no struct/class`, and per-subproblem exceptions.

## Suggested Prompt For A New Codex Window

```text
Read HANDOFF.md first, then read 需求.md, 方案.md, README.md, src/automatic_gc/cli.py, and src/automatic_gc/orchestrator.py.
This repo is a Windows-local coursework C++ solving orchestrator MVP.
Current Linux work already validated PDF extraction and grouped testcase parsing, but not demo.exe/get_input_data.exe/txt_compare.exe execution because those are Windows PE executables.
Continue from there and focus on a real Windows end-to-end run for a single subproblem first.
```
