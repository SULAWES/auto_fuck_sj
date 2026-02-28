from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Workspace:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.input_dir = root / "input"
        self.extracted_dir = root / "extracted"
        self.testcases_dir = root / "testcases"
        self.candidates_dir = root / "candidates"
        self.outputs_dir = root / "outputs"
        self.logs_dir = root / "logs"
        self.final_dir = root / "final"

    @classmethod
    def create(cls, workspaces_root: Path) -> "Workspace":
        workspaces_root.mkdir(parents=True, exist_ok=True)
        existing = sorted(
            int(path.name)
            for path in workspaces_root.iterdir()
            if path.is_dir() and path.name.isdigit()
        )
        next_id = (existing[-1] + 1) if existing else 1
        root = workspaces_root / f"{next_id:06d}"
        instance = cls(root)
        instance.ensure_layout()
        return instance

    def ensure_layout(self) -> None:
        for path in (
            self.root,
            self.input_dir,
            self.extracted_dir,
            self.testcases_dir,
            self.candidates_dir,
            self.outputs_dir,
            self.logs_dir,
            self.final_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def candidate_attempt_dir(self, attempt: int) -> Path:
        path = self.candidates_dir / f"attempt_{attempt:02d}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def output_attempt_dir(self, attempt: int) -> Path:
        path = self.outputs_dir / f"attempt_{attempt:02d}"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def log_dir(self, *parts: str) -> Path:
        path = self.logs_dir.joinpath(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "root": str(self.root),
            "input_dir": str(self.input_dir),
            "extracted_dir": str(self.extracted_dir),
            "testcases_dir": str(self.testcases_dir),
            "candidates_dir": str(self.candidates_dir),
            "outputs_dir": str(self.outputs_dir),
            "logs_dir": str(self.logs_dir),
            "final_dir": str(self.final_dir),
        }
