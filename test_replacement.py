#!/usr/bin/env python3
"""测试 Kimi 适配器的替换功能"""

import sys
sys.path.insert(0, 'src')

from auto_fuck_sj.kimi_adapter import KimiAdapter
import re

# 测试替换功能
test_code = '''
#include <iostream>
int main() {
    for (int i = 0; i < 3; i++) {
        cout << "Please enter line " << (i + 1) << endl;
    }
    cout << "Uppercase: " << count << endl;
    cout << "Lowercase: " << count << endl;
    cout << "Digits: " << count << endl;
    cout << "Spaces: " << count << endl;
    cout << "Others: " << count << endl;
    return 0;
}
'''

print("=== 原始代码 ===")
print(test_code)

print("\n=== 应用替换 ===")
for pattern, replacement in KimiAdapter.CHINESE_REPLACEMENTS.items():
    test_code = re.sub(pattern, replacement, test_code)

print("\n=== 替换后的代码 ===")
print(test_code)

# 验证替换结果
has_chinese = any('\u4e00' <= c <= '\u9fff' for c in test_code)
print(f"\n包含中文字符: {has_chinese}")

if "请输入第" in test_code and "大写 : " in test_code:
    print("替换成功！")
else:
    print("替换可能不完整，检查正则表达式")
