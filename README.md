# auto_fuck_sj

An MVP orchestrator for coursework-style C++ solving on Windows.

Current focus:

- run a single subproblem at a time
- use Codex as the only agent backend
- compile with `g++`
- compare candidate output against `demo.exe`
- keep all intermediate artifacts in a per-run workspace

Current validated status:

- real Windows end-to-end execution has been verified for `5-b15.cpp`
- real Windows end-to-end execution has been verified for `5-b16.cpp` with `--sub1`, `--sub2`, `--sub3`, and `--sub4`
- a real 5-job regression run passed on March 9, 2026 in `workspaces/000014` through `workspaces/000018`
- grouped testcase selection filters by the active subproblem prefix
- `demo.exe` arguments are now part of the run pipeline and regression spec

## What exists in this version

- workspace creation with persistent artifacts
- best-effort problem text extraction
- provided testcase loading through `get_input_data.exe`
- local grouped testcase parsing fallback for development without the Windows tool
- Codex-driven testcase generation
- Codex-driven C++ source generation
- compile, run, compare loop with retry feedback
- basic hard-constraint and style checks
- post-pass humanization step with regression test
- pre-solver demo observation capture for format inference
- structured retry feedback summaries
- regression command driven by a JSON spec
- explicit `demo.exe` argument support for both single runs and regression runs
- Windows-local output encoding alignment for Chinese console text

## Current limits

- PDF extraction is best-effort only
- multiple generated `.cpp` files are compiled together as one program
- if a question actually requires multiple independent programs, run separate jobs
- hard constraints are partly inferred from problem text and partly configurable via CLI flags
- `5-b16` still depends on manually specifying the correct `--subN` flag from the PDF
- current `5-b16` validation uses one provided grouped testcase, so coverage is still narrow

## Usage

Run from the repository root:

```bash
python main.py run \
  --problem path/to/problem.pdf \
  --demo path/to/demo.exe \
  --data path/to/hw_data.txt \
  --cpp-name main.cpp \
  --workspace-root workspaces
```

Useful options:

- `--cpp-name`: repeatable, expected generated source filenames
- `--entry-cpp`: preferred entry filename when there are multiple source files
- `--demo-arg`: extra argument passed to `demo.exe`, repeatable
- `--ban-token`: extra forbidden token, repeatable
- `--generated-cases`: number of Codex-generated testcases
- `--codex-model`: optional model override for `codex exec`
- `--codex-bin`: explicit Codex binary path when the PATH entry is not runnable

Example for `5-b16` subproblem validation:

```bash
python main.py run \
  --problem ".\\24252-050109-W1201.第05模块 作业 - PART4 - 字符数组与string类 - II.pdf" \
  --demo .\\5-b16-demo.exe \
  --demo-arg=--sub1 \
  --data .\\test_data.txt \
  --cpp-name 5-b16.cpp \
  --generated-cases 0
```

## Regression Usage

Run multiple jobs from a checked-in spec:

```bash
python main.py run-regression --spec docs/regression_spec_example.json
```

The example spec currently covers `5-b15` plus `5-b16 --sub1..--sub4`.

## Workspace layout

Each run creates a numbered workspace:

```text
workspaces/000001/
  input/
  extracted/
  testcases/
  candidates/
  outputs/
  logs/
  final/
```

## Suggested Windows setup

Ensure the following commands are callable on the target Windows machine:

- `codex`
- `g++`
- `txt_compare.exe`
- `get_input_data.exe`
- `demo.exe` for the current problem

Then run:

```bash
python main.py run --problem problem.pdf --demo demo.exe --data hw_data.txt
```

## Next steps

- install `pdftotext` on the Windows machine and re-check extraction quality
- improve hard-constraint inference for banned syntax and per-subproblem exceptions
- add a stable way to locate a runnable `codex.exe`
- expand regression coverage with more real grouped testcases


