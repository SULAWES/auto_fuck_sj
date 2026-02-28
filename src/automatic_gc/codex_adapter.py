from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from string import Template

from .models import ToolConfig
from .subprocess_utils import run_command
from .workspace import Workspace


class CodexAdapter:
    def __init__(self, tools: ToolConfig, workspace: Workspace) -> None:
        self.tools = tools
        self.workspace = workspace
        self.agent_log_dir = workspace.log_dir("agent")

    def render_prompt(self, prompt_name: str, **values: str) -> str:
        template_text = (
            resources.files("automatic_gc")
            .joinpath("prompts")
            .joinpath(f"{prompt_name}.md")
            .read_text(encoding="utf-8")
        )
        return Template(template_text).safe_substitute(values)

    def run_json_task(
        self,
        *,
        task_name: str,
        prompt: str,
        schema: dict,
        workdir: Path,
        sandbox: str = "read-only",
    ) -> dict:
        prompt_path = self.agent_log_dir / f"{task_name}_prompt.md"
        schema_path = self.agent_log_dir / f"{task_name}_schema.json"
        stdout_path = self.agent_log_dir / f"{task_name}_stdout.log"
        stderr_path = self.agent_log_dir / f"{task_name}_stderr.log"
        message_path = self.agent_log_dir / f"{task_name}_last_message.json"

        prompt_path.write_text(prompt, encoding="utf-8")
        schema_path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        command = [
            self.tools.codex_bin,
            "exec",
            "--skip-git-repo-check",
            "--sandbox",
            sandbox,
            "--cd",
            str(workdir),
            "--output-schema",
            str(schema_path),
            "-o",
            str(message_path),
            "-",
        ]
        if self.tools.codex_model:
            command.extend(["-m", self.tools.codex_model])

        result = run_command(
            command,
            cwd=workdir,
            input_text=prompt,
            timeout_sec=300,
            encoding="utf-8",
        )
        stdout_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")

        if result.returncode != 0:
            raise RuntimeError(
                f"Codex task '{task_name}' failed with exit code {result.returncode}. "
                f"See {stdout_path} and {stderr_path}."
            )
        if not message_path.exists():
            raise RuntimeError(
                f"Codex task '{task_name}' did not produce {message_path}."
            )
        try:
            return json.loads(message_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Codex task '{task_name}' returned invalid JSON in {message_path}."
            ) from exc
