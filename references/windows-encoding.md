# Windows Encoding

Coursework assignments in Chinese often fail for encoding reasons rather than logic reasons.

Use these rules:

- Keep source files in UTF-8.
- Compile with:
  - `-finput-charset=UTF-8`
  - `-fexec-charset=GBK`
- Export the final submission copy separately when the assignment requires `GB2312 (SYS)` or another legacy encoding.
- Treat the Windows preferred locale encoding as the default for process stdin and stdout.
- When capturing binary process output, preserve raw bytes and decode with replacement only for logs.
- Compare files on disk rather than normalizing process text in memory when correctness matters.

Common failure modes:

- The candidate prints correct Chinese text but the byte encoding differs from `demo.exe`.
- The shell decodes `stderr` or `stdout` with the wrong codec and produces misleading logs.
- An AI-generated file contains mojibake because the model or terminal emitted non-UTF-8 text.
- The final submitted file uses UTF-8 or LF even though the coursework checker expects `GB2312 + CRLF`.

When in doubt:

1. Save raw bytes.
2. Decode only for human-readable logs.
3. Compare the written files.
4. Export the final submission copy separately and validate that exported copy again.
