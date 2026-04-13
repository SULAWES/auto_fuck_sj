# Regression Workflow

## Purpose

Use `run-regression` when you want to run multiple known solving jobs from one checked-in spec.

## Command

```bash
python main.py run-regression --spec docs/regression-spec.example.json
```

If the default `codex` on PATH is not runnable on the current machine, pass an explicit binary path:

```bash
python main.py run-regression --spec docs/regression-spec.example.json --codex-bin "C:\\path\\to\\codex.exe"
```

## Spec Format

The spec is a UTF-8 JSON file with a top-level `jobs` array.

Each job supports:

- `problem`: required, problem file path
- `demo`: required, demo executable path
- `demo_args`: optional, extra arguments passed to `demo.exe`
- `data`: optional, grouped testcase file path
- `cpp_name`: optional, single expected output filename
- `cpp_names`: optional, list form of expected output filenames
- `entry_cpp`: optional, preferred entry filename
- `max_attempts`: optional, defaults to `3`
- `generated_cases`: optional, defaults to `5`
- `ban_tokens`: optional, list of extra forbidden tokens

## Single-Run Equivalent

For ad hoc validation, the single-job form now also supports repeated `--demo-arg` flags:

```bash
python main.py run \
  --problem .\\24252-050109-W1201.第05模块 作业 - PART4 - 字符数组与string类 - II.pdf \
  --demo .\\5-b16-demo.exe \
  --demo-arg=--sub1 \
  --data .\\test_data.txt \
  --cpp-name 5-b16.cpp \
  --generated-cases 0
```

## Adding A New Subproblem

1. Put the new `demo.exe` in the repository or another stable local path.
2. Confirm the grouped testcase file contains the matching prefix, such as `5-b16-*`.
3. If the PDF says the demo requires a subproblem switch, add it through `demo_args`.
4. Add a job entry to the regression spec with the matching `cpp_name`, such as `5-b16.cpp`.
5. Run the single-job command first if the subproblem has never been validated.
6. After it passes, keep that job in the regression spec for future runs.

## Current Validated Coverage

The checked-in example spec now covers:

- `5-b15.cpp`
- `5-b16.cpp --sub1`
- `5-b16.cpp --sub2`
- `5-b16.cpp --sub3`
- `5-b16.cpp --sub4`

`5-b16` must be validated with an explicit subproblem flag. A bare `5-b16-demo.exe` invocation is not authoritative for this assignment.

