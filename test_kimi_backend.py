#!/usr/bin/env python3
"""测试 Kimi 后端 - 完全不含中文的 schema"""

import subprocess
import json

# 完全 ASCII-only 的 prompt
test_prompt = """You are generating a coursework-style C++ submission.

Task: Generate a C++ program that counts character types in 3 lines of input.

Requirements:
1. Read 3 lines of input using cin.getline or getline
2. Count uppercase, lowercase, digits, spaces, and other characters
3. Print counts with labels

IMPORTANT: Output the C++ code using ENGLISH ONLY for all strings.
Example: cout << "Uppercase: " << count << endl;

The code will be post-processed to replace English labels with Chinese.

Output format: JSON with the following structure (ENGLISH ONLY):
{
  "files": [
    {
      "filename": "count.cpp",
      "content": "ASCII only C++ source code"
    }
  ],
  "assumptions": "brief description in English"
}

ALL string values MUST be ASCII-only (English characters only).
"""

schema = {
    "type": "object",
    "properties": {
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["filename", "content"]
            }
        },
        "assumptions": {"type": "string"}
    },
    "required": ["files"]
}

schema_json = json.dumps(schema, ensure_ascii=True, indent=2)
enhanced_prompt = test_prompt + f"""

---

CRITICAL: You must respond with JSON format matching the schema below.
ALL strings in the JSON MUST be ASCII-only (English characters only).

```json
{schema_json}
```

Your JSON response (ASCII-only):"""

print("=" * 60)
print("Testing Kimi CLI with ASCII-only schema...")
print("=" * 60)

command = [
    "kimi",
    "--print",
    "--yolo",
    "--final-message-only",
]

try:
    result = subprocess.run(
        command,
        cwd=r"D:\Dev\auto_fuck_sj",
        input=enhanced_prompt.encode('utf-8'),
        capture_output=True,
        timeout=180,
    )
    
    print(f"Return code: {result.returncode}")
    
    stdout_text = result.stdout.decode('utf-8', errors='replace')
    
    print("\n--- STDOUT (first 2000 chars) ---")
    print(stdout_text[:2000])
    
    # 尝试解析 JSON
    print("\n--- JSON Parsing ---")
    
    import re
    
    data = None
    for pattern in [r'```json\s*\n(.*?)\n```', r'```\s*\n(.*?)\n```']:
        match = re.search(pattern, stdout_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1).strip())
                print("[OK] Found JSON in code block")
                break
            except json.JSONDecodeError as e:
                print(f"  Block parse error: {e}")
    
    if not data:
        try:
            data = json.loads(stdout_text.strip())
            print("[OK] Direct JSON parse successful")
        except json.JSONDecodeError as e:
            print(f"[FAIL] Direct parse error: {e}")
    
    if data and data.get('files'):
        code = data['files'][0]['content']
        print(f"\n--- Generated Code (first 1000 chars) ---")
        print(code[:1000])
        
        # 检查是否全 ASCII
        is_ascii = all(ord(c) < 128 for c in code)
        print(f"\nCode is ASCII-only: {is_ascii}")

except subprocess.TimeoutExpired:
    print("[FAIL] Timeout after 180 seconds")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()
