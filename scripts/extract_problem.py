#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

from common import read_text_best_effort, run_text_command, write_json


def extract_pdf_text_with_pypdf(problem_path: Path) -> tuple[str, str]:
    try:
        from pypdf import PdfReader
    except Exception as exc:
        return "", f"pypdf unavailable in current interpreter: {exc}"

    try:
        reader = PdfReader(str(problem_path))
        text_parts: list[str] = []
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
        text = "\n".join(part for part in text_parts if part).strip()
        if text:
            return text, "Extracted text with pypdf in the current Python interpreter."
        return "", "pypdf loaded, but the PDF text layer was empty."
    except Exception as exc:
        return "", f"pypdf extraction failed: {exc}"


def find_bundled_node_executable() -> Path | None:
    candidates = [
        Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "bin" / "node.exe",
        Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "bin" / "node",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def find_bundled_pdfjs_dir() -> Path | None:
    candidate = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "node_modules" / "pdfjs-dist"
    if candidate.exists():
        return candidate
    return None


def extract_pdf_text_with_pdfjs(
    problem_path: Path,
    extracted_dir: Path,
    timeout_sec: int,
    output_name: str = "problem_text.txt",
) -> tuple[str, str]:
    node_executable = find_bundled_node_executable()
    pdfjs_dir = find_bundled_pdfjs_dir()
    if node_executable is None or pdfjs_dir is None:
        return "", "Bundled Node.js PDF reader is unavailable."

    script_path: Path | None = None
    output_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".mjs", encoding="utf-8", delete=False, dir=extracted_dir) as script_file:
            script_path = Path(script_file.name)
            output_path = extracted_dir / output_name
            script_file.write(
                "\n".join(
                    [
                        "import fs from 'fs';",
                        "import { pathToFileURL } from 'url';",
                        "",
                        "globalThis.DOMMatrix = globalThis.DOMMatrix || class {};",
                        "globalThis.ImageData = globalThis.ImageData || class {};",
                        "globalThis.Path2D = globalThis.Path2D || class {};",
                        "",
                        f"const pdfjsEntry = {json.dumps(str((pdfjs_dir / 'legacy' / 'build' / 'pdf.mjs').resolve()).replace('\\\\', '/'))};",
                        "const pdfjs = await import(pathToFileURL(pdfjsEntry).href);",
                        f"const inputPdf = {json.dumps(str(problem_path.resolve()))};",
                        f"const outputFile = {json.dumps(str(output_path.resolve()))};",
                        "const data = new Uint8Array(fs.readFileSync(inputPdf));",
                        "const doc = await pdfjs.getDocument({ data, useWorkerFetch: false, isEvalSupported: false }).promise;",
                        "const pageTexts = [];",
                        "for (let pageIndex = 1; pageIndex <= doc.numPages; pageIndex += 1)",
                        "{",
                        "  const page = await doc.getPage(pageIndex);",
                        "  const content = await page.getTextContent();",
                        "  const text = content.items.map((item) => item.str || '').join(' ').trim();",
                        "  if (text)",
                        "  {",
                        "    pageTexts.push(text);",
                        "  }",
                        "}",
                        "fs.writeFileSync(outputFile, pageTexts.join('\\n\\n'), 'utf8');",
                        "console.log(outputFile);",
                    ]
                )
            )

        result = run_text_command(
            [str(node_executable), str(script_path)],
            cwd=extracted_dir,
            timeout_sec=timeout_sec,
            encoding="utf-8",
        )
        if result["returncode"] != 0:
            return "", f"Bundled pdfjs extraction failed: {result['stderr'] or result['stdout']}".strip()

        if output_path.exists():
            text = output_path.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                return text, "Extracted text with bundled Node.js and pdfjs-dist."
            return "", "Bundled pdfjs ran, but the PDF text layer was empty."
        return "", "Bundled pdfjs did not produce a text artifact."
    finally:
        if script_path and script_path.exists():
            script_path.unlink(missing_ok=True)


