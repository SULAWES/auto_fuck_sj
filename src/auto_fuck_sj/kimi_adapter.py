from __future__ import annotations

import json
import os
import re
import subprocess
from importlib import resources
from pathlib import Path
from string import Template

from .ai_adapter import AIAdapter
from .models import ToolConfig
from .workspace import Workspace


class KimiAdapter(AIAdapter):
    """Kimi CLI 适配器。
    
    使用 kimi-cli 作为 AI 后端。由于 kimi-cli 在 Windows 下对非 ASCII 字符
    的 JSON 序列化存在问题，我们采用 ASCII-only 策略：
    
    1. 要求 Kimi 生成纯 ASCII（英文）的 C++ 代码
    2. 在后端自动将英文标签替换为对应的中文
    
    使用方式：kimi --print --yolo --final-message-only
    """
    
    # 默认模型
    DEFAULT_MODEL = "kimi-k2-0711-preview"
    
    # 英文到中文的替换映射（用于 5-b15 类型题目）
    # 这些替换在代码生成后自动应用
    CHINESE_REPLACEMENTS = {
        # 输入提示
        r'cout\s*<<\s*"Please enter line "\s*<<\s*i\s*<<\s*endl': 'cout << "请输入第" << i << "行" << endl',
        r'cout\s*<<\s*"Please enter line "\s*<<\s*\(i\s*\+\s*1\)\s*<<\s*endl': 'cout << "请输入第" << (i + 1) << "行" << endl',
        r'cout\s*<<\s*"Enter line "\s*<<\s*i\s*<<\s*endl': 'cout << "请输入第" << i << "行" << endl',
        r'cout\s*<<\s*"Enter line "\s*<<\s*\(i\s*\+\s*1\)\s*<<\s*endl': 'cout << "请输入第" << (i + 1) << "行" << endl',
        # 带冒号的变体
        r'cout\s*<<\s*"Please enter line "\s*<<\s*i\s*<<\s*":"?\s*<<\s*endl': 'cout << "请输入第" << i << "行" << endl',
        r'cout\s*<<\s*"Please enter line "\s*<<\s*\(i\s*\+\s*1\)\s*<<\s*":"?\s*<<\s*endl': 'cout << "请输入第" << (i + 1) << "行" << endl',
        
        # 输出标签 - 英文到中文
        r'"Uppercase\s*:?\s*"': '"大写 : "',
        r'"Lowercase\s*:?\s*"': '"小写 : "',
        r'"Digits?\s*:?\s*"': '"数字 : "',
        r'"Spaces?\s*:?\s*"': '"空格 : "',
        r'"Others?\s*:?\s*"': '"其它 : "',
        r'"Other\s*:?\s*"': '"其它 : "',
    }
    
    def __init__(self, tools: ToolConfig, workspace: Workspace) -> None:
        super().__init__(tools, workspace)
        self.tools = tools
        self.workspace = workspace

    def render_prompt(self, prompt_name: str, **values: str) -> str:
        template_text = (
            resources.files("auto_fuck_sj")
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
        output_path = self.agent_log_dir / f"{task_name}_output.json"

        # 保存原始 prompt 和 schema
        prompt_path.write_text(prompt, encoding="utf-8")
        schema_path.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 构建增强 prompt，要求 ASCII-only 输出
        enhanced_prompt = self._build_json_prompt(prompt, schema)
        
        # 构建 kimi-cli 命令
        command = [
            "kimi",
            "--print",              # 非交互式打印模式
            "--yolo",               # 自动确认所有操作
            "--final-message-only", # 只输出最终消息
        ]
        
        # 添加模型参数（如果指定）
        model = self.tools.kimi_model
        if model:
            command.extend(["--model", model])
        
        # 使用项目根目录作为工作目录
        project_root = self.workspace.root.parent.parent if hasattr(self.workspace, 'root') else workdir
        
        # 调用 kimi-cli
        try:
            result = subprocess.run(
                command,
                cwd=project_root,
                input=enhanced_prompt.encode('utf-8'),
                capture_output=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"Kimi task '{task_name}' timed out after 300 seconds."
            ) from exc
        
        # 解码输出，使用 replace 错误处理
        stdout_text = result.stdout.decode('utf-8', errors='replace')
        stderr_text = result.stderr.decode('utf-8', errors='replace')
        
        # 记录输出
        stdout_path.write_text(stdout_text, encoding="utf-8")
        stderr_path.write_text(stderr_text, encoding="utf-8")

        if result.returncode != 0:
            # 检查是否是配置问题
            if "LLM not set" in stdout_text or "LLM not set" in stderr_text:
                raise RuntimeError(
                    f"Kimi task '{task_name}' failed: LLM not configured. "
                    f"Please run 'kimi login' first or set MOONSHOT_API_KEY environment variable."
                )
            raise RuntimeError(
                f"Kimi task '{task_name}' failed with exit code {result.returncode}. "
                f"See {stdout_path} and {stderr_path}."
            )
        
        # 解析输出中的 JSON
        return self._parse_json_output(task_name, output_path, stdout_text, schema)
    
    def _build_json_prompt(self, original_prompt: str, schema: dict) -> str:
        """构建增强的 prompt，要求 AI 输出 ASCII-only 的 JSON。"""
        schema_json = json.dumps(schema, ensure_ascii=True, indent=2)
        
        # 要求 ASCII-only 输出，避免 Windows 编码问题
        json_instruction = f"""

---

IMPORTANT: You must respond with JSON format matching the following JSON Schema:

```json
{schema_json}
```

CRITICAL REQUIREMENTS:
1. Output valid JSON only, no other explanatory text
2. ALL strings in the JSON MUST be ASCII-only (English characters only)
3. For C++ code that needs Chinese output, use English strings like:
   - "Please enter line " instead of Chinese
   - "Uppercase: ", "Lowercase: ", "Digits: ", "Spaces: ", "Others: " for labels
4. Do not use Markdown code blocks to wrap JSON (except in examples above)
5. Output raw JSON text directly

The system will automatically translate English labels to Chinese in post-processing.

Your ASCII-only JSON response:"""
        
        return original_prompt + json_instruction
    
    def _parse_json_output(
        self, 
        task_name: str, 
        output_path: Path, 
        stdout: str, 
        expected_schema: dict
    ) -> dict:
        """从 kimi-cli 输出中解析 JSON 并进行后处理。"""
        raw_text = stdout.strip()
        
        # 尝试提取 JSON 代码块
        json_data = self._extract_json_from_text(raw_text)
        
        if json_data is None:
            # 保存原始输出用于调试
            debug_path = output_path.parent / f"{task_name}_raw_output.txt"
            debug_path.write_text(raw_text, encoding="utf-8")
            raise RuntimeError(
                f"Kimi task '{task_name}' did not return valid JSON. "
                f"Raw output saved to {debug_path}."
            )
        
        # 后处理：将英文标签替换为中文
        json_data = self._apply_chinese_replacements(json_data)
        
        # 将解析后的 JSON 保存到输出路径
        output_path.write_text(
            json.dumps(json_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return json_data
    
    def _apply_chinese_replacements(self, data):
        """将代码中的英文标签替换为中文。
        
        遍历 data 中的所有字符串，对 C++ 代码内容应用替换规则。
        """
        def fix_code_content(content: str) -> str:
            if not isinstance(content, str):
                return content
            
            result = content
            # 应用所有替换规则
            for pattern, replacement in self.CHINESE_REPLACEMENTS.items():
                result = re.sub(pattern, replacement, result)
            return result
        
        def fix_recursive(obj):
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    # 对 content 字段（通常是代码）应用替换
                    if k == "content" and isinstance(v, str):
                        result[k] = fix_code_content(v)
                    else:
                        result[k] = fix_recursive(v)
                return result
            elif isinstance(obj, list):
                return [fix_recursive(item) for item in obj]
            return obj
        
        return fix_recursive(data)
    
    def _extract_json_from_text(self, text: str) -> dict | None:
        """从文本中提取 JSON 对象。
        
        尝试以下方式：
        1. 提取 ```json ... ``` 代码块
        2. 提取 ``` ... ``` 代码块
        3. 直接解析整个文本
        4. 寻找文本中的第一个 { ... } 结构
        """
        text = text.strip()
        
        # 尝试匹配 ```json ... ``` 代码块
        json_block_pattern = r'```json\s*\n(.*?)\n```'
        match = re.search(json_block_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # 尝试匹配 ``` ... ``` 代码块（无语言标记）
        generic_block_pattern = r'```\s*\n(.*?)\n```'
        match = re.search(generic_block_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # 尝试直接解析整个文本
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 尝试寻找文本中的第一个 { ... } 或 [ ... ] 结构
        brace_pattern = r'(\{[\s\S]*?\})'
        matches = re.findall(brace_pattern, text)
        for match_text in matches:
            try:
                parsed = json.loads(match_text)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
        
        return None
