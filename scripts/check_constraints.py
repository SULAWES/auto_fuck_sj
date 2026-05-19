#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import read_text_best_effort, write_json


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

STL_TOKEN_PATTERNS = {
    "vector": re.compile(r"\bvector\s*<"),
    "string": re.compile(r"(?:\bstd::string\b|\bstring\b(?!\s*\.\w))"),
    "map": re.compile(r"\bmap\s*<"),
    "set": re.compile(r"\bset\s*<"),
    "queue": re.compile(r"\bqueue\s*<"),
    "stack": re.compile(r"\bstack\s*<"),
    "deque": re.compile(r"\bdeque\s*<"),
    "list": re.compile(r"\blist\s*<"),
    "unordered_map": re.compile(r"\bunordered_map\s*<"),
    "unordered_set": re.compile(r"\bunordered_set\s*<"),
    "sort(": re.compile(r"\bsort\s*\("),
}

SNAKE_CASE_EXEMPT_NAMES = {
    "main",
    "cin",
    "cout",
    "endl",
    "printf",
    "scanf",
    "i",
    "j",
    "k",
    "ch",
}

KNOWLEDGE_TOPICS = [
    "comparison_logic_conditional",
    "branch",
    "loop",
    "pointer",
    "reference",
    "function",
    "array",
    "struct",
    "class",
]

KNOWLEDGE_LABELS = {
    "comparison_logic_conditional": "comparison/logical/conditional operators",
    "branch": "branch statements",
    "loop": "loops",
    "pointer": "pointers",
    "reference": "references",
    "function": "functions",
    "array": "arrays",
    "struct": "structs",
    "class": "classes",
}

KNOWLEDGE_TERMS = {
    "comparison_logic_conditional": ["比较", "逻辑", "条件运算符"],
    "branch": ["分支"],
    "loop": ["循环"],
    "pointer": ["指针"],
    "reference": ["引用"],
    "function": ["函数"],
    "array": ["数组"],
    "struct": ["结构体"],
    "class": ["类等", "类相关", "类概念", "class"],
}


def infer_constraints(problem_text: str) -> list[str]:
    text = problem_text.lower()
    inferred: list[str] = []
    if any(token in text for token in ("允许使用stl", "可以使用stl")):
        inferred.append("allow_stl")
    if any(token in text for token in ("允许使用string", "可以使用string", "允许 c++的 string", "允许c++的string")):
        inferred.append("allow_token:string")
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
    for topic in infer_banned_knowledge(problem_text):
        inferred.append(f"ban_knowledge:{topic}")
    return inferred


def infer_banned_knowledge(problem_text: str) -> list[str]:
    banned: set[str] = set()
    ban_spans = re.findall(r"(?:不允许|不得|不能|禁止)使用[^。；;！!\n]*", problem_text)
    for span in ban_spans:
        span = re.split(r"\s+\d+、", span, maxsplit=1)[0]
        for topic, terms in KNOWLEDGE_TERMS.items():
            if any(term in span for term in terms):
                banned.add(topic)
    return sorted(banned)


def collect_variable_names(code: str) -> list[str]:
    pattern = re.compile(r"\b(?:int|long|long\s+long|double|float|char|bool|string|auto)\s+([A-Za-z_]\w*)")
    return pattern.findall(code)


def collect_function_names(code: str) -> list[str]:
    pattern = re.compile(
        r"\b(?:int|long|long\s+long|double|float|char|bool|void)\s+([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{",
        re.MULTILINE,
    )
    return pattern.findall(code)


def is_snake_case(name: str) -> bool:
    return bool(re.fullmatch(r"[a-z][a-z0-9_]*", name))


def find_non_snake_case_identifiers(code: str) -> list[str]:
    names = set(collect_variable_names(code)) | set(collect_function_names(code))
    violations = []
    for name in sorted(names):
        if name in SNAKE_CASE_EXEMPT_NAMES:
            continue
        if not is_snake_case(name):
            violations.append(name)
    return violations


def has_non_allman_opening_brace(code: str) -> bool:
    for raw_line in code.splitlines():
        line = raw_line.strip()
        if not line or line == "{":
            continue
        if line.endswith("{"):
            if re.match(r"^(switch|do)\b", line):
                return True
            if re.search(r"\)\s*\{$", line):
                return True
            if re.search(r"\b(?:else|try|class|struct|namespace)\b.*\{$", line):
                return True
    return False


def contains_recursion(code: str) -> bool:
    function_pattern = re.compile(
        r"\b(?:int|long|long\s+long|double|float|char|bool|void)\s+([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{",
        re.MULTILINE,
    )
    for name in function_pattern.findall(code):
        body_pattern = re.compile(rf"\b{name}\s*\(")
        if len(body_pattern.findall(code)) >= 2:
            return True
    return False


def strip_string_literals(code: str) -> str:
    code = re.sub(r'"(?:\\.|[^"\\])*"', '""', code)
    code = re.sub(r"'(?:\\.|[^'\\])*'", "''", code)
    return code