def extract_problem_text(
    problem_path: Path,
    extracted_dir: Path,
    timeout_sec: int,
    output_name: str = "problem_text.txt",
) -> tuple[str, str]:
    suffix = problem_path.suffix.lower()
    if suffix in {".txt", ".md", ".c", ".cpp", ".h", ".hpp"}:
        text, encoding = read_text_best_effort(problem_path)
        return text, f"Loaded text directly with {encoding}."

    if suffix != ".pdf":
        return "", f"Unsupported problem format: {suffix}"

    attempts: list[str] = []

    text, note = extract_pdf_text_with_pypdf(problem_path)
    attempts.append(note)
    if text:
        return text, note

    text, note = extract_pdf_text_with_pdfjs(problem_path, extracted_dir, timeout_sec, output_name)
    attempts.append(note)
    if text:
        return text, note

    combined_notes = " ".join(note for note in attempts if note).strip()
    fallback = "PDF text extraction did not succeed. Continue with the copied PDF, pre-PDF constraints, any supplied text companion, official testcases, and demo behavior."
    return "", f"{combined_notes} {fallback}".strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy and extract a coursework problem statement.")
    parser.add_argument("--problem", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--pre-constraint-file", type=Path, action="append", default=[])
    parser.add_argument("--problem-text-file", type=Path, action="append", default=[])
    parser.add_argument("--reference-assignment-file", type=Path, action="append", default=[])
    parser.add_argument("--demo-name")
    parser.add_argument("--demo-arg", action="append", default=[])
    parser.add_argument("--cpp-name", action="append", default=[])
    parser.add_argument("--timeout-sec", type=int, default=30)
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

    supplemental_sections: list[str] = []
    copied_problem_text_files: list[str] = []
    for text_path in args.problem_text_file:
        copied_text = input_dir / text_path.name
        shutil.copy2(text_path, copied_text)
        copied_problem_text_files.append(str(copied_text))
        statement_text, statement_encoding = read_text_best_effort(copied_text)
        supplemental_sections.extend(
            [
                f"### {copied_text.name}",
                f"Loaded with {statement_encoding}.",
                "",
                statement_text,
                "",
            ]
        )

    reference_sections: list[str] = []
    copied_reference_files: list[str] = []
    for index, reference_path in enumerate(args.reference_assignment_file, start=1):
        copied_reference = input_dir / reference_path.name
        shutil.copy2(reference_path, copied_reference)
        copied_reference_files.append(str(copied_reference))
        reference_text, reference_note = extract_problem_text(
            copied_reference,
            extracted_dir,
            args.timeout_sec,
            f"reference_{index:02d}_text.txt",
        )
        reference_sections.extend(
            [
                f"### {copied_reference.name}",
                reference_note,
                "",
                reference_text or "Reference text unavailable. Use the copied artifact only for manual review.",
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
            "## Extracted Problem Text",
            "",
            extracted_text or "Extraction unavailable. Read the copied problem file directly if needed.",
            "",
            "## Supplemental Statement Text",
            "",
            *(
                supplemental_sections
                if supplemental_sections
                else ["No separate problem text companion files were provided."]
            ),
            "",
            "## Reference Assignments",
            "",
            *(
                reference_sections
                if reference_sections
                else ["No optional previous-assignment reference files were provided."]
            ),
            "",
            "## Extraction Notes",
            "",
            notes or "No extraction notes.",
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
            "problem_text_files": [str(path.resolve()) for path in args.problem_text_file],
            "copied_problem_text_files": copied_problem_text_files,
            "reference_assignment_files": [str(path.resolve()) for path in args.reference_assignment_file],
            "copied_reference_assignment_files": copied_reference_files,
            "notes": notes,
            "demo_name": demo_text,
            "demo_args": list(args.demo_arg),
            "cpp_names": list(args.cpp_name),
            "timeout_sec": args.timeout_sec,
        },
    )
    print(extracted_dir / "problem_context.md")


if __name__ == "__main__":
    main()
