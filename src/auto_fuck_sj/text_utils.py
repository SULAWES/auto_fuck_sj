from __future__ import annotations

from pathlib import Path


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
