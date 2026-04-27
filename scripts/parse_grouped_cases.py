#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import parse_grouped_cases, write_json


def matches_prefix(case_name: str, prefixes: list[str]) -> bool:
    normalized_name = case_name.strip().strip("[]").lower()
    return any(normalized_name == prefix or normalized_name.startswith(f"{prefix}-") for prefix in prefixes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse grouped coursework testcase data with a text parser fallback.")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prefix", action="append", default=[])
    args = parser.parse_args()

    cases, encoding = parse_grouped_cases(args.data.resolve())
    normalized_prefixes = [prefix.lower() for prefix in args.prefix if prefix.strip()]
    matched = [case for case in cases if matches_prefix(case["name"], normalized_prefixes)]
    use_filtered = bool(normalized_prefixes and matched)
    selected = matched if use_filtered else cases

    payload = {
        "encoding": encoding,
        "requested_prefixes": list(args.prefix),
        "raw_count": len(cases),
        "selected_count": len(selected),
        "used_filtered_selection": use_filtered,
        "cases": selected,
    }
    write_json(args.output.resolve(), payload)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
