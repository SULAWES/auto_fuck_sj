from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import RunRequest, SubmissionTarget, ToolConfig
from .orchestrator import AutomaticGC


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="automatic_gc MVP orchestrator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a single solving job")
    run_parser.add_argument("--problem", required=True, type=Path, help="Problem file path")
    run_parser.add_argument("--demo", required=True, type=Path, help="Path to demo.exe")
    run_parser.add_argument("--data", type=Path, help="Optional grouped testcase file")
    run_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path("workspaces"),
        help="Workspace root directory",
    )
    run_parser.add_argument(
        "--cpp-name",
        action="append",
        default=[],
        help="Expected generated .cpp filename, repeatable",
    )
    run_parser.add_argument(
        "--entry-cpp",
        help="Preferred entry cpp filename when multiple files are generated",
    )
    run_parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Maximum solver attempts",
    )
    run_parser.add_argument(
        "--generated-cases",
        type=int,
        default=5,
        help="How many Codex-generated cases to request",
    )
    run_parser.add_argument(
        "--ban-token",
        action="append",
        default=[],
        help="Extra forbidden token, repeatable",
    )
    run_parser.add_argument("--codex-bin", default="codex")
    run_parser.add_argument("--codex-model")
    run_parser.add_argument("--gpp-bin", default="g++")
    run_parser.add_argument("--txt-compare-bin", default="txt_compare.exe")
    run_parser.add_argument("--get-input-data-bin", default="get_input_data.exe")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command != "run":
        parser.error(f"Unsupported command: {args.command}")

    cpp_names = args.cpp_name or ["main.cpp"]
    request = RunRequest(
        problem_file=args.problem.resolve(),
        demo_exe=args.demo.resolve(),
        data_file=args.data.resolve() if args.data else None,
        workspace_root=args.workspace_root.resolve(),
        submission_targets=[SubmissionTarget(filename=name) for name in cpp_names],
        entry_cpp=args.entry_cpp,
        max_attempts=args.max_attempts,
        generated_cases=args.generated_cases,
        extra_banned_tokens=args.ban_token,
    )
    tools = ToolConfig(
        codex_bin=args.codex_bin,
        gpp_bin=args.gpp_bin,
        txt_compare_bin=args.txt_compare_bin,
        get_input_data_bin=args.get_input_data_bin,
        codex_model=args.codex_model,
    )

    result = AutomaticGC(request=request, tools=tools).run()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
