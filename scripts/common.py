from __future__ import annotations

import json
import locale
import re
import subprocess
from pathlib import Path
from typing import Any


COMMON_ENCODINGS = [
    "utf-8",
    "utf-8-sig",
    "gb18030",
    "gbk",
    "big5",
    "latin-1",
]


def read_text_best_effort(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    for encoding in COMMON_ENCODINGS:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_cases_payload(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        cases = payload.get("cases", [])
        if isinstance(cases, list):
            return cases
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Unsupported cases payload in {path}")


def run_text_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    input_text: str | None = None,
    timeout_sec: int | None = None,
    encoding: str | None = None,
) -> dict[str, Any]:
    resolved_encoding = encoding or locale.getpreferredencoding(False) or "utf-8"
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            input=input_text,
            capture_output=True,
            text=True,
            encoding=resolved_encoding,
            errors="replace",
            timeout=timeout_sec,
            check=False,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": -1,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
        }


def run_binary_command(
    command: list[str],
    *,
    cwd: Path,
    input_text: str,
    timeout_sec: int,
) -> dict[str, Any]:
    encoding = locale.getpreferredencoding(False) or "utf-8"
    input_bytes = input_text.encode(encoding, errors="replace")
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            input=input_bytes,
            capture_output=True,
            text=False,
            timeout=timeout_sec,
            check=False,
        )
        stdout_bytes = completed.stdout or b""
        stderr_bytes = completed.stderr or b""
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout_bytes": stdout_bytes,
            "stderr_bytes": stderr_bytes,
            "stdout_text": stdout_bytes.decode(encoding, errors="replace"),
            "stderr_text": stderr_bytes.decode(encoding, errors="replace"),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout_bytes = exc.stdout or b""
        stderr_bytes = exc.stderr or b""
        return {
            "command": command,
            "returncode": -1,
            "stdout_bytes": stdout_bytes,
            "stderr_bytes": stderr_bytes,
            "stdout_text": stdout_bytes.decode(encoding, errors="replace"),
            "stderr_text": stderr_bytes.decode(encoding, errors="replace"),
            "timed_out": True,
        }


GROUP_PATTERN = re.compile(
    r"^\[(?P<name>[^\]\r\n]+)\]\r?\n(?P<body>.*?)(?=^\[[^\]\r\n]+\]\r?\n|\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_grouped_cases(path: Path) -> tuple[list[dict[str, str]], str]:
    content, encoding = read_text_best_effort(path)
    cases: list[dict[str, str]] = []
    for match in GROUP_PATTERN.finditer(content):
        body = match.group("body")
        if body.endswith("\r\n"):
            body = body[:-2]
        elif body.endswith("\n"):
            body = body[:-1]
        cases.append(
            {
                "name": match.group("name"),
                "input_text": body,
                "source": "grouped_data",
                "purpose": f"Parsed from grouped testcase file with encoding {encoding}",
            }
        )
    return cases, encoding


def infer_compare_match(stdout: str, stderr: str, returncode: int) -> bool:
    text = f"{stdout}\n{stderr}".lower()
    mismatch_markers = ["不匹配", "different", "diff", "mismatch", "差异"]
    match_markers = ["匹配", "match", "same", "通过"]
    if any(marker in text for marker in mismatch_markers):
        return False
    if any(marker in text for marker in match_markers):
        return True
    return returncode == 0


def safe_case_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
    return cleaned or "case"
