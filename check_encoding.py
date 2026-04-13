import json
import re

with open('workspaces/000040/candidates/attempt_01/solver_notes.json', 'r', encoding='utf-8', errors='replace') as f:
    data = json.load(f)

content = data['files'][0]['content']

# 获取第37-41行
lines = content.split('\n')
for i in range(37, 42):
    line = lines[i]
    match = re.search(r'"(.*?)"', line)
    if match:
        s = match.group(1)
        print(f'Line {i}: {repr(s)}')
        print(f'  Codepoints: {[hex(ord(c)) for c in s]}')
        print()
