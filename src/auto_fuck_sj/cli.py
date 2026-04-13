from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .models import RunRequest, SubmissionTarget, ToolConfig
from .orchestrator import AutomaticGC


def _add_common_run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--problem", required=True, type=Path, help="Problem file path")
    parser.add_argument("--demo", required=True, type=Path, help="Path to demo.exe")
    parser.add_argument(
        "--demo-arg",
        action="append",
        default=[],
        help="Extra argument passed to demo.exe, repeatable",
    )
    parser.add_argument("--data", type=Path, help="Optional grouped testcase file")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path("workspaces"),
        help="Workspace root directory",
    )
    parser.add_argument(
        "--cpp-name",
        action="append",
        default=[],
        help="Expected generated .cpp filename, repeatable",
    )
    parser.add_argument(
        "--entry-cpp",
        help="Preferred entry cpp filename when multiple files are generated",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Maximum solver attempts",
    )
    parser.add_argument(
        "--generated-cases",
        type=int,
        default=5,
        help="How many Codex-generated cases to request",
    )
    parser.add_argument(
        "--ban-token",
        action="append",
        default=[],
        help="Extra forbidden token, repeatable",
    )
    parser.add_argument("--ai-backend", default="codex", choices=["codex", "kimi"],
                        help="AI backend to use (default: codex)")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--codex-model")
    parser.add_argument("--kimi-model", help="Kimi model name (e.g., kimi-k2-0711-preview)")
    parser.add_argument("--gpp-bin", default="g++")
    parser.add_argument("--txt-compare-bin", default="txt_compare.exe")
    parser.add_argument("--get-input-data-bin", default="get_input_data.exe")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="auto_fuck_sj MVP orchestrator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a single solving job")
    _add_common_run_arguments(run_parser)

    regression_parser = subparsers.add_parser(
        "run-regression",
        help="Run a sequence of solving jobs from a JSON spec",
    )
    regression_parser.add_argument("--spec", required=True, type=Path, help="Regression spec JSON path")
    regression_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path("workspaces"),
        help="Workspace root directory",
    )
    regression_parser.add_argument("--ai-backend", default="codex", choices=["codex", "kimi"],
                                   help="AI backend to use (default: codex)")
    regression_parser.add_argument("--codex-bin", default="codex")
    regression_parser.add_argument("--codex-model")
    regression_parser.add_argument("--kimi-model", help="Kimi model name (e.g., kimi-k2-0711-preview)")
    regression_parser.add_argument("--gpp-bin", default="g++")
    regression_parser.add_argument("--txt-compare-bin", default="txt_compare.exe")
    regression_parser.add_argument("--get-input-data-bin", default="get_input_data.exe")
    return parser


def _build_request(args: argparse.Namespace) -> RunRequest:
    cpp_names = args.cpp_name or ["main.cpp"]
    return RunRequest(
        problem_file=args.problem.resolve(),
        demo_exe=args.demo.resolve(),
        demo_args=list(args.demo_arg),
        data_file=args.data.resolve() if args.data else None,
        workspace_root=args.workspace_root.resolve(),
        submission_targets=[SubmissionTarget(filename=name) for name in cpp_names],
        entry_cpp=args.entry_cpp,
        max_attempts=args.max_attempts,
        generated_cases=args.generated_cases,
        extra_banned_tokens=args.ban_token,
    )


def _build_tools(args: argparse.Namespace) -> ToolConfig:
    return ToolConfig(
        ai_backend=args.ai_backend,
        codex_bin=args.codex_bin,
        gpp_bin=args.gpp_bin,
        txt_compare_bin=args.txt_compare_bin,
        get_input_data_bin=args.get_input_data_bin,
        codex_model=args.codex_model,
        kimi_model=args.kimi_model,
    )


def _load_regression_jobs(spec_path: Path, workspace_root: Path) -> list[RunRequest]:
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    jobs = payload.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ValueError(f"Regression spec {spec_path} must contain a non-empty 'jobs' array.")

    requests: list[RunRequest] = []
    for index, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            raise ValueError(f"Job #{index} in {spec_path} must be an object.")

        cpp_names = job.get("cpp_names")
        if not cpp_names:
            cpp_name = job.get("cpp_name")
            cpp_names = [cpp_name] if cpp_name else ["main.cpp"]
        requests.append(
            RunRequest(
                problem_file=Path(job["problem"]).resolve(),
                demo_exe=Path(job["demo"]).resolve(),
                demo_args=list(job.get("demo_args", [])),
                data_file=Path(job["data"]).resolve() if job.get("data") else None,
                workspace_root=workspace_root.resolve(),
                submission_targets=[SubmissionTarget(filename=name) for name in cpp_names],
                entry_cpp=job.get("entry_cpp"),
                max_attempts=int(job.get("max_attempts", 3)),
                generated_cases=int(job.get("generated_cases", 5)),
                extra_banned_tokens=list(job.get("ban_tokens", [])),
            )
        )
    return requests


def _run_regression(args: argparse.Namespace) -> dict[str, Any]:
    tools = _build_tools(args)
    requests = _load_regression_jobs(args.spec.resolve(), args.workspace_root)

    results: list[dict[str, Any]] = []
    passed = 0
    for request in requests:
        result = AutomaticGC(request=request, tools=tools).run()
        results.append(
            {
                "job": request.job_label(),
                "problem_file": str(request.problem_file),
                "demo_exe": str(request.demo_exe),
                "demo_args": list(request.demo_args),
                "result": result,
            }
        )
        if result.get("status") == "passed":
            passed += 1

    return {
        "status": "passed" if passed == len(results) else "failed",
        "passed_jobs": passed,
        "total_jobs": len(results),
        "results": results,
    }


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        request = _build_request(args)
        tools = _build_tools(args)
        result = AutomaticGC(request=request, tools=tools).run()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "run-regression":
        result = _run_regression(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    parser.error(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()

