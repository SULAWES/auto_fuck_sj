# automatic_gc

An MVP orchestrator for coursework-style C++ solving on Windows.

Current focus:

- run a single problem at a time
- use Codex as the only agent backend
- compile with `g++`
- compare candidate output against `demo.exe`
- keep all intermediate artifacts in a per-run workspace

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

## Current limits

- PDF extraction is best-effort only
- multiple generated `.cpp` files are compiled together as one program
- if a question actually requires multiple independent programs, run separate jobs
- hard constraints are partly inferred from problem text and partly configurable via CLI flags

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
- `--ban-token`: extra forbidden token, repeatable
- `--generated-cases`: number of Codex-generated testcases
- `--codex-model`: optional model override for `codex exec`

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
