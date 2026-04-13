from __future__ import annotations

import re
from pathlib import Path

from .models import TestCase
from .text_utils import read_text_best_effort


GROUP_PATTERN = re.compile(
    r"^\[(?P<name>[^\]\r\n]+)\]\r?\n(?P<body>.*?)(?=^\[[^\]\r\n]+\]\r?\n|\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_grouped_test_data(path: Path) -> tuple[list[TestCase], str]:
    content, encoding = read_text_best_effort(path)
    cases: list[TestCase] = []
    for match in GROUP_PATTERN.finditer(content):
        body = match.group("body")
        if body.endswith("\r\n"):
            body = body[:-2]
        elif body.endswith("\n"):
            body = body[:-1]
        cases.append(
            TestCase(
                name=match.group("name"),
                input_text=body,
                source="local_grouped_text",
                purpose=f"Parsed locally from grouped data file with encoding {encoding}",
            )
        )
    return cases, encoding
