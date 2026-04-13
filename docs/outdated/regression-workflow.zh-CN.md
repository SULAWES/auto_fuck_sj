# 回归工作流

## 用途

当你希望用一个 checked-in spec 跑多个已知求解 job 时，使用 `run-regression`。

## 命令

```bash
python main.py run-regression --spec docs/regression-spec.example.json
```

如果当前机器上 PATH 里的默认 `codex` 不可运行，可以显式传入可执行路径：

```bash
python main.py run-regression --spec docs/regression-spec.example.json --codex-bin "C:\\path\\to\\codex.exe"
```

## Spec 格式

Spec 是一个 UTF-8 JSON 文件，顶层包含 `jobs` 数组。

每个 job 支持以下字段：

- `problem`：必填，题目文件路径
- `demo`：必填，demo 可执行文件路径
- `demo_args`：可选，传给 `demo.exe` 的附加参数
- `data`：可选，grouped testcase 文件路径
- `cpp_name`：可选，单个预期输出文件名
- `cpp_names`：可选，多个预期输出文件名的列表形式
- `entry_cpp`：可选，首选入口文件名
- `max_attempts`：可选，默认值为 `3`
- `generated_cases`：可选，默认值为 `5`
- `ban_tokens`：可选，额外禁用 token 列表

## 单次运行等价写法

做临时验证时，单 job 形式同样支持重复传 `--demo-arg`：

```bash
python main.py run \
  --problem .\\24252-050109-W1201.第05模块 作业 - PART4 - 字符数组与string类 - II.pdf \
  --demo .\\5-b16-demo.exe \
  --demo-arg=--sub1 \
  --data .\\test_data.txt \
  --cpp-name 5-b16.cpp \
  --generated-cases 0
```

## 如何新增一个子题

1. 把新的 `demo.exe` 放进仓库，或者放在稳定的本地路径上。
2. 确认 grouped testcase 文件中包含匹配的前缀，例如 `5-b16-*`。
3. 如果 PDF 说明 demo 需要子题开关，就通过 `demo_args` 显式写进去。
4. 在回归 spec 中加上对应 `cpp_name` 的 job，例如 `5-b16.cpp`。
5. 如果这个子题还没有被验证过，先跑一次单 job 命令。
6. 验证通过后，把这个 job 保留在回归 spec 里，作为后续回归基线。

## 当前已验证覆盖面

当前 checked-in 示例 spec 覆盖：

- `5-b15.cpp`
- `5-b16.cpp --sub1`
- `5-b16.cpp --sub2`
- `5-b16.cpp --sub3`
- `5-b16.cpp --sub4`

`5-b16` 必须带显式子题参数验证。直接裸跑 `5-b16-demo.exe` 不构成这个作业的有效验证。
