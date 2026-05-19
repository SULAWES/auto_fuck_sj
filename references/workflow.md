# Workflow

## Inputs

Expected inputs for a typical run:

- optional pre-PDF constraint text or files
- problem statement file
- `demo.exe`
- optional grouped testcase file
- optional `get_input_data.exe`
- optional previous-assignment reference files
- optional demo arguments such as `--sub1`
- optional expected source filenames and extensions

## Recommended order

1. Create a numbered workspace.
2. Copy the original inputs into `input/`.
3. Copy any pre-PDF constraint files into `input/` and treat them as the highest-priority specification layer.
4. Build `extracted/problem_context.md` from the copied source file, pre-PDF constraints, extracted PDF text, optional text companion files, and optional previous-assignment references.
5. Build `testcases/provided_cases.json`, preferably with `get_input_data.exe`.
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
- Do not depend on external PDF-to-text tools. Prefer the local PDF-reading path built into the agent runtime, and only fall back to treating the PDF as a raw artifact if extraction still fails.
- Treat extracted PDF text as the primary written statement after explicit pre-PDF constraints.
- Use previous-assignment references only as a comparison group for ambiguous formatting, error handling, extraction sanity checks, and allowed-knowledge expectations. Never copy their solutions.
- Default to not using STL unless the statement explicitly allows it.
- For allowed knowledge, start from the whitelist near the front of the PDF. If no whitelist is clear, stay conservative with pointers, references, structs, and classes.
- Trust `demo.exe` more than extracted PDF text when they disagree on visible output.
- Trust the official grouped testcase data more than invented cases when they disagree on input shape.
- Prefer `get_input_data.exe` over text parsing when it is available, because it reflects the teacher-provided extraction path.
- If the task requires a demo flag, carry it through every demo invocation.
- Keep the editable working copy in UTF-8 unless a tool absolutely requires another encoding.
- Convert to the required submission encoding only at the final export step.
- If the statement specifies an exact output filename such as `5-b16-1.c`, preserve that exact filename and extension in the final artifact.
- If there is no grouped testcase file, or the official data only covers a small subset, add `generated_cases.json` and merge it into the evaluation bundle.
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
