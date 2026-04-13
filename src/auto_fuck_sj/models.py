from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SubmissionTarget:
    filename: str


@dataclass(slots=True)
class ToolConfig:
    ai_backend: str = "codex"  # 可选: codex, kimi
    codex_bin: str = "codex"
    gpp_bin: str = "g++"
    txt_compare_bin: str = "txt_compare.exe"
    get_input_data_bin: str = "get_input_data.exe"
    codex_model: str | None = None
    kimi_model: str | None = None  # Kimi 模型名称，如 kimi-k2-0711-preview
    compile_timeout_sec: int = 30
    run_timeout_sec: int = 10
    compare_timeout_sec: int = 10
    pdf_extract_timeout_sec: int = 20


@dataclass(slots=True)
class RunRequest:
    problem_file: Path
    demo_exe: Path
    demo_args: list[str] = field(default_factory=list)
    data_file: Path | None = None
    workspace_root: Path = Path("workspaces")
    submission_targets: list[SubmissionTarget] = field(
        default_factory=lambda: [SubmissionTarget(filename="main.cpp")]
    )
    entry_cpp: str | None = None
    max_attempts: int = 3
    generated_cases: int = 5
    extra_banned_tokens: list[str] = field(default_factory=list)
    compare_trim: str = "right"
    compare_ignore_blank: bool = True

    def normalized_entry_cpp(self) -> str:
        if self.entry_cpp:
            return self.entry_cpp
        return self.submission_targets[0].filename

    def testcase_prefixes(self) -> list[str]:
        prefixes: list[str] = []
        for target in self.submission_targets:
            stem = Path(target.filename).stem.strip()
            if stem:
                prefixes.append(stem)
        return prefixes

    def demo_command(self, demo_path: Path | None = None) -> list[str]:
        resolved_demo = demo_path or self.demo_exe
        return [str(resolved_demo), *self.demo_args]

    def job_label(self) -> str:
        label = self.normalized_entry_cpp()
        if self.demo_args:
            label = f"{label} {' '.join(self.demo_args)}"
        return label


@dataclass(slots=True)
class TestCase:
    name: str
    input_text: str
    source: str
    purpose: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvaluationFailure:
    case_name: str
    reason: str
    compare_stdout: str = ""
    compare_stderr: str = ""
    expected_file: str = ""
    actual_file: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvaluationSummary:
    compile_ok: bool
    all_passed: bool
    tested_case_count: int
    compile_result: dict[str, Any]
    failures: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ConstraintReport:
    hard_violations: list[str] = field(default_factory=list)
    style_warnings: list[str] = field(default_factory=list)
    inferred_constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
