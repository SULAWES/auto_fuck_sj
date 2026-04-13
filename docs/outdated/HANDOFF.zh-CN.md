# Windows 交接说明

## 目的

这个仓库是一个运行在 Windows 本地环境中的课程作业型 C++ 自动求解编排器 MVP。

主要目标：

- 读取课程题目材料
- 用 Codex 生成一个或多个要求提交的源文件
- 用 `g++` 编译
- 让候选程序与 `demo.exe` 对照运行
- 用 `txt_compare.exe` 比较输出
- 将所有中间产物保留在独立的 workspace 中

## 当前状态

已实现：

- 仓库骨架和 CLI 入口
- 编号式 workspace 创建
- 可用时通过 `pdftotext` 进行 PDF 文本提取
- 面向中文课程材料的尽力文本解码
- 供本地开发使用的 grouped testcase 解析回退
- 基于 Codex 的结构化 JSON 生成链路
- 编译 / 运行 / 对比编排骨架
- 硬约束推断和基础风格检查
- 通过 demo 输出观测增强 solver prompt
- UTF-8 安全的 `codex exec` prompt 提交
- demo 与 candidate 评测时的二进制 stdout 捕获
- 通过 Windows `g++` 字符集参数对齐本地中文控制台输出

已在当前 Windows 机器上验证：

- `get_input_data.exe --all_group test_data.txt` 正常工作
- `5-b15-demo.exe` 能正确处理 grouped test input
- `txt_compare.exe` 的成功 / 失败提示字符串已经确认
- `codex exec --output-schema` 能在 Windows shell 中工作
- `5-b15.cpp` 在 `workspaces/000008` 上端到端通过
- `5-b16.cpp` 配合 `--sub1`、`--sub2`、`--sub3`、`--sub4` 已完成真实验证

当前已知限制：

- PDF 提取仍然只是尽力而为
- 样例 PDF 包含多个子题，当前流程仍更适合一次跑一个子题
- 成功的输出匹配仍然依赖 Windows 本地编码行为和 `g++` 字符集参数
- 对 `no scanf/printf`、`no class`、`no struct` 以及子题例外规则的约束推断仍然较浅

## 重要文件

建议先读：

1. `需求.md`
2. `方案.md`
3. `README.md`
4. `src/auto_fuck_sj/cli.py`
5. `src/auto_fuck_sj/orchestrator.py`
6. `src/auto_fuck_sj/codex_adapter.py`
7. `src/auto_fuck_sj/constraints.py`

如果要看最近的已验证样例运行，再读：

1. `workspaces/000008/outputs/attempt_01/evaluation_summary.json`
2. `workspaces/000008/final/5-b15.cpp`
3. `workspaces/000015/final/5-b16.cpp`
4. `workspaces/000018/final/5-b16.cpp`

## 当前样例输入

仓库根目录当前包含：

- `24252-050109-W1201.第05模块 作业 - PART4 - 字符数组与string类 - II.pdf`
- `test_data.txt`
- `5-b15-demo.exe`
- `5-b16-demo.exe`
- `get_input_data.exe`
- `txt_compare.exe`

说明：

- `test_data.txt` 被识别为 `gb18030`
- 当前样例 PDF 包含多个子题，而不是单题
- `5-b16` 必须结合 PDF 中的子题说明给 `demo.exe` 传 `--subN`

## 最新进展

前一轮交接建议先做第一轮真实 Windows 端到端运行，这一步已经完成，并且已经扩展到 `5-b16`。

代码层面的关键变化：

- 编排器会在求解前写出 `testcases/demo_observations.json`，基于选中的 provided case 记录真实 `demo.exe` 输出
- solver prompt 会读取这些观测结果，从而在不猜测的情况下对齐提示文字与输出格式
- `codex exec` 现在显式使用 UTF-8 喂 prompt，避免中文反馈在重试时因为 stdin 编码失败
- 评测阶段会先按原始字节捕获 demo 与 candidate stdout，再写文件，避免文本重编码损坏 compare 输入
- 调用 `g++` 时使用 `-finput-charset=UTF-8` 和 `-fexec-charset=GBK`，让 UTF-8 源码字面量生成与 Windows 本地 `demo.exe` 兼容的中文字节流
- 运行请求中已经支持 `demo.exe` 参数，`5-b16` 的 `--sub1..--sub4` 会进入观测、评测和回归 spec

已验证内容：

- `5-b15.cpp` 已经返回 `"status": "passed"`
- `workspaces/000008` 的 `evaluation_summary.json` 报告 `all_passed: true`
- `5-b16.cpp` 已分别在 `--sub1`、`--sub2`、`--sub3`、`--sub4` 模式下通过真实回归验证，对应 `workspaces/000015` 到 `workspaces/000018`

## 行为预期

用户已经明确风格目标：

- 不要过度工程化
- 仍然体现基础计算机科学训练
- 核心逻辑不要使用 `a`、`b`、`c`、`d` 这类无意义命名
- 不要使用拼音变量名
- 先保证正确性，再考虑风格

用户还明确了：

- 第一版优先保证“最可能运行成功”
- Windows 编译目标是 `g++`
- 最终输出必须保留中间产物
- 题目经常带硬限制
- `get_input_data.exe` 是默认主工具，少数作业可能会要求 `get_input_data2.exe`

## 建议的下一步

1. 在 Windows 上安装并验证 PDF 文本提取器，优先 `pdftotext`，减少对 demo 观测的依赖。
2. 强化对子题规则和禁用语法的题面提取能力，例如 `no string`、`no scanf/printf`、`no struct/class` 等。
3. 增加稳定定位可运行 `codex.exe` 的后备策略。
4. 扩充 `5-b16` 的测试数据覆盖，不要只依赖当前这一组 grouped testcase。
5. 评估编译器参数做字符集转换是否应继续作为长期方案。

## 给新 Codex 窗口的建议提示词

```text
先读 HANDOFF.md，然后读 需求.md、方案.md、README.md、src/auto_fuck_sj/cli.py 和 src/auto_fuck_sj/orchestrator.py。
这个仓库是一个运行在 Windows 本地环境中的课程作业型 C++ 自动求解编排器 MVP。
现在已经完成 `5-b15.cpp` 以及 `5-b16 --sub1..--sub4` 的真实验证，包括真实执行 `get_input_data.exe`、`demo.exe`、`txt_compare.exe` 和 `codex exec --output-schema`。
接下来从 PDF 提取增强、约束处理强化、以及扩大回归覆盖面继续推进。
```
