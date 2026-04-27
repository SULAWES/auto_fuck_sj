#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import load_cases_payload, parse_grouped_cases, run_text_command, write_json


def normalize_prefixes(prefixes: list[str]) -> list[str]:
    return [prefix.strip().lower() for prefix in prefixes if prefix.strip()]


def normalize_group_name(group_name: str) -> str:
    return group_name.strip().strip("[]").lower()


def matches_prefix(case_name: str, prefixes: list[str]) -> bool:
    if not prefixes:
        return True
    normalized_name = normalize_group_name(case_name)
    return any(normalized_name == prefix or normalized_name.startswith(f"{prefix}-") for prefix in prefixes)


def extract_cases_with_exe(data_path: Path, get_input_data_bin: Path, prefixes: list[str], timeout_sec: int) -> tuple[list[dict], dict]:
    list_result = run_text_command(
        [str(get_input_data_bin), "--all_group", str(data_path)],
        cwd=data_path.resolve().parent,
        timeout_sec=timeout_sec,
    )
    if list_result["returncode"] != 0:
        raise RuntimeError(list_result["stderr"] or list_result["stdout"] or "get_input_data.exe failed to list groups")

    group_names = [line.strip() for line in list_result["stdout"].splitlines() if line.strip()]
    selected_names = [name for name in group_names if matches_prefix(name, prefixes)]
    use_filtered = bool(prefixes and selected_names)
    if not use_filtered:
        selected_names = group_names

    cases: list[dict] = []
    for raw_name in selected_names:
        normalized_name = raw_name.strip().strip("[]")
        extract_result = run_text_command(
            [str(get_input_data_bin), str(data_path), normalized_name],
            cwd=data_path.resolve().parent,
            timeout_sec=timeout_sec,
        )
        if extract_result["returncode"] != 0:
            raise RuntimeError(
                extract_result["stderr"] or extract_result["stdout"] or f"get_input_data.exe failed for group {normalized_name}"
            )
        cases.append(
            {
                "name": normalized_name,
                "input_text": extract_result["stdout"].rstrip("\r\n"),
                "source": "grouped_data_exe",
                "purpose": f"Extracted with {get_input_data_bin.name}",
            }
        )

    metadata = {
        "method": "get_input_data.exe",
        "group_count": len(group_names),
        "selected_group_count": len(cases),
        "used_filtered_selection": use_filtered,
    }
    return cases, metadata


def extract_cases_with_parser(data_path: Path, prefixes: list[str]) -> tuple[list[dict], dict]:
    cases, encoding = parse_grouped_cases(data_path.resolve())
    selected = [case for case in cases if matches_prefix(case["name"], prefixes)]
    use_filtered = bool(prefixes and selected)
    if not use_filtered:
        selected = cases
    metadata = {
        "method": "text_parser_fallback",
        "encoding": encoding,
        "group_count": len(cases),
        "selected_group_count": len(selected),
        "used_filtered_selection": use_filtered,
    }
    return selected, metadata


def load_extra_cases(paths: list[Path], source_label: str) -> list[dict]:
    extra_cases: list[dict] = []
    for path in paths:
        for index, case in enumerate(load_cases_payload(path.resolve()), start=1):
            name = str(case.get("name") or f"{path.stem}-{index:02d}")
            input_text = str(case.get("input_text", ""))
            extra_cases.append(
                {
                    "name": name,
                    "input_text": input_text,
                    "source": case.get("source", source_label),
                    "purpose": case.get("purpose", f"Loaded from {path.name}"),
                }
            )
    return extra_cases


def deduplicate_cases(cases: list[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    deduplicated: list[dict] = []
    for case in cases:
        key = (str(case["name"]), str(case["input_text"]))
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(case)
    return deduplicated


def main() -> None:
    parser = argparse.ArgumentParser(description="Build testcase bundles from official grouped data and supplemental cases.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--get-input-data-bin", type=Path)
    parser.add_argument("--prefix", action="append", default=[])
    parser.add_argument("--supplement-cases", type=Path, action="append", default=[])
    parser.add_argument("--generated-cases", type=Path, action="append", default=[])
    parser.add_argument("--min-official-cases", type=int, default=1)
    parser.add_argument("--timeout-sec", type=int, default=10)
    args = parser.parse_args()

    prefixes = normalize_prefixes(args.prefix)
    official_cases: list[dict] = []
    official_metadata: dict = {"method": "none", "group_count": 0, "selected_group_count": 0, "used_filtered_selection": False}

    if args.data:
        if args.get_input_data_bin and args.get_input_data_bin.exists():
            official_cases, official_metadata = extract_cases_with_exe(
                args.data.resolve(),
                args.get_input_data_bin.resolve(),
                prefixes,
                args.timeout_sec,
            )
        else:
            official_cases, official_metadata = extract_cases_with_parser(args.data.resolve(), prefixes)

    supplement_cases = load_extra_cases(args.supplement_cases, "supplement_cases")
    generated_cases = load_extra_cases(args.generated_cases, "generated_cases")
    selected_cases = deduplicate_cases([*official_cases, *supplement_cases, *generated_cases])

    needs_more_cases = len(official_cases) < max(args.min_official_cases, 0) and not supplement_cases and not generated_cases
    payload = {
        "requested_prefixes": list(args.prefix),
        "official_case_count": len(official_cases),
        "supplement_case_count": len(supplement_cases),
        "generated_case_count": len(generated_cases),
        "selected_count": len(selected_cases),
        "official_metadata": official_metadata,
        "needs_more_cases": needs_more_cases,
        "min_official_cases": args.min_official_cases,
        "cases": selected_cases,
    }
    write_json(args.output.resolve(), payload)
    print(args.output.resolve())


if __name__ == "__main__":
    main()
