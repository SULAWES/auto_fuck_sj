#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import read_text_best_effort, write_json


def extract_compare_hint(compare_stdout: str) -> str:
    for line in compare_stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("第[") or stripped.startswith("在指定检查条件下"):
            return stripped
    return ""


def read_output_preview(file_path: str) -> str:
    if not file_path:
        return ""
    path = Path(file_path)
    if not path.exists() or path.is_dir():
        return ""
    try:
        text, _ = read_text_best_effort(path)
    except OSError:
        return ""
    preview_lines = [(line if line else "<EMPTY>") for line in text.splitlines()[:3]]
    return " | ".join(preview_lines).strip()[:240]


def summarize_failure(failure: dict) -> str:
    parts = [f"Case {failure['case_name']} failed: {failure['reason']}."]
    compare_hint = extract_compare_hint(failure.get("compare_stdout", ""))
    if compare_hint:
        parts.append(f"Compare hint: {compare_hint}.")
    expected_preview = read_output_preview(failure.get("expected_file", ""))
    if expected_preview:
        parts.append(f"Expected preview: {expected_preview}")
    actual_preview = read_output_preview(failure.get("actual_file", ""))
    if actual_preview:
        parts.append(f"Actual preview: {actual_preview}")
    compare_stderr = failure.get("compare_stderr", "").strip()
    if compare_stderr:
        parts.append(f"Compare stderr: {compare_stderr[:240]}")
    return " ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize evaluation failures into compact feedback items.")
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--constraints", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    evaluation = json.loads(args.evaluation.resolve().read_text(encoding="utf-8"))
    feedback: list[str] = []
    if not evaluation.get("compile_ok"):
        feedback.append("Previous attempt did not compile. Fix compilation errors first.")
        compile_stderr = evaluation.get("compile_result", {}).get("stderr", "")
        if compile_stderr:
            feedback.append(f"Compiler stderr:\n{compile_stderr}")
    else:
        for failure in evaluation.get("failures", [])[: max(args.limit, 0)]:
            feedback.append(summarize_failure(failure))

    if args.constraints and args.constraints.exists():
        constraints = json.loads(args.constraints.resolve().read_text(encoding="utf-8"))
        for violation in constraints.get("hard_violations", []):
            feedback.append(f"Hard constraint violation: {violation}")

    if not feedback:
        feedback.append("Improve overall robustness. Previous attempt still did not pass.")

    payload = {"feedback_items": feedback}
    write_json(args.output.resolve(), payload)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
