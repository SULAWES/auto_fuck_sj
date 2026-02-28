from __future__ import annotations

import locale
import subprocess
from pathlib import Path

from .models import CommandResult


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    input_text: str | None = None,
    timeout_sec: int | None = None,
    encoding: str | None = None,
) -> CommandResult:
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
        return CommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            timed_out=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            command=command,
            returncode=-1,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            timed_out=True,
        )
