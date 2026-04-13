from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class AIAdapter(ABC):
    """AI 适配器抽象基类。
    
    支持不同的 AI 后端（Codex、Kimi 等），提供统一的接口用于：
    - 渲染 prompt 模板
    - 执行 JSON 结构化任务
    """
    
    def __init__(self, tools: Any, workspace: Any) -> None:
        self.tools = tools
        self.workspace = workspace
        self.agent_log_dir = workspace.log_dir("agent")
    
    @abstractmethod
    def render_prompt(self, prompt_name: str, **values: str) -> str:
        """渲染指定名称的 prompt 模板。
        
        Args:
            prompt_name: prompt 模板文件名（不含扩展名）
            **values: 模板变量替换值
            
        Returns:
            渲染后的 prompt 文本
        """
        pass
    
    @abstractmethod
    def run_json_task(
        self,
        *,
        task_name: str,
        prompt: str,
        schema: dict,
        workdir: Path,
        sandbox: str = "read-only",
    ) -> dict:
        """执行一个返回 JSON 结构化输出的 AI 任务。
        
        Args:
            task_name: 任务名称（用于日志记录）
            prompt: 发送给 AI 的 prompt 文本
            schema: 期望输出的 JSON Schema
            workdir: 工作目录
            sandbox: 沙箱模式（默认 read-only）
            
        Returns:
            解析后的 JSON 字典
            
        Raises:
            RuntimeError: 当任务执行失败或返回无效 JSON 时
        """
        pass
