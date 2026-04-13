# auto_fuck_sj

一个面向 Windows 的课程作业型 C++ 自动求解 MVP 编排器。

当前重点：

- 一次只处理一个子题
- 只使用 Codex 作为代理后端
- 使用 `g++` 编译
- 用 `demo.exe` 作为标准输出行为对照
- 将所有中间产物保存在独立编号的 workspace 中

当前已验证状态：

- 已在真实 Windows 环境下验证 `5-b15.cpp` 端到端通过
- 已在真实 Windows 环境下验证 `5-b16.cpp` 配合 `--sub1`、`--sub2`、`--sub3`、`--sub4` 端到端通过
- 已于 2026 年 3 月 9 日完成 5 个任务的真实回归运行，结果位于 `workspaces/000014` 到 `workspaces/000018`
- grouped testcase 选择逻辑会按当前子题前缀进行过滤
- `demo.exe` 参数已经进入单次运行与回归 spec 的正式链路

## 当前版本已有内容

- 带持久化产物的 workspace 创建逻辑
- 尽力而为的题面文本提取
- 通过 `get_input_data.exe` 加载提供的测试数据
- 在缺少 Windows 工具时的本地 grouped testcase 解析回退
- 基于 Codex 的测试用例生成
- 基于 Codex 的 C++ 源码生成
- 带重试反馈的编译 / 运行 / 对比主循环
- 基础硬约束检查与风格检查
- 通过回归测试保护的人化后处理步骤
- 在求解前记录 demo 观测结果以推断输出格式
- 结构化重试反馈摘要
- 由 JSON spec 驱动的回归命令
- 同时支持单次运行和回归运行的 `demo.exe` 参数传递
- 面向中文控制台输出的 Windows 本地编码对齐策略

## 当前限制

- PDF 提取仍然只是尽力而为
- 多个生成的 `.cpp` 文件会被当作一个程序一起编译
- 如果题目实际上要求多个彼此独立的程序，需要拆成多个 job
- 硬约束目前一部分来自题面推断，一部分来自 CLI 显式配置
- `5-b16` 仍然依赖你根据 PDF 手动指定正确的 `--subN` 参数
- 当前 `5-b16` 的验证仍只覆盖 `test_data.txt` 中的一组 provided grouped testcase，覆盖面偏窄

## 使用方式

在仓库根目录运行：

```bash
python main.py run \
  --problem path/to/problem.pdf \
  --demo path/to/demo.exe \
  --data path/to/hw_data.txt \
  --cpp-name main.cpp \
  --workspace-root workspaces
```

常用参数：

- `--cpp-name`：可重复，声明预期生成的源文件名
- `--entry-cpp`：多文件情况下指定首选入口文件名
- `--demo-arg`：传给 `demo.exe` 的附加参数，可重复
- `--ban-token`：额外禁用 token，可重复
- `--generated-cases`：请求 Codex 生成测试用例的数量
- `--codex-model`：可选，覆盖 `codex exec` 使用的模型
- `--codex-bin`：当 PATH 中的 `codex` 不可执行时，显式指定可运行路径

`5-b16` 子题验证示例：

```bash
python main.py run \
  --problem ".\\24252-050109-W1201.第05模块 作业 - PART4 - 字符数组与string类 - II.pdf" \
  --demo .\\5-b16-demo.exe \
  --demo-arg=--sub1 \
  --data .\\test_data.txt \
  --cpp-name 5-b16.cpp \
  --generated-cases 0
```

## 回归用法

运行 checked-in spec 中定义的多个 job：

```bash
python main.py run-regression --spec docs/regression-spec.example.json
```

当前示例 spec 覆盖 `5-b15` 以及 `5-b16 --sub1..--sub4`。

## Workspace 结构

每次运行都会创建一个编号 workspace：

```text
workspaces/000001/
  input/
  extracted/
  testcases/
  candidates/
  outputs/
  logs/
  final/
```

## 建议的 Windows 环境

确保以下命令在目标 Windows 机器上可调用：

- `codex`
- `g++`
- `txt_compare.exe`
- `get_input_data.exe`
- 与当前题目匹配的 `demo.exe`

然后运行：

```bash
python main.py run --problem problem.pdf --demo demo.exe --data hw_data.txt
```

## 下一步

- 在这台 Windows 机器上安装 `pdftotext` 并重新验证提取质量
- 加强对禁用语法与子题特定例外的硬约束推断
- 增加稳定定位可运行 `codex.exe` 的策略
- 扩充真实 grouped testcase 的回归覆盖范围