def detect_knowledge_usage(code: str) -> set[str]:
    cleaned = strip_string_literals(code)
    usage: set[str] = set()
    if re.search(r"\b(?:if|switch)\s*\(", cleaned):
        usage.add("branch")
    if re.search(r"\b(?:for|while)\s*\(", cleaned) or re.search(r"\bdo\b", cleaned):
        usage.add("loop")
    if re.search(r"\bstruct\s+[A-Za-z_]\w*", cleaned):
        usage.add("struct")
    if re.search(r"\bclass\s+[A-Za-z_]\w*", cleaned):
        usage.add("class")
    if re.search(r"\b[A-Za-z_]\w*\s*\[[^\]]*\]", cleaned):
        usage.add("array")
    if re.search(r"\b(?:int|long|long\s+long|double|float|char|bool|void)\s*\*+\s*[A-Za-z_]\w*", cleaned):
        usage.add("pointer")
    if re.search(r"\b(?:int|long|long\s+long|double|float|char|bool|string|auto|[A-Z][A-Za-z_]\w*)\s*&\s*[A-Za-z_]\w*", cleaned):
        usage.add("reference")
    if re.search(r"\b(?:int|long|long\s+long|double|float|char|bool|void)\s+[A-Za-z_]\w*\s*\([^;{}]*\)\s*\{", cleaned):
        usage.add("function")
    if re.search(r"(?:==|!=|<=|>=|<|>|\|\||&&|\?|!)", cleaned):
        usage.add("comparison_logic_conditional")
    return usage


def main() -> None:
    parser = argparse.ArgumentParser(description="Check hard and soft coursework constraints.")
    parser.add_argument("--problem-context", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ban-token", action="append", default=[])
    args = parser.parse_args()

    problem_text, _ = read_text_best_effort(args.problem_context.resolve())
    source_files = sorted(args.candidate_dir.resolve().glob("*.c")) + sorted(args.candidate_dir.resolve().glob("*.cpp"))
    combined_code = "\n\n".join(path.read_text(encoding="utf-8", errors="replace") for path in source_files)
    lower_code = combined_code.lower()

    inferred = infer_constraints(problem_text)
    banned_tokens = set(args.ban_token)
    allowed_tokens = {item.split(":", 1)[1] for item in inferred if item.startswith("allow_token:")}
    allow_stl = "allow_stl" in inferred
    if "ban_stl" in inferred:
        banned_tokens.update(STL_BANNED_TOKENS)
    for item in inferred:
        if item.startswith("ban_token:"):
            banned_tokens.add(item.split(":", 1)[1])
    banned_tokens.difference_update(allowed_tokens)

    hard_violations: list[str] = []
    for token in sorted(banned_tokens):
        pattern = STL_TOKEN_PATTERNS.get(token)
        if pattern is not None:
            token_found = bool(pattern.search(lower_code))
        else:
            token_found = token.lower() in lower_code
        if token_found:
            hard_violations.append(f"Forbidden token detected: {token}")

    if "ban_recursion" in inferred and contains_recursion(combined_code):
        hard_violations.append("Possible recursion detected")

    used_knowledge = detect_knowledge_usage(combined_code)
    banned_knowledge = {
        item.split(":", 1)[1] for item in inferred if item.startswith("ban_knowledge:")
    }
    for topic in sorted(banned_knowledge & used_knowledge):
        hard_violations.append(f"Forbidden knowledge topic used: {KNOWLEDGE_LABELS.get(topic, topic)}")

    style_warnings: list[str] = []
    single_letter_names = {
        name for name in collect_variable_names(combined_code) if len(name) == 1 and name.lower() in {"a", "b", "c", "d"}
    }
    if single_letter_names:
        style_warnings.append("Single-letter variable names detected: " + ", ".join(sorted(single_letter_names)))
    if "template<" in lower_code:
        style_warnings.append("Template usage may look too advanced for the target style")
    if "[](" in combined_code or "[&]" in combined_code or "[=]" in combined_code:
        style_warnings.append("Lambda usage may look too advanced for the target style")
    if "namespace " in combined_code and "std" not in combined_code:
        style_warnings.append("Custom namespace usage may look too engineered")
    active_stl_patterns = {
        token: pattern for token, pattern in STL_TOKEN_PATTERNS.items() if token not in allowed_tokens
    }
    if not allow_stl and any(pattern.search(lower_code) for pattern in active_stl_patterns.values()):
        style_warnings.append("STL usage detected; default policy is to avoid STL unless the statement explicitly allows it")
    cautious_topics = sorted(
        topic for topic in used_knowledge
        if topic in {"pointer", "reference", "struct", "class"} and topic not in banned_knowledge
    )
    if cautious_topics:
        style_warnings.append(
            "Potentially advanced knowledge topics detected; confirm the PDF whitelist allows them: "
            + ", ".join(KNOWLEDGE_LABELS[topic] for topic in cautious_topics)
        )
    non_snake_case_names = find_non_snake_case_identifiers(combined_code)
    if non_snake_case_names:
        style_warnings.append("Non-snake_case identifiers detected: " + ", ".join(non_snake_case_names[:20]))
    if has_non_allman_opening_brace(combined_code):
        style_warnings.append("Non-Allman opening brace style detected")

    write_json(
        args.output.resolve(),
        {
            "hard_violations": hard_violations,
            "style_warnings": style_warnings,
            "inferred_constraints": inferred,
            "used_knowledge_topics": sorted(used_knowledge),
            "checked_files": [str(path) for path in source_files],
        },
    )
    print(args.output.resolve())


if __name__ == "__main__":
    main()
