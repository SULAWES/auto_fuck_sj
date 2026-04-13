from __future__ import annotations

import json
import locale
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .ai_adapter import AIAdapter
from .codex_adapter import CodexAdapter
from .constraints import check_constraints
from .kimi_adapter import KimiAdapter
from .models import EvaluationFailure, EvaluationSummary, RunRequest, TestCase, ToolConfig
from .subprocess_utils import run_command
from .testcase_parser import parse_grouped_test_data
from .text_utils import read_text_best_effort
from .workspace import Workspace


class AutomaticGC:
    def __init__(self, request: RunRequest, tools: ToolConfig) -> None:
        self.request = request
        self.tools = tools
        self.workspace = Workspace.create(request.workspace_root)
        self.agent = self._create_ai_adapter()
        self.problem_text = ""
        self.problem_context_path = self.workspace.extracted_dir / "problem_context.md"
        self.constraint_hints_path = self.workspace.extracted_dir / "constraint_hints.json"
        self.demo_observations_path = self.workspace.testcases_dir / "demo_observations.json"
        self.run_manifest_path = self.workspace.root / "run_manifest.json"
    
    def _create_ai_adapter(self) -> AIAdapter:
        """根据配置创建对应的 AI 适配器。"""
        backend = self.tools.ai_backend.lower()
        if backend == "kimi":
            return KimiAdapter(self.tools, self.workspace)
        elif backend == "codex":
            return CodexAdapter(self.tools, self.workspace)
        else:
            raise ValueError(f"Unsupported AI backend: {backend}. Use 'codex' or 'kimi'.")

    def run(self) -> dict[str, Any]:
        self._write_run_manifest()
        self.problem_text = self._ingest_problem()
        testcases = self._build_testcases()
        self._write_demo_observations(testcases)

        feedback_items: list[str] = []
        best_attempt_dir: Path | None = None
        best_files: dict[str, str] | None = None
        best_evaluation: EvaluationSummary | None = None

        for attempt in range(1, self.request.max_attempts + 1):
            attempt_dir = self.workspace.candidate_attempt_dir(attempt)
            files, notes = self._run_solver(attempt=attempt, feedback_items=feedback_items)
            self._write_candidate_files(attempt_dir, files)
            self.workspace.write_json(attempt_dir / "solver_notes.json", notes)

            evaluation = self._evaluate_attempt(attempt, attempt_dir, testcases)
            self.workspace.write_json(
                self.workspace.output_attempt_dir(attempt) / "evaluation_summary.json",
                evaluation.to_dict(),
            )

            constraint_report = check_constraints(
                files=files,
                problem_text=self.problem_text,
                extra_banned_tokens=self.request.extra_banned_tokens,
            )
            self.workspace.write_json(
                self.workspace.output_attempt_dir(attempt) / "constraint_report.json",
                constraint_report.to_dict(),
            )

            if evaluation.compile_ok:
                best_attempt_dir = attempt_dir
                best_files = files
                best_evaluation = evaluation

            if evaluation.all_passed and not constraint_report.hard_violations:
                final_files = files
                final_dir = attempt_dir
                if constraint_report.style_warnings:
                    humanized = self._run_humanizer(
                        attempt=attempt,
                        files=files,
                        style_warnings=constraint_report.style_warnings,
                    )
                    humanized_dir = self.workspace.candidate_attempt_dir(attempt + 100)
                    self._write_candidate_files(humanized_dir, humanized["files"])
                    self.workspace.write_json(
                        humanized_dir / "humanizer_notes.json",
                        humanized,
                    )
                    humanized_eval = self._evaluate_attempt(
                        attempt + 100, humanized_dir, testcases
                    )
                    self.workspace.write_json(
                        self.workspace.output_attempt_dir(attempt + 100)
                        / "evaluation_summary.json",
                        humanized_eval.to_dict(),
                    )
                    if humanized_eval.all_passed:
                        final_files = humanized["files"]
                        final_dir = humanized_dir

                self._publish_final(final_dir, final_files)
                return {
                    "status": "passed",
                    "workspace": str(self.workspace.root),
                    "final_dir": str(self.workspace.final_dir),
                    "tested_cases": len(testcases),
                }

            feedback_items = self._build_feedback(
                evaluation=evaluation,
                constraint_report=constraint_report.to_dict(),
            )

        if best_attempt_dir and best_files and best_evaluation:
            self._publish_final(best_attempt_dir, best_files)
            return {
                "status": "failed_best_effort",
                "workspace": str(self.workspace.root),
                "final_dir": str(self.workspace.final_dir),
                "tested_cases": len(testcases),
                "compile_ok": best_evaluation.compile_ok,
            }

        return {
            "status": "failed",
            "workspace": str(self.workspace.root),
            "final_dir": str(self.workspace.final_dir),
            "tested_cases": len(testcases),
        }

    def _write_run_manifest(self) -> None:
        manifest = {
            "problem_file": str(self.request.problem_file),
            "demo_exe": str(self.request.demo_exe),
            "demo_args": list(self.request.demo_args),
            "data_file": str(self.request.data_file) if self.request.data_file else None,
            "submission_targets": [item.filename for item in self.request.submission_targets],
            "entry_cpp": self.request.normalized_entry_cpp(),
            "max_attempts": self.request.max_attempts,
            "generated_cases": self.request.generated_cases,
            "extra_banned_tokens": self.request.extra_banned_tokens,
            "testcase_prefixes": self.request.testcase_prefixes(),
        }
        self.workspace.write_json(self.run_manifest_path, manifest)

    def _ingest_problem(self) -> str:
        input_problem = self.workspace.input_dir / self.request.problem_file.name
        shutil.copy2(self.request.problem_file, input_problem)
        input_demo = self.workspace.input_dir / self.request.demo_exe.name
        shutil.copy2(self.request.demo_exe, input_demo)
        if self.request.data_file:
            shutil.copy2(
                self.request.data_file,
                self.workspace.input_dir / self.request.data_file.name,
            )

        extracted_text, extraction_notes = self._extract_problem_text(input_problem)
        submission_text = "\n".join(
            f"- {target.filename}" for target in self.request.submission_targets
        )
        demo_args_text = " ".join(self.request.demo_args) if self.request.demo_args else "(none)"
        context = "\n".join(
            [
                "# Problem Context",
                "",
                f"- Original problem file: `{input_problem.name}`",
                f"- Demo executable: `{input_demo.name}`",
                f"- Demo arguments: `{demo_args_text}`",
                f"- Expected source files:",
                submission_text,
                "",
                "## Extraction Notes",
                "",
                extraction_notes or "No extraction notes.",
                "",
                "## Extracted Problem Text",
                "",
                extracted_text or "Extraction unavailable. Read the copied problem file directly if needed.",
            ]
        )
        self.workspace.write_text(self.problem_context_path, context)
        return extracted_text

    def _extract_problem_text(self, input_problem: Path) -> tuple[str, str]:
        suffix = input_problem.suffix.lower()
        if suffix in {".txt", ".md"}:
            text, encoding = read_text_best_effort(input_problem)
            return text, f"Loaded text directly with {encoding}."

        if suffix != ".pdf":
            return "", f"Unsupported problem format: {suffix}"

        output_text_path = self.workspace.extracted_dir / "problem_text.txt"
        extractors = [
            ["pdftotext", "-layout", "-nopgbrk", str(input_problem), str(output_text_path)],
            ["mutool", "draw", "-F", "txt", "-o", str(output_text_path), str(input_problem)],
        ]
        for command in extractors:
            if shutil.which(command[0]) is None:
                continue
            result = run_command(
                command,
                cwd=self.workspace.root,
                timeout_sec=self.tools.pdf_extract_timeout_sec,
            )
            if result.returncode == 0 and output_text_path.exists():
                return (
                    output_text_path.read_text(encoding="utf-8", errors="replace"),
                    f"Extracted text with {command[0]}.",
                )

        return "", "No supported PDF extractor found. Codex will rely on copied files and extraction notes."

    def _build_testcases(self) -> list[TestCase]:
        provided_cases = self._load_provided_cases()
        generated_cases = self._generate_cases_with_codex()
        merged_cases = provided_cases + generated_cases
        self.workspace.write_json(
            self.workspace.testcases_dir / "merged_cases.json",
            [case.to_dict() for case in merged_cases],
        )
        return merged_cases

    def _load_provided_cases(self) -> list[TestCase]:
        selection_path = self.workspace.testcases_dir / "provided_cases_selection.json"
        if not self.request.data_file:
            self.workspace.write_json(self.workspace.testcases_dir / "provided_cases.json", [])
            self.workspace.write_json(
                selection_path,
                {
                    "requested_prefixes": self.request.testcase_prefixes(),
                    "raw_count": 0,
                    "selected_count": 0,
                    "used_filtered_selection": False,
                    "selected_case_names": [],
                    "skipped_case_names": [],
                },
            )
            return []

        data_path = self.workspace.input_dir / self.request.data_file.name
        candidate_bins = [
            self.tools.get_input_data_bin,
            "get_input_data2.exe",
            "get_input_data.exe",
        ]
        resolved_tool = next((name for name in candidate_bins if shutil.which(name)), None)
        if not resolved_tool:
            return self._load_provided_cases_locally(data_path)

        list_result = run_command(
            [resolved_tool, "--all_group", str(data_path)],
            cwd=self.workspace.root,
            timeout_sec=20,
        )
        raw_cases: list[TestCase] = []
        if list_result.returncode != 0:
            self.workspace.write_json(
                self.workspace.testcases_dir / "provided_cases_error.json",
                list_result.to_dict(),
            )
            return self._load_provided_cases_locally(data_path)

        group_names = [line.strip() for line in list_result.stdout.splitlines() if line.strip()]
        for group_name in group_names:
            case_result = run_command(
                [resolved_tool, str(data_path), group_name],
                cwd=self.workspace.root,
                timeout_sec=20,
            )
            if case_result.returncode != 0:
                continue
            raw_cases.append(
                TestCase(
                    name=group_name,
                    input_text=case_result.stdout,
                    source="provided_data",
                    purpose="Imported from provided grouped testcase file",
                )
            )

        provided_cases, selection = self._filter_testcases_for_active_targets(raw_cases)
        self.workspace.write_json(selection_path, selection)
        self.workspace.write_json(
            self.workspace.testcases_dir / "provided_cases.json",
            [case.to_dict() for case in provided_cases],
        )
        return provided_cases

    def _load_provided_cases_locally(self, data_path: Path) -> list[TestCase]:
        cases, encoding = parse_grouped_test_data(data_path)
        provided_cases, selection = self._filter_testcases_for_active_targets(cases)
        self.workspace.write_json(
            self.workspace.testcases_dir / "provided_cases_local_parse.json",
            {
                "encoding": encoding,
                "raw_count": len(cases),
                "selected_count": len(provided_cases),
                "selection": selection,
                "cases": [case.to_dict() for case in provided_cases],
            },
        )
        self.workspace.write_json(
            self.workspace.testcases_dir / "provided_cases_selection.json",
            selection,
        )
        self.workspace.write_json(
            self.workspace.testcases_dir / "provided_cases.json",
            [case.to_dict() for case in provided_cases],
        )
        return provided_cases

    def _filter_testcases_for_active_targets(
        self,
        cases: list[TestCase],
    ) -> tuple[list[TestCase], dict[str, Any]]:
        requested_prefixes = self.request.testcase_prefixes()
        normalized_prefixes = [prefix.lower() for prefix in requested_prefixes if prefix.strip()]

        matched_cases = [
            case for case in cases if self._matches_requested_prefix(case.name, normalized_prefixes)
        ]
        use_filtered_selection = bool(normalized_prefixes and matched_cases)
        selected_cases = matched_cases if use_filtered_selection else cases
        selected_case_names = [case.name for case in selected_cases]
        skipped_case_names = [
            case.name for case in cases if case.name not in set(selected_case_names)
        ]

        return selected_cases, {
            "requested_prefixes": requested_prefixes,
            "raw_count": len(cases),
            "selected_count": len(selected_cases),
            "used_filtered_selection": use_filtered_selection,
            "selected_case_names": selected_case_names,
            "skipped_case_names": skipped_case_names,
        }

    def _matches_requested_prefix(self, case_name: str, prefixes: list[str]) -> bool:
        normalized_name = case_name.strip().strip("[]").lower()
        return any(
            normalized_name == prefix or normalized_name.startswith(f"{prefix}-")
            for prefix in prefixes
        )

    def _generate_cases_with_codex(self) -> list[TestCase]:
        if self.request.generated_cases <= 0:
            self.workspace.write_json(self.workspace.testcases_dir / "generated_cases.json", [])
            return []

        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "notes": {"type": "array", "items": {"type": "string"}},
                "cases": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "input": {"type": "string"},
                            "purpose": {"type": "string"},
                        },
                        "required": ["name", "input", "purpose"],
                    },
                },
            },
            "required": ["notes", "cases"],
        }
        prompt = self.agent.render_prompt(
            "testgen",
            problem_context_path=str(self.problem_context_path.relative_to(self.workspace.root)),
            generated_case_count=str(self.request.generated_cases),
        )
        try:
            response = self.agent.run_json_task(
                task_name="testgen",
                prompt=prompt,
                schema=schema,
                workdir=self.workspace.root,
            )
        except RuntimeError as exc:
            self.workspace.write_text(
                self.workspace.logs_dir / "testgen_error.log",
                str(exc),
            )
            self.workspace.write_json(self.workspace.testcases_dir / "generated_cases.json", [])
            return []

        generated_cases = [
            TestCase(
                name=item["name"],
                input_text=item["input"],
                source="codex_generated",
                purpose=item["purpose"],
            )
            for item in response["cases"]
        ]
        self.workspace.write_json(
            self.workspace.testcases_dir / "generated_cases.json",
            [case.to_dict() for case in generated_cases],
        )
        return generated_cases

    def _write_demo_observations(self, testcases: list[TestCase]) -> None:
        preferred_cases = [case for case in testcases if case.source == "provided_data"]
        selected_cases = preferred_cases[:5] if preferred_cases else testcases[:3]

        observations: list[dict[str, Any]] = []
        demo_path = self.workspace.input_dir / self.request.demo_exe.name
        for testcase in selected_cases:
            demo_result = run_command(
                self.request.demo_command(demo_path),
                cwd=self.workspace.root,
                input_text=testcase.input_text,
                timeout_sec=self.tools.run_timeout_sec,
            )
            observations.append(
                {
                    "name": testcase.name,
                    "source": testcase.source,
                    "input_text": testcase.input_text,
                    "demo_stdout": demo_result.stdout,
                    "demo_stderr": demo_result.stderr,
                    "returncode": demo_result.returncode,
                    "timed_out": demo_result.timed_out,
                    "demo_args": list(self.request.demo_args),
                }
            )

        self.workspace.write_json(self.demo_observations_path, observations)

    def _run_solver(self, *, attempt: int, feedback_items: list[str]) -> tuple[dict[str, str], dict]:
        file_enum = [target.filename for target in self.request.submission_targets]
        file_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "summary": {"type": "string"},
                "assumptions": {"type": "array", "items": {"type": "string"}},
                "files": {
                    "type": "array",
                    "minItems": len(file_enum),
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "filename": {"type": "string", "enum": file_enum},
                            "content": {"type": "string"},
                            "purpose": {"type": "string"},
                        },
                        "required": ["filename", "content", "purpose"],
                    },
                },
            },
            "required": ["summary", "assumptions", "files"],
        }
        feedback_text = "\n".join(f"- {item}" for item in feedback_items) if feedback_items else "- None"
        prompt = self.agent.render_prompt(
            "solver",
            problem_context_path=str(self.problem_context_path.relative_to(self.workspace.root)),
            testcase_path=str(
                (self.workspace.testcases_dir / "merged_cases.json").relative_to(self.workspace.root)
            ),
            demo_observations_path=str(
                self.demo_observations_path.relative_to(self.workspace.root)
            ),
            required_cpp_names="\n".join(f"- {name}" for name in file_enum),
            attempt_number=str(attempt),
            feedback_text=feedback_text,
        )
        response = self.agent.run_json_task(
            task_name=f"solver_attempt_{attempt:02d}",
            prompt=prompt,
            schema=file_schema,
            workdir=self.workspace.root,
        )
        files = {item["filename"]: item["content"] for item in response["files"]}
        return files, response

    def _write_candidate_files(self, attempt_dir: Path, files: dict[str, str]) -> None:
        for filename, content in files.items():
            self.workspace.write_text(attempt_dir / filename, content)

    def _evaluate_attempt(
        self,
        attempt: int,
        attempt_dir: Path,
        testcases: list[TestCase],
    ) -> EvaluationSummary:
        output_dir = self.workspace.output_attempt_dir(attempt)
        compile_log_path = output_dir / "compile_result.json"
        executable_path = output_dir / "candidate.exe"

        cpp_files = sorted(attempt_dir.glob("*.cpp"))
        if not cpp_files:
            summary = EvaluationSummary(
                compile_ok=False,
                all_passed=False,
                tested_case_count=0,
                compile_result={"error": "No .cpp files generated"},
                failures=[],
                notes=["Solver did not generate any .cpp files."],
            )
            self.workspace.write_json(compile_log_path, summary.compile_result)
            return summary

        compile_command = [
            self.tools.gpp_bin,
            "-std=c++17",
            "-finput-charset=UTF-8",
            "-fexec-charset=GBK",
            "-O2",
            "-Wall",
            "-Wextra",
            "-o",
            str(executable_path),
            *[str(path) for path in cpp_files],
        ]
        compile_result = run_command(
            compile_command,
            cwd=attempt_dir,
            timeout_sec=self.tools.compile_timeout_sec,
        )
        self.workspace.write_json(compile_log_path, compile_result.to_dict())
        if compile_result.returncode != 0:
            return EvaluationSummary(
                compile_ok=False,
                all_passed=False,
                tested_case_count=0,
                compile_result=compile_result.to_dict(),
                failures=[],
                notes=["Compilation failed."],
            )

        if not testcases:
            return EvaluationSummary(
                compile_ok=True,
                all_passed=True,
                tested_case_count=0,
                compile_result=compile_result.to_dict(),
                failures=[],
                notes=["No testcases available. Compile-only pass."],
            )

        failures: list[EvaluationFailure] = []
        for index, testcase in enumerate(testcases, start=1):
            case_dir = output_dir / "cases" / f"{index:03d}_{self._safe_case_name(testcase.name)}"
            case_dir.mkdir(parents=True, exist_ok=True)
            input_path = case_dir / "input.txt"
            expected_path = case_dir / "expected.txt"
            actual_path = case_dir / "actual.txt"
            demo_stderr_path = case_dir / "demo_stderr.txt"
            candidate_stderr_path = case_dir / "candidate_stderr.txt"

            input_path.write_text(testcase.input_text, encoding="utf-8")

            demo_result = self._run_binary_command(
                self.request.demo_command(self.workspace.input_dir / self.request.demo_exe.name),
                cwd=case_dir,
                input_text=testcase.input_text,
                timeout_sec=self.tools.run_timeout_sec,
            )
            expected_path.write_bytes(demo_result["stdout_bytes"])
            demo_stderr_path.write_text(demo_result["stderr_text"], encoding="utf-8")
            if demo_result["returncode"] != 0:
                failures.append(
                    EvaluationFailure(
                        case_name=testcase.name,
                        reason="demo.exe failed",
                        compare_stdout=demo_result["stdout_text"],
                        compare_stderr=demo_result["stderr_text"],
                        expected_file=str(expected_path),
                    )
                )
                continue

            candidate_result = self._run_binary_command(
                [str(executable_path)],
                cwd=case_dir,
                input_text=testcase.input_text,
                timeout_sec=self.tools.run_timeout_sec,
            )
            actual_path.write_bytes(candidate_result["stdout_bytes"])
            candidate_stderr_path.write_text(
                candidate_result["stderr_text"],
                encoding="utf-8",
            )
            if candidate_result["returncode"] != 0:
                failures.append(
                    EvaluationFailure(
                        case_name=testcase.name,
                        reason="candidate program failed",
                        compare_stdout=candidate_result["stdout_text"],
                        compare_stderr=candidate_result["stderr_text"],
                        expected_file=str(expected_path),
                        actual_file=str(actual_path),
                    )
                )
                continue

            compare_result = self._compare_outputs(actual_path, expected_path, case_dir)
            if not compare_result["matched"]:
                failures.append(
                    EvaluationFailure(
                        case_name=testcase.name,
                        reason="output mismatch",
                        compare_stdout=compare_result["stdout"],
                        compare_stderr=compare_result["stderr"],
                        expected_file=str(expected_path),
                        actual_file=str(actual_path),
                    )
                )

        return EvaluationSummary(
            compile_ok=True,
            all_passed=not failures,
            tested_case_count=len(testcases),
            compile_result=compile_result.to_dict(),
            failures=[item.to_dict() for item in failures],
            notes=[] if failures else ["All available testcases passed."],
        )

    def _compare_outputs(
        self,
        actual_path: Path,
        expected_path: Path,
        case_dir: Path,
    ) -> dict[str, Any]:
        compare_command = [
            self.tools.txt_compare_bin,
            "--file1",
            str(actual_path),
            "--file2",
            str(expected_path),
            "--trim",
            self.request.compare_trim,
            "--display",
            "normal",
        ]
        if self.request.compare_ignore_blank:
            compare_command.append("--ignore_blank")

        compare_result_path = case_dir / "compare_result.json"
        if shutil.which(self.tools.txt_compare_bin):
            result = run_command(
                compare_command,
                cwd=case_dir,
                timeout_sec=self.tools.compare_timeout_sec,
            )
            payload = result.to_dict()
            payload["matched"] = self._infer_compare_match(result.stdout, result.stderr, result.returncode)
            self.workspace.write_json(compare_result_path, payload)
            return {
                "matched": payload["matched"],
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        actual = actual_path.read_text(encoding="utf-8")
        expected = expected_path.read_text(encoding="utf-8")
        normalized_actual = actual.rstrip() if self.request.compare_trim == "right" else actual
        normalized_expected = expected.rstrip() if self.request.compare_trim == "right" else expected
        matched = normalized_actual == normalized_expected
        payload = {
            "command": compare_command,
            "fallback": "txt_compare.exe not found in PATH, used Python fallback",
            "matched": matched,
        }
        self.workspace.write_json(compare_result_path, payload)
        return {"matched": matched, "stdout": json.dumps(payload), "stderr": ""}

    def _infer_compare_match(self, stdout: str, stderr: str, returncode: int) -> bool:
        text = f"{stdout}\n{stderr}".lower()
        mismatch_markers = ["不匹配", "different", "diff", "mismatch", "差异"]
        match_markers = ["匹配", "match", "same", "通过"]
        if any(marker in text for marker in mismatch_markers):
            return False
        if any(marker in text for marker in match_markers):
            return True
        return returncode == 0

    def _run_humanizer(
        self,
        *,
        attempt: int,
        files: dict[str, str],
        style_warnings: list[str],
    ) -> dict[str, Any]:
        file_enum = list(files)
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "notes": {"type": "array", "items": {"type": "string"}},
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "filename": {"type": "string", "enum": file_enum},
                            "content": {"type": "string"},
                        },
                        "required": ["filename", "content"],
                    },
                },
            },
            "required": ["notes", "files"],
        }
        source_bundle = "\n\n".join(
            f"### FILE: {name}\n```cpp\n{content}\n```" for name, content in files.items()
        )
        prompt = self.agent.render_prompt(
            "humanizer",
            attempt_number=str(attempt),
            style_warnings="\n".join(f"- {item}" for item in style_warnings),
            source_bundle=source_bundle,
        )
        response = self.agent.run_json_task(
            task_name=f"humanizer_attempt_{attempt:02d}",
            prompt=prompt,
            schema=schema,
            workdir=self.workspace.root,
        )
        return {
            "notes": response["notes"],
            "files": {item["filename"]: item["content"] for item in response["files"]},
        }

    def _build_feedback(
        self,
        *,
        evaluation: EvaluationSummary,
        constraint_report: dict[str, Any],
    ) -> list[str]:
        feedback: list[str] = []
        if not evaluation.compile_ok:
            feedback.append("Previous attempt did not compile. Fix compilation errors first.")
            compile_stderr = evaluation.compile_result.get("stderr", "")
            if compile_stderr:
                feedback.append(f"Compiler stderr:\n{compile_stderr}")
            return feedback

        for failure in evaluation.failures[:5]:
            feedback.append(self._summarize_failure_for_feedback(failure))
        for violation in constraint_report.get("hard_violations", []):
            feedback.append(f"Hard constraint violation: {violation}")
        return feedback or ["Improve overall robustness. Previous attempt still did not pass."]

    def _summarize_failure_for_feedback(self, failure: dict[str, Any]) -> str:
        parts = [f"Case {failure['case_name']} failed: {failure['reason']}." ]

        compare_hint = self._extract_compare_hint(failure.get("compare_stdout", ""))
        if compare_hint:
            parts.append(f"Compare hint: {compare_hint}.")

        expected_preview = self._read_output_preview(failure.get("expected_file", ""))
        if expected_preview:
            parts.append(f"Expected preview: {expected_preview}")

        actual_preview = self._read_output_preview(failure.get("actual_file", ""))
        if actual_preview:
            parts.append(f"Actual preview: {actual_preview}")

        compare_stderr = failure.get("compare_stderr", "").strip()
        if compare_stderr:
            parts.append(f"Compare stderr: {compare_stderr[:240]}")

        return " ".join(parts)

    def _extract_compare_hint(self, compare_stdout: str) -> str:
        for line in compare_stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("第[") or stripped.startswith("在指定检查条件下"):
                return stripped
        return ""

    def _read_output_preview(self, file_path: str) -> str:
        if not file_path:
            return ""

        path = Path(file_path)
        if not path.exists() or path.is_dir():
            return ""

        try:
            text, _ = read_text_best_effort(path)
        except OSError:
            return ""

        preview_lines: list[str] = []
        for line in text.splitlines()[:3]:
            preview_lines.append(line if line else "<EMPTY>")

        preview = " | ".join(preview_lines).strip()
        return preview[:240]

    def _publish_final(self, source_dir: Path, files: dict[str, str]) -> None:
        for filename, content in files.items():
            self.workspace.write_text(self.workspace.final_dir / filename, content)
        self.workspace.write_json(
            self.workspace.final_dir / "final_manifest.json",
            {
                "source_dir": str(source_dir),
                "files": sorted(files),
            },
        )

    def _safe_case_name(self, name: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
        return cleaned or "case"

    def _run_binary_command(
        self,
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
        except subprocess.TimeoutExpired as exc:
            stdout_bytes = exc.stdout or b""
            stderr_bytes = exc.stderr or b""
            return {
                "returncode": -1,
                "stdout_bytes": stdout_bytes,
                "stderr_bytes": stderr_bytes,
                "stdout_text": stdout_bytes.decode(encoding, errors="replace"),
                "stderr_text": stderr_bytes.decode(encoding, errors="replace"),
                "timed_out": True,
            }

        stdout_bytes = completed.stdout or b""
        stderr_bytes = completed.stderr or b""
        return {
            "returncode": completed.returncode,
            "stdout_bytes": stdout_bytes,
            "stderr_bytes": stderr_bytes,
            "stdout_text": stdout_bytes.decode(encoding, errors="replace"),
            "stderr_text": stderr_bytes.decode(encoding, errors="replace"),
            "timed_out": False,
        }









