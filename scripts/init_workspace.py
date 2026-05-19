#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import write_json


LAYOUT = [
    "input",
    "extracted",
    "testcases",
    "candidates",
    "outputs",
    "logs",
    "final",
]


def create_workspace(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    existing = sorted(int(path.name) for path in root.iterdir() if path.is_dir() and path.name.isdigit())
    next_id = (existing[-1] + 1) if existing else 1
    workspace = root / f"{next_id:06d}"
    workspace.mkdir(parents=True, exist_ok=False)
    for name in LAYOUT:
        (workspace / name).mkdir(parents=True, exist_ok=True)
    return workspace


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a numbered coursework solver workspace.")
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--problem")
    parser.add_argument("--pre-constraint-file", action="append", default=[])
    parser.add_argument("--reference-assignment-file", action="append", default=[])
    parser.add_argument("--demo")
    parser.add_argument("--data")
    parser.add_argument("--get-input-data")
    parser.add_argument("--demo-arg", action="append", default=[])
    parser.add_argument("--cpp-name", action="append", default=[])
    args = parser.parse_args()

    workspace = create_workspace(args.workspace_root.resolve())
    manifest = {
        "problem": args.problem,
        "pre_constraint_files": list(args.pre_constraint_file),
        "reference_assignment_files": list(args.reference_assignment_file),
        "demo": args.demo,
        "data": args.data,
        "get_input_data": args.get_input_data,
        "demo_args": list(args.demo_arg),
        "cpp_names": list(args.cpp_name),
        "workspace": str(workspace),
    }
    write_json(workspace / "run_manifest.json", manifest)
    print(workspace)


if __name__ == "__main__":
    main()
