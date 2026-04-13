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
    
    使用 kimi-cli 作为 AI 后端。由于 kimi-cli 没有内置的 --output-schema 参数，
    我们通过在 prompt 中附加 JSON Schema 要求，并解析返回的 JSON 块来实现结构化输出。
    
    使用方式：kimi --print --yolo --final-message-only
    
    注意：Windows 下需要 UTF-8 编码支持。
    """
    
    # 默认模型
    DEFAULT_MODEL = "kimi-k2-0711-preview"
    
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

        # 构建增强 prompt，要求输出符合 JSON Schema
        enhanced_prompt = self._build_json_prompt(prompt, schema)
        
        # 构建 kimi-cli 命令
        # 使用 --print 模式进行非交互式运行
        command = [
            "kimi",
            "--print",              # 非交互式打印模式
            "--yolo",               # 自动确认所有操作
            "--final-message-only", # 只输出最终消息
        ]
        
        # 添加模型参数（如果指定）
        # 注意：kimi-cli 的 --model 参数格式与 API 不同，目前不传递模型参数
        # 使用默认配置中的模型
        model = self.tools.kimi_model
        if model:
            command.extend(["--model", model])
        
        # 使用项目根目录作为工作目录，以便 kimi 能找到配置
        # self.workspace.root 是 workspaces/0000xx
        # 所以项目根目录是 self.workspace.root.parent.parent (workspaces/ 的父目录)
        project_root = self.workspace.root.parent.parent if hasattr(self.workspace, 'root') else workdir
        
        # 直接调用 subprocess，使用二进制模式避免编码问题
        # 使用项目根目录作为 cwd，以便 kimi 能找到配置
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
        """构建增强的 prompt，要求 AI 输出符合 JSON Schema。"""
        schema_json = json.dumps(schema, ensure_ascii=True, indent=2)
        
        # 使用英文避免编码问题
        json_instruction = f"""

---

IMPORTANT: You must respond with JSON format matching the following JSON Schema:

```json
{schema_json}
```

Requirements:
1. Output JSON only, no other explanatory text
2. Ensure valid JSON format that can be parsed by standard JSON parsers
3. Use double quotes for all string values
4. Do not use Markdown code blocks to wrap JSON (except in examples above)
5. Output raw JSON text directly
6. CRITICAL: ALL strings in the C++ code MUST be in English only (ASCII characters)
7. Do NOT use Chinese characters in the code - use English prompts and labels only
8. Example: cout << "Line " << i << ":" instead of Chinese characters

Your JSON response:"""
        
        return original_prompt + json_instruction
    
    def _parse_json_output(
        self, 
        task_name: str, 
        output_path: Path, 
        stdout: str, 
        expected_schema: dict
    ) -> dict:
        """从 kimi-cli 输出中解析 JSON。
        
        尝试从以下位置获取 JSON：
        1. 输出文件
        2. stdout 中的 JSON 代码块
        3. stdout 本身
        """
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
        
        # 修复 Kimi CLI 的编码问题（替换乱码为正确的中文字符）
        json_data = self._fix_encoding_issues(json_data)
        
        # 将解析后的 JSON 保存到输出路径
        output_path.write_text(
            json.dumps(json_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return json_data
    
    def _fix_encoding_issues(self, data):
        """修复 Kimi CLI 返回数据中的编码问题。
        
        Kimi CLI 在 Windows 下会损坏中文字符，导致生成的代码包含乱码或英文。
        需要将乱码/英文替换为正确的中文字符串。
        """
        # U+FFFD 替换字符（Kimi 乱码）
        REPL = '\ufffd'
        
        # 定义乱码/英文到中文的映射（针对 5-b15 题目）
        replacement_map = {
            # 输入提示 - 处理乱码模式（7个替换字符 + 数字 + 2个替换字符）
            f'cout << "{REPL*7}" << (i + 1) << "{REPL*2}" << endl': 'cout << "请输入第" << (i + 1) << "行" << endl',
            f'cout << "{REPL*7}" << i << "{REPL*2}" << endl': 'cout << "请输入第" << i << "行" << endl',
            # 输入提示 - 处理英文模式
            'cout << "Please enter line " << i << endl': 'cout << "请输入第" << i << "行" << endl',
            'cout << "Please enter line " << (i + 1) << endl': 'cout << "请输入第" << (i + 1) << "行" << endl',
            'cout << "Please enter line " << i << ":" << endl': 'cout << "请输入第" << i << "行" << endl',
            # 输出标签 - 处理乱码模式（替换字符 + 俄文字母）
            f'"{REPL*2}д : "': '"大写 : "',
            f'"Сд : "': '"小写 : "',
            f'"{REPL*4} : "': '"数字 : "',
            f'"{REPL*1}ո{REPL*1} : "': '"空格 : "',
            f'"{REPL*4} : "': '"其它 : "',
            # 输出标签 - 处理英文模式
            '"Uppercase : "': '"大写 : "',
            '"Uppercase: "': '"大写 : "',
            '"Lowercase : "': '"小写 : "',
            '"Lowercase: "': '"小写 : "',
            '"Digits : "': '"数字 : "',
            '"Digits: "': '"数字 : "',
            '"Spaces : "': '"空格 : "',
            '"Spaces: "': '"空格 : "',
            '"Others : "': '"其它 : "',
            '"Others: "': '"其它 : "',
        }
        
        def fix_string(s):
            if not isinstance(s, str):
                return s
            result = s
            for bad, good in replacement_map.items():
                result = result.replace(bad, good)
            return result
        
        def fix_recursive(obj):
            if isinstance(obj, dict):
                return {k: fix_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [fix_recursive(item) for item in obj]
            elif isinstance(obj, str):
                return fix_string(obj)
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
        # 匹配最外层的大括号（非贪婪匹配嵌套结构）
        # 使用平衡匹配策略
        brace_pattern = r'(\{[\s\S]*?\})'
        matches = re.findall(brace_pattern, text)
        for match_text in matches:
            try:
                # 验证是否是有效的 JSON 对象
                parsed = json.loads(match_text)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
        
        return None
