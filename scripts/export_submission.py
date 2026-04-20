#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import write_json


def normalize_line_endings(text: str, line_ending: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if normalized and not normalized.endswith("\n"):
        normalized += "\n"
    if line_ending.lower() == "crlf":
        return normalized.replace("\n", "\r\n")
    if line_ending.lower() == "lf":
        return normalized
    raise ValueError(f"Unsupported line ending: {line_ending}")


def describe_unencodable_characters(text: str, encoding: str) -> list[dict]:
    issues: list[dict] = []
    line_number = 1
    column_number = 1
    for ch in text:
        try:
            ch.encode(encoding)
        except UnicodeEncodeError:
            issues.append(
                {
                    "line": line_number,
                    "column": column_number,
                    "character": ch,
                    "code_point": f"U+{ord(ch):04X}",
                }
            )
        if ch == "\n":
            line_number += 1
            column_number = 1
        else:
            column_number += 1
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Export final submission files with the required encoding and line endings.")
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--encoding", default="gb2312")
    parser.add_argument("--line-ending", default="crlf")
    args = parser.parse_args()

    candidate_dir = args.candidate_dir.resolve()
    output_dir = args.output_dir.resolve()
    report_path = args.report.resolve() if args.report else (output_dir / "export_report.json")
    output_dir.mkdir(parents=True, exist_ok=True)

    source_files = sorted(candidate_dir.glob("*.c")) + sorted(candidate_dir.glob("*.cpp"))
    exported_files: list[dict] = []
    failures: list[dict] = []

    for source_path in source_files:
        text = source_path.read_text(encoding="utf-8", errors="strict")
        normalized_text = normalize_line_endings(text, args.line_ending)
        issues = describe_unencodable_characters(normalized_text, args.encoding)
        if issues:
            failures.append(
                {
                    "file": str(source_path),
                    "reason": f"Cannot encode file as {args.encoding}",
                    "issues": issues[:20],
                }
            )
            continue

        destination_path = output_dir / source_path.name
        destination_path.write_bytes(normalized_text.encode(args.encoding))
        exported_files.append(
            {
                "source_file": str(source_path),
                "exported_file": str(destination_path),
                "encoding": args.encoding,
                "line_ending": args.line_ending.upper(),
            }
        )

    payload = {
        "success": not failures,
        "candidate_dir": str(candidate_dir),
        "output_dir": str(output_dir),
        "encoding": args.encoding,
        "line_ending": args.line_ending.upper(),
        "exported_files": exported_files,
        "failures": failures,
    }
    write_json(report_path, payload)
    print(report_path)


if __name__ == "__main__":
    main()
