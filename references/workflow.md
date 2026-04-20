# Workflow

## Inputs

Expected inputs for a typical run:

- optional pre-PDF constraint text or files
- problem statement file
- `demo.exe`
- optional grouped testcase file
- optional demo arguments such as `--sub1`
- optional expected source filenames and extensions

## Recommended order

1. Create a numbered workspace.
2. Copy the original inputs into `input/`.
3. Copy any pre-PDF constraint files into `input/` and treat them as the highest-priority specification layer.
4. Extract best-effort problem text and write `extracted/problem_context.md`.
5. Parse provided grouped testcases into `testcases/provided_cases.json`.
6. Observe `demo.exe` on representative cases and save `testcases/demo_observations.json`.
7. Generate or repair candidate source files in `candidates/attempt_XX/`.
8. Run constraint checks.
9. Compile and evaluate with the local Windows toolchain.
10. Summarize failures and iterate.
11. Only after a pass, make the code less polished and rerun evaluation.
12. Export the final deliverable as the required submission encoding and line endings.
13. Re-run compile and runtime validation on the exported submission files.

## Decision rules

- Trust explicit pre-PDF constraints more than the PDF when they disagree.
- Default to not using STL unless the statement explicitly allows it.
- Trust `demo.exe` more than extracted PDF text when they disagree on visible output.
- Trust the original grouped testcase file more than invented cases when they disagree on input shape.
- If the task requires a demo flag, carry it through every demo invocation.
- Keep the editable working copy in UTF-8 unless a tool absolutely requires another encoding.
- Convert to the required submission encoding only at the final export step.
- If the statement specifies an exact output filename such as `5-b16-1.c`, preserve that exact filename and extension in the final artifact.
- If there are no cases, a compile-only pass is acceptable, but state that runtime coverage is missing.

## Output expectations

The final candidate should:

- compile locally with the appropriate compiler for the required extension, typically `gcc` for `.c` and `g++` for `.cpp`
- preserve any exact source filename and extension required by the statement
- export successfully to the required submission encoding and line endings, typically `GB2312 + CRLF`
- pass at least one final compile check on the exported submission files
- match `demo.exe` output on all available cases
- avoid explicit hard-constraint violations
- default to non-STL implementations unless the statement explicitly allows STL
- use `snake_case` names unless the assignment explicitly says otherwise
- use Allman braces unless the assignment explicitly says otherwise
- use procedural, task-focused code rather than framework-like abstractions
- keep comments sparse and practical
- remain readable and student-like
