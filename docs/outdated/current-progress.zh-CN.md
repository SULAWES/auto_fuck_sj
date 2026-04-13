# 当前进展

## 项目定位

`auto_fuck_sj` 目前已经是一个运行在 Windows 本地环境中的 MVP，可以用 Codex 求解课程作业型 C++ 子题，用 `demo.exe` 校验行为，并把完整过程保存在编号 workspace 中。

当前主链路已经具备：

- 读取题目文件
- 创建编号 workspace
- 加载提供的 grouped testcase
- 调用 Codex 生成候选 C++ 文件
- 用 `g++` 编译
- 运行 candidate 和 `demo.exe`
- 用 `txt_compare.exe` 比较输出
- 保存所有中间产物

## 已实现内容

- 单次运行的 CLI 入口
- 由 checked-in JSON spec 驱动的 `run-regression` 命令
- workspace 目录结构生成
- 尽力而为的题目文本提取
- grouped testcase 文件的本地回退解析器
- 按当前子题前缀过滤 provided testcase
- 通过 CLI、run manifest、regression spec、demo observations 和 evaluation 显式支持 `demo.exe` 参数
- 基于 Codex 的 JSON schema 生成流程
- 编译 / 运行 / compare 主循环
- 基础约束推断和风格检查
- humanizer 后处理流程
- 求解前的 demo 观测记录
- 用紧凑预览替代原始 compare dump 的结构化重试反馈
- UTF-8 安全的 `codex exec` prompt 提交
- 评测阶段的二进制 stdout 捕获
- 通过 `g++` 字符集参数完成 Windows 本地中文输出对齐

## 已验证内容

已在当前 Windows 机器上验证：

- `get_input_data.exe --all_group test_data.txt` 正常工作
- `5-b15-demo.exe` 和 `5-b16-demo.exe` 能正确处理提供的 grouped 输入
- `5-b16-demo.exe` 在 `--sub1`、`--sub2`、`--sub3`、`--sub4` 下会产生不同的目标输出
- `txt_compare.exe` 的成功 / 失败行为已经确认
- 当前 VS Code 扩展里的 `codex --version` 可以正常工作
- grouped testcase 选择逻辑会只保留当前子题前缀
- `run-regression` 已完成真实 5 job 验证并全部通过

参考已验证回归运行：

- `workspaces/000014`：`5-b15.cpp`，通过，测试用例数 = `5`
- `workspaces/000015`：`5-b16.cpp --sub1`，通过，测试用例数 = `1`
- `workspaces/000016`：`5-b16.cpp --sub2`，通过，测试用例数 = `1`
- `workspaces/000017`：`5-b16.cpp --sub3`，通过，测试用例数 = `1`
- `workspaces/000018`：`5-b16.cpp --sub4`，通过，测试用例数 = `1`

## 重要验证规则

`5-b16` 必须带明确的 demo 子题参数进行验证。直接裸跑 `5-b16-demo.exe` 不能作为这个作业的有效验证方式。应使用以下之一：

- `--sub1`
- `--sub2`
- `--sub3`
- `--sub4`

## 已解决的关键问题

- 当 PDF 文本无法提取时，solver 以前会猜题目提示语和输出格式。
- 带中文反馈的重试以前会因为 `codex exec` 的 stdin 没强制 UTF-8 而失败。
- candidate 输出以前会因为 Windows 本地中文输出编码未对齐而与 `demo.exe` 不一致。
- 评测时的文本重编码以前会破坏 compare 输入。
- 不相关的 grouped testcase 以前会泄漏到当前子题运行中。
- solver 重试以前会收到过大的原始 compare 日志，而不是紧凑失败摘要。
- `5-b16` 子题验证以前会忽略 `demo.exe` 所需的参数标志。

## 当前限制

- PDF 提取仍然只是尽力而为。
- 样例 PDF 包含多个子题，当前流程仍然依赖人工指定正确的 `demo.exe` 子题参数。
- 对许多硬限制的约束推断仍然偏浅。
- `5-b16` 当前在 `test_data.txt` 中只有一组 provided grouped testcase，因此回归覆盖仍然有限。
- 实时验证仍然依赖本地 Codex 可执行文件和 API / 网络链路在运行时可用。
