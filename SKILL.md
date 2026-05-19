---
name: auto-fuck-sj
description: Solve and validate coursework-style C++ assignments on Windows when the user provides a problem PDF or text statement plus a local `demo.exe`, grouped testcase data, or existing candidate `.cpp` files. Use for tasks such as extracting the problem, observing exact output format from `demo.exe`, generating or repairing coursework-style C++ code, checking banned syntax, running `g++` builds, comparing outputs with `txt_compare.exe`, and producing student-like final code that still passes local validation.
---

# Auto Fuck Sj

## Overview

Use this skill for Windows-local C++ homework workflows where correctness is judged by a provided executable rather than by manually reading the problem alone.

Treat `demo.exe` behavior as ground truth. Use the scripts in this skill for deterministic steps, and use Codex reasoning in-thread for code generation, repair, and final explanation.

Treat explicit user-provided constraints that appear before the PDF as hard requirements. When those constraints disagree with your default style preferences, follow the explicit constraints.

## Workflow

1. Confirm inputs.
   Required minimum:
   - problem statement file (`.pdf`, `.txt`, or `.md`)
   - `demo.exe`
   Optional but preferred:
   - pre-PDF constraint text or files
   - grouped testcase data file
   - `get_input_data.exe` for official grouped data extraction
   - previous-assignment reference files for ambiguous format, error handling, or allowed-knowledge checks
   - expected source filenames and extensions such as `5-b16-1.c` or `5-b16-2.cpp`
   - extra demo arguments such as `--sub1`

2. Create a workspace before touching candidate code.
   - Keep all artifacts in a numbered workspace.
   - Use `scripts/init_workspace.py`.
   - Unless the user requests another location, create the workspace under the current repo's `workspaces/` directory.

3. Extract the problem statement.
   - Use `scripts/extract_problem.py` to copy the original file and produce `problem_context.md`.
   - If the user provides constraint text or files before the PDF, include them with `--pre-constraint-file` and treat them as the highest-priority specification layer.
   - This skill does not depend on external PDF-to-text tools such as `pdftotext`.
   - For PDFs, first try the local PDF-reading path built into the agent runtime.
   - Treat extracted PDF text as the primary problem statement after any explicit pre-PDF constraints.
   - If PDF extraction still fails, keep the copied PDF as the source artifact and rely on pre-PDF constraints, any supplied text companion files, official testcases, and `demo.exe` behavior.
   - If the user has a plain text or markdown transcript of the statement, include it with `--problem-text-file`.
   - If the user provides previous-assignment reference files, include them with `--reference-assignment-file`; use them only to understand ambiguous input/output conventions, error handling, PDF extraction correctness, and likely allowed knowledge.
   - Never copy a previous-assignment solution. The current PDF and explicit constraints remain the source of truth.
   - Read [references/windows-encoding.md](references/windows-encoding.md) when Chinese console output or encoding drift is relevant.

4. Load provided testcases before inventing new ones.
   - If the user gives a grouped testcase file and `get_input_data.exe`, build the testcase bundle with `scripts/build_testcases.py` and prefer the exe-based extraction path.
   - If the grouped testcase file exists but `get_input_data.exe` is unavailable, fall back to `scripts/parse_grouped_cases.py`.
   - If there are subproblem prefixes such as `5-b16`, `sub1`, or filename stems that clearly scope the task, filter the provided cases to the active target.
   - If there is no grouped testcase file, or the official bundle is too small, create `testcases/generated_cases.json` in-thread and merge it into the testcase bundle as supplemental coverage.
   - Only create extra cases after you have consumed the provided ones.

5. Observe the demo program early.
   - Run representative cases through `scripts/observe_demo.py`.
   - Preserve `stdout`, `stderr`, return code, and the exact demo arguments used.
   - Use these observations to infer prompts, line breaks, spacing, and whether the program echoes anything unexpected.
   - If the task depends on a demo flag like `--sub1`, pass that same flag on every observation and evaluation run. Never mix bare and flagged demo runs.

6. Generate or repair candidate code in-thread.
   - Keep the code looking like solid coursework, not library or production code.
   - Treat the statement as the source of truth. When the statement imposes a coding restriction, follow it over any default habit.
   - Read the allowed-knowledge whitelist near the start of the PDF before choosing constructs.
   - Default to using only the allowed course topics: comparison/logical/conditional operators, branches, loops, functions, and arrays unless the PDF allows more.
   - Treat pointers, references, structs, and classes as advanced for this course context unless the PDF whitelist allows them.
   - If the statement explicitly gives the target source filename or extension, preserve it exactly.
   - Default to not using STL unless the statement explicitly allows it.
   - Prefer direct arrays, loops, and straightforward control flow over generic abstractions.
   - Prefer procedural decomposition: a clear `main()` flow plus a small number of task-specific helpers.
   - Keep helper functions concrete and local to the task; avoid reusable frameworks and unnecessary wrapper layers.
   - Match visible output exactly, including prompts, spaces, punctuation, and line breaks.
   - Handle required input validation explicitly instead of hiding it behind generic helpers.
   - Use `snake_case` for identifiers by default unless the assignment explicitly requires another naming scheme.
   - Allow short local names such as `i`, `j`, `k`, and `ch` when they are the clearest choice.
   - Preserve题目指定名、既有接口名、类名和外部常量名 exactly as required.
   - Use Allman braces: put every opening brace on its own line.
   - Avoid meaningless core identifiers such as `a`, `b`, `c`, `d`.
   - Do not use pinyin identifiers.
   - Use comments sparingly and only when they preserve a task rule, a tricky branch, or a required limitation.
   - If the assignment requests multiple independent source files, treat each required filename as its own deliverable and preserve the requested extension such as `.c` or `.cpp`.

