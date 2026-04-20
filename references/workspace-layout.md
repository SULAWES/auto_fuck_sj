# Workspace Layout

Use a numbered workspace for every run.

Suggested layout:

```text
workspaces/000001/
  input/
  extracted/
  testcases/
  candidates/
  outputs/
  logs/
  final/
    submission/
  run_manifest.json
```

Recommended conventions:

- `input/`
  Original copied inputs such as the problem file, `demo.exe`, and grouped testcase data.
- `extracted/`
  `problem_text.txt`, `problem_context.md`, and extraction metadata.
- `testcases/`
  Provided cases, generated cases, filtered selections, and demo observations.
- `candidates/attempt_XX/`
  Candidate `.cpp` files and any generation notes.
- `outputs/attempt_XX/`
  `candidate.exe`, compile logs, evaluation summary, constraint report, and per-case details.
- `logs/`
  Extra command output and debugging artifacts.
- `final/`
  The final UTF-8 source files that survived validation.
- `final/submission/`
  Exported submission files, typically `GB2312 + CRLF`, ready for upload after re-validation.

Keep filenames stable and descriptive. Do not overwrite one attempt with another.
