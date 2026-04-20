#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from common import read_text_best_effort, run_text_command, write_json


def extract_problem_text(problem_path: Path, extracted_dir: Path, timeout_sec: int) -> tuple[str, str]:
    suffix = problem_path.suffix.lower()
    if suffix in {".txt", ".md"}:
        text, encoding = read_text_best_effort(problem_path)
        return text, f"Loaded text directly with {encoding}."

    if suffix != ".pdf":
        return "", f"Unsupported problem format: {suffix}"

    output_text_path = extracted_dir / "problem_text.txt"
    extractors = [
        ["pdftotext", "-layout", "-nopgbrk", str(problem_path), str(output_text_path)],
        ["mutool", "draw", "-F", "txt", "-o", str(output_text_path), str(problem_path)],
    ]
    for command in extractors:
        if shutil.which(command[0]) is None:
            continue
        result = run_text_command(command, cwd=extracted_dir, timeout_sec=timeout_sec)
        if result["returncode"] == 0 and output_text_path.exists():
            return output_text_path.read_text(encoding="utf-8", errors="replace"), f"Extracted text with {command[0]}."

    return "", "No supported PDF extractor found. Continue with the copied source file."


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy and extract a coursework problem statement.")
    parser.add_argument("--problem", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--pre-constraint-file", type=Path, action="append", default=[])
    parser.add_argument("--demo-name")
    parser.add_argument("--demo-arg", action="append", default=[])
    parser.add_argument("--cpp-name", action="append", default=[])
    parser.add_argument("--timeout-sec", type=int, default=20)
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    input_dir = workspace / "input"
    extracted_dir = workspace / "extracted"
    input_dir.mkdir(parents=True, exist_ok=True)
    extracted_dir.mkdir(parents=True, exist_ok=True)

    copied_problem = input_dir / args.problem.name
    shutil.copy2(args.problem, copied_problem)

    constraint_sections: list[str] = []
    copied_constraint_files: list[str] = []
    for constraint_path in args.pre_constraint_file:
        copied_constraint = input_dir / constraint_path.name
        shutil.copy2(constraint_path, copied_constraint)
        copied_constraint_files.append(str(copied_constraint))
        constraint_text, constraint_encoding = read_text_best_effort(copied_constraint)
        constraint_sections.extend(
            [
                f"### {copied_constraint.name}",
                f"Loaded with {constraint_encoding}.",
                "",
                constraint_text,
                "",
            ]
        )

    extracted_text, notes = extract_problem_text(copied_problem, extracted_dir, args.timeout_sec)
    demo_text = args.demo_name or "(unknown)"
    demo_args_text = " ".join(args.demo_arg) if args.demo_arg else "(none)"
    expected_files = "\n".join(f"- {name}" for name in (args.cpp_name or ["main.cpp"]))
    context = "\n".join(
        [
            "# Problem Context",
            "",
            f"- Original problem file: `{copied_problem.name}`",
            f"- Demo executable: `{demo_text}`",
            f"- Demo arguments: `{demo_args_text}`",
            "- Expected source files:",
            expected_files,
            "",
            "## Pre-PDF Constraints",
            "",
            *(
                constraint_sections
                if constraint_sections
                else ["No separate pre-PDF constraint files were provided."]
            ),
            "",
            "## Extraction Notes",
            "",
            notes or "No extraction notes.",
            "",
            "## Extracted Problem Text",
            "",
            extracted_text or "Extraction unavailable. Read the copied problem file directly if needed.",
        ]
    )

    (extracted_dir / "problem_context.md").write_text(context, encoding="utf-8")
    write_json(
        extracted_dir / "extract_metadata.json",
        {
            "problem_file": str(args.problem.resolve()),
            "copied_problem": str(copied_problem),
            "pre_constraint_files": [str(path.resolve()) for path in args.pre_constraint_file],
            "copied_pre_constraint_files": copied_constraint_files,
            "notes": notes,
            "demo_name": demo_text,
            "demo_args": list(args.demo_arg),
            "cpp_names": list(args.cpp_name),
        },
    )
    print(extracted_dir / "problem_context.md")


if __name__ == "__main__":
    main()