7. Check constraints before spending time on style.
   - Use `scripts/check_constraints.py` on the generated files.
   - Read [references/constraints.md](references/constraints.md) when the statement bans STL, recursion, classes, or templates.
   - Treat PDF knowledge bans and whitelist-derived bans as hard constraints.
   - Read [references/style.md](references/style.md) when preparing the final candidate.
   - Treat hard violations as blockers. Treat style warnings as post-pass cleanup only.

8. Evaluate with the real local toolchain.
   - Use `scripts/evaluate_candidate.py` to compile and run the candidate on all available cases.
   - Keep working source files in UTF-8 during generation and repair.
   - Prefer `-finput-charset=UTF-8 -fexec-charset=GBK` on Windows while evaluating UTF-8 working files.
   - Compare candidate output against `demo.exe` with `txt_compare.exe` when available.
   - Store per-case `input.txt`, `expected.txt`, `actual.txt`, and compare logs in the workspace.
   - Run dependent stages sequentially: testcase bundle construction before demo observation, and evaluation before failure summarization.

9. Feed back only compact failures.
   - Use `scripts/summarize_failures.py` to convert evaluation output into compact feedback items.
   - Do not paste full raw logs back into the next generation step unless the compact summary is insufficient.
   - Prioritize compile errors, first mismatching cases, expected vs actual previews, and hard constraint violations.

10. Humanize only after the code already passes.
   - Make the code less polished only after the baseline candidate passes evaluation.
   - Re-run `check_constraints.py` and `evaluate_candidate.py` after every style downgrade.
   - Never preserve humanization edits that break correctness.

11. Export the submission format only after the final candidate already passes.
   - Use `scripts/export_submission.py` to convert the final UTF-8 source files into the required submission encoding and line endings.
   - Default submission export for this coursework family is `GB2312 + CRLF` unless the statement says otherwise.
   - Preserve the exact required source filenames and extensions in the exported files.
   - If export fails because a character cannot be encoded as `GB2312`, treat that as a blocker and repair the source text.
   - Re-run `scripts/evaluate_candidate.py` on the exported files with `--source-input-charset=GB2312` before declaring the submission ready.

## Scripts

- `scripts/init_workspace.py`
  Create a numbered workspace with the standard folder layout and a run manifest.
- `scripts/extract_problem.py`
  Copy the source statement into the workspace and build `problem_context.md` using the local PDF-reading path when available, without requiring external PDF-to-text tools.
- `scripts/build_testcases.py`
  Build the testcase bundle by extracting official grouped data with `get_input_data.exe` when available, then merge supplemental or generated cases.
- `scripts/parse_grouped_cases.py`
  Parse `[group]`-style testcase files into JSON cases as a fallback when `get_input_data.exe` is unavailable.
- `scripts/observe_demo.py`
  Run `demo.exe` on representative cases and save observable behavior for prompt grounding.
- `scripts/check_constraints.py`
  Detect inferred hard bans and style warnings from the problem text and generated code.
- `scripts/evaluate_candidate.py`
  Compile candidate `.c` or `.cpp` files, run `demo.exe` and the candidate, compare outputs, and emit an evaluation summary.
- `scripts/export_submission.py`
  Export final source files into the required submission encoding and line endings, such as `GB2312 + CRLF`.
- `scripts/summarize_failures.py`
  Turn evaluation artifacts into short retry feedback.

## References

- Read [references/workflow.md](references/workflow.md) for the full end-to-end loop and artifact expectations.
- Read [references/workspace-layout.md](references/workspace-layout.md) when you need a stable directory convention.
- Read [references/windows-encoding.md](references/windows-encoding.md) when console encoding or Chinese text is involved.
- Read [references/submission-format.md](references/submission-format.md) when preparing the final deliverable for upload.
- Read [references/constraints.md](references/constraints.md) when the statement includes syntax bans or style constraints.
- Read [references/style.md](references/style.md) when enforcing identifier and brace style.

## Operating Rules

- Prefer the local workspace as the source of truth over memory.
- Preserve raw artifacts. Do not hide failed runs.
- Keep the skill lightweight: Codex does the reasoning; scripts do deterministic work.
- If a required Windows binary is missing, report which one is missing and continue with the best fallback that does not fake correctness.
