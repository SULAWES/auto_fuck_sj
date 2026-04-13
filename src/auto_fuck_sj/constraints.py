from __future__ import annotations

import re
from typing import Iterable

from .models import ConstraintReport


STL_BANNED_TOKENS = [
    "vector",
    "string",
    "map",
    "set",
    "queue",
    "stack",
    "deque",
    "list",
    "unordered_map",
    "unordered_set",
    "sort(",
]


def infer_constraints(problem_text: str) -> list[str]:
    text = problem_text.lower()
    inferred: list[str] = []
    if any(token in text for token in ("不能使用stl", "不得使用stl", "禁止使用stl")):
        inferred.append("ban_stl")
    if any(token in text for token in ("不能使用递归", "不得使用递归", "禁止使用递归")):
        inferred.append("ban_recursion")
    if any(token in text for token in ("不能使用vector", "不得使用vector", "禁止使用vector")):
        inferred.append("ban_token:vector")
    if any(token in text for token in ("不能使用string", "不得使用string", "禁止使用string")):
        inferred.append("ban_token:string")
    if any(token in text for token in ("不能使用类", "不得使用类", "禁止使用类")):
        inferred.append("ban_token:class")
        inferred.append("ban_token:struct")
    if any(token in text for token in ("不能使用模板", "不得使用模板", "禁止使用模板")):
        inferred.append("ban_token:template")
    return inferred


def _collect_variable_names(code: str) -> list[str]:
    pattern = re.compile(
        r"\b(?:int|long|long\s+long|double|float|char|bool|string|auto)\s+([A-Za-z_]\w*)"
    )
    return pattern.findall(code)


def _contains_recursion(code: str) -> bool:
    function_pattern = re.compile(
        r"\b(?:int|long|long\s+long|double|float|char|bool|void)\s+([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{",
        re.MULTILINE,
    )
    for name in function_pattern.findall(code):
        body_pattern = re.compile(rf"\b{name}\s*\(")
        if len(body_pattern.findall(code)) >= 2:
            return True
    return False


def check_constraints(
    files: dict[str, str],
    problem_text: str,
    extra_banned_tokens: Iterable[str],
) -> ConstraintReport:
    inferred = infer_constraints(problem_text)
    hard_violations: list[str] = []
    style_warnings: list[str] = []
    combined_code = "\n\n".join(files.values())
    lower_code = combined_code.lower()

    banned_tokens = set(extra_banned_tokens)
    if "ban_stl" in inferred:
        banned_tokens.update(STL_BANNED_TOKENS)
    for item in inferred:
        if item.startswith("ban_token:"):
            banned_tokens.add(item.split(":", 1)[1])

    for token in sorted(banned_tokens):
        if token.lower() in lower_code:
            hard_violations.append(f"Forbidden token detected: {token}")

    if "ban_recursion" in inferred and _contains_recursion(combined_code):
        hard_violations.append("Possible recursion detected")

    single_letter_names = {
        name
        for name in _collect_variable_names(combined_code)
        if len(name) == 1 and name.lower() in {"a", "b", "c", "d"}
    }
    if single_letter_names:
        style_warnings.append(
            "Single-letter variable names detected: "
            + ", ".join(sorted(single_letter_names))
        )

    if "template<" in lower_code:
        style_warnings.append("Template usage may look too advanced for the target style")
    if "[](" in combined_code or "[&]" in combined_code or "[=]" in combined_code:
        style_warnings.append("Lambda usage may look too advanced for the target style")
    if "namespace " in combined_code and "std" not in combined_code:
        style_warnings.append("Custom namespace usage may look too engineered")

    return ConstraintReport(
        hard_violations=hard_violations,
        style_warnings=style_warnings,
        inferred_constraints=inferred,
    )
