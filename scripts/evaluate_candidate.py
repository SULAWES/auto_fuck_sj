#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from common import infer_compare_match, read_text_best_effort, run_binary_command, run_text_command, safe_case_name, write_json


def load_cases(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        cases = payload.get("cases", [])
        if isinstance(cases, list):
            return cases
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Unsupported cases payload in {path}")


def compare_outputs(actual_path: Path, expected_path: Path, *, txt_compare_bin: str, case_dir: Path) -> dict:
    compare_command = [
        txt_compare_bin,
        "--file1",
        str(actual_path),
        "--file2",
        str(expected_path),
        "--trim",
        "right",
        "--display",
        "normal",
        "--ignore_blank",
    ]
    compare_result_path = case_dir / "compare_result.json"
    if shutil.which(txt_compare_bin):
        result = run_text_command(compare_command, cwd=case_dir, timeout_sec=10)
        payload = dict(result)
        payload["matched"] = infer_compare_match(result["stdout"], result["stderr"], result["returncode"])
        write_json(compare_result_path, payload)
        return {
            "matched": payload["matched"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
        }

    actual, _ = read_text_best_effort(actual_path)
    expected, _ = read_text_best_effort(expected_path)
    matched = actual.rstrip() == expected.rstrip()
    payload = {
        "command": compare_command,
        "fallback": "txt_compare.exe not found in PATH, used Python fallback",
        "matched": matched,
    }
    write_json(compare_result_path, payload)
    return {"matched": matched, "stdout": json.dumps(payload, ensure_ascii=False), "stderr": ""}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile and evaluate candidate coursework C or C++ files.")
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--demo", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--demo-arg", action="append", default=[])
    parser.add_argument("--gpp-bin", default="g++")
    parser.add_argument("--gcc-bin", default="gcc")
    parser.add_argument("--txt-compare-bin", default="txt_compare.exe")
    parser.add_argument("--source-input-charset", default="UTF-8")
    parser.add_argument("--compile-timeout-sec", type=int, default=30)
    parser.add_argument("--run-timeout-sec", type=int, default=10)
    args = parser.parse_args()

    candidate_dir = args.candidate_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    compile_log_path = output_dir / "compile_result.json"
    executable_path = output_dir / "candidate.exe"

    c_files = sorted(candidate_dir.glob("*.c"))
    cpp_files = sorted(candidate_dir.glob("*.cpp"))
    source_files = [*c_files, *cpp_files]
    if not source_files:
        write_json(
            compile_log_path,
            {"error": "No .c or .cpp files generated", "candidate_dir": str(candidate_dir)},
        )
        write_json(
            output_dir / "evaluation_summary.json",
            {
                "compile_ok": False,
                "all_passed": False,
                "tested_case_count": 0,
                "compile_result": {"error": "No .c or .cpp files generated"},
                "failures": [],
                "notes": ["Candidate directory does not contain any .c or .cpp files."],
            },
        )
        print(output_dir / "evaluation_summary.json")
        return

    if cpp_files:
        compile_command = [
            args.gpp_bin,
            "-std=c++17",
            f"-finput-charset={args.source_input_charset}",
            "-fexec-charset=GBK",
            "-O2",
            "-Wall",
            "-Wextra",
            "-o",
            str(executable_path),
            *[str(path) for path in source_files],
        ]
    else:
        compile_command = [
            args.gcc_bin,
            "-std=c11",
            f"-finput-charset={args.source_input_charset}",
            "-fexec-charset=GBK",
            "-O2",
            "-Wall",
            "-Wextra",
            "-o",
            str(executable_path),
            *[str(path) for path in source_files],
        ]
    compile_result = run_text_command(compile_command, cwd=candidate_dir, timeout_sec=args.compile_timeout_sec)
    write_json(compile_log_path, compile_result)
    if compile_result["returncode"] != 0:
        write_json(
            output_dir / "evaluation_summary.json",
            {
                "compile_ok": False,
                "all_passed": False,
                "tested_case_count": 0,
                "compile_result": compile_result,
                "failures": [],
                "notes": ["Compilation failed."],
            },
        )
        print(output_dir / "evaluation_summary.json")
        return

    cases = load_cases(args.cases.resolve())
    if not cases:
        write_json(
            output_dir / "evaluation_summary.json",
            {
                "compile_ok": True,
                "all_passed": True,
                "tested_case_count": 0,
                "compile_result": compile_result,
                "failures": [],
                "notes": ["No testcases available. Compile-only pass."],
            },
        )
        print(output_dir / "evaluation_summary.json")
        return

    failures: list[dict] = []
    demo_command = [str(args.demo.resolve()), *args.demo_arg]
    for index, case in enumerate(cases, start=1):
        case_dir = output_dir / "cases" / f"{index:03d}_{safe_case_name(case['name'])}"
        case_dir.mkdir(parents=True, exist_ok=True)
        input_path = case_dir / "input.txt"
        expected_path = case_dir / "expected.txt"
        actual_path = case_dir / "actual.txt"
        demo_stderr_path = case_dir / "demo_stderr.txt"
        candidate_stderr_path = case_dir / "candidate_stderr.txt"

        input_text = case["input_text"]
        input_path.write_text(input_text, encoding="utf-8")

        demo_result = run_binary_command(demo_command, cwd=case_dir, input_text=input_text, timeout_sec=args.run_timeout_sec)
        expected_path.write_bytes(demo_result["stdout_bytes"])
        demo_stderr_path.write_text(demo_result["stderr_text"], encoding="utf-8")
        if demo_result["returncode"] != 0:
            failures.append(
                {
                    "case_name": case["name"],
                    "reason": "demo.exe failed",
                    "compare_stdout": demo_result["stdout_text"],
                    "compare_stderr": demo_result["stderr_text"],
                    "expected_file": str(expected_path),
                    "actual_file": "",
                }
            )
            continue

        candidate_result = run_binary_command([str(executable_path)], cwd=case_dir, input_text=input_text, timeout_sec=args.run_timeout_sec)
        actual_path.write_bytes(candidate_result["stdout_bytes"])
        candidate_stderr_path.write_text(candidate_result["stderr_text"], encoding="utf-8")
        if candidate_result["returncode"] != 0:
            failures.append(
                {
                    "case_name": case["name"],
                    "reason": "candidate program failed",
                    "compare_stdout": candidate_result["stdout_text"],
                    "compare_stderr": candidate_result["stderr_text"],
                    "expected_file": str(expected_path),
                    "actual_file": str(actual_path),
                }
            )
            continue

        compare_result = compare_outputs(actual_path, expected_path, txt_compare_bin=args.txt_compare_bin, case_dir=case_dir)
        if not compare_result["matched"]:
            failures.append(
                {
                    "case_name": case["name"],
                    "reason": "output mismatch",
                    "compare_stdout": compare_result["stdout"],
                    "compare_stderr": compare_result["stderr"],
                    "expected_file": str(expected_path),
                    "actual_file": str(actual_path),
                }
            )

    write_json(
        output_dir / "evaluation_summary.json",
        {
            "compile_ok": True,
            "all_passed": not failures,
            "tested_case_count": len(cases),
            "compile_result": compile_result,
            "failures": failures,
            "notes": [] if failures else ["All available testcases passed."],
        },
    )
    print(output_dir / "evaluation_summary.json")


if __name__ == "__main__":
    main()
