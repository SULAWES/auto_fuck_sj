# Submission Format

Many coursework platforms care about the final uploaded source file format separately from the internal working format.

Use this rule set unless the statement explicitly overrides it:

- Keep the editable working files in UTF-8.
- Export the final submission copy as `GB2312 + CRLF`.
- Preserve the exact required filenames and extensions such as `5-b16-1.c` or `5-b16-2.cpp`.
- Treat export failures as blockers. Do not silently replace or drop characters.
- After export, run at least one compile check on the exported files.
- Prefer re-running the full local evaluation on the exported files with `--source-input-charset=GB2312`.

Recommended sequence:

1. Generate and repair the candidate in UTF-8.
2. Run constraint checks on the UTF-8 working files.
3. Run full evaluation on the UTF-8 working files.
4. Export with `scripts/export_submission.py`.
5. Re-run evaluation on the exported files with `--source-input-charset=GB2312`.
6. Deliver the exported files, not the working copies.
