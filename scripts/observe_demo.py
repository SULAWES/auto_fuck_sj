#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import run_binary_command, write_json


def load_cases(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        cases = payload.get("cases", [])
        if isinstance(cases, list):
            return cases
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Unsupported cases payload in {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Observe demo.exe behavior on representative cases.")
    parser.add_argument("--demo", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--demo-arg", action="append", default=[])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--timeout-sec", type=int, default=10)
    args = parser.parse_args()

    cases = load_cases(args.cases.resolve())
    selected = cases[: max(args.limit, 0)]
    observations: list[dict] = []
    command = [str(args.demo.resolve()), *args.demo_arg]
    for case in selected:
        result = run_binary_command(
            command,
            cwd=args.output.resolve().parent,
            input_text=case["input_text"],
            timeout_sec=args.timeout_sec,
        )
        observations.append(
            {
                "name": case["name"],
                "source": case.get("source", "unknown"),
                "input_text": case["input_text"],
                "demo_stdout": result["stdout_text"],
                "demo_stderr": result["stderr_text"],
                "returncode": result["returncode"],
                "timed_out": result["timed_out"],
                "demo_args": list(args.demo_arg),
            }
        )
    write_json(args.output.resolve(), observations)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
