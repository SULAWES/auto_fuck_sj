# 行动追踪

这个文件用于追踪具体工作项。每完成一项就做标记。

## 已完成

- [x] 创建仓库骨架和 CLI 入口。
- [x] 实现 workspace 创建和产物目录布局。
- [x] 增加 grouped testcase 加载能力。
- [x] 增加 grouped testcase 的本地回退解析。
- [x] 增加基于 Codex 的 JSON schema 生成流程。
- [x] 增加编译 / 运行 / compare 编排逻辑。
- [x] 在 Windows 上验证 `get_input_data.exe`。
- [x] 在 Windows 上验证 `txt_compare.exe` 行为。
- [x] 在 Windows 上验证 `codex exec --output-schema`。
- [x] 对 `5-b15.cpp` 完成一次真实 Windows 端到端运行。
- [x] 在 solver 执行前增加 demo 观测记录。
- [x] 修复重试阶段 prompt 提交的 UTF-8 问题。
- [x] 在评测阶段保留原始 stdout 字节。
- [x] 对齐 candidate 中文输出与 Windows 本地行为。
- [x] 在 `docs/` 下补齐项目文档。
- [x] 将 grouped testcase 过滤到当前子题前缀。
- [x] 用结构化失败摘要替代原始 compare dump。
- [x] 增加回归式重复验证命令。
- [x] 记录如何为回归覆盖增加新的样例子题。
- [x] 补充或获取 `5-b16-demo.exe`。
- [x] 将显式 `demo.exe` 参数支持接入运行主链路。
- [x] 用 `--sub1` 跑通 `5-b16.cpp` 全流程。
- [x] 用 `--sub2` 跑通 `5-b16.cpp` 全流程。
- [x] 用 `--sub3` 跑通 `5-b16.cpp` 全流程。
- [x] 用 `--sub4` 跑通 `5-b16.cpp` 全流程。
- [x] 确认当前 prompt 和编码策略能泛化到另一个子题。
- [x] 用至少两个真实 job 验证 `run-regression`。

## 下一步行动

- [ ] 在 Windows 机器上安装 `pdftotext`。
- [ ] 验证当前样例 PDF 的文本提取质量。
- [ ] 改进对 `string`、`scanf/printf`、`class`、`struct` 等禁用项的约束推断。
- [ ] 增加稳定定位可运行 `codex.exe` 的方式。
- [ ] 补一份从 PDF 子题描述到 `demo.exe` 参数标志的明确映射文档。
- [ ] 将回归覆盖扩展到当前这组 `5-b16` grouped testcase 之外。

## 后续行动

- [ ] 评估基于编译器参数的字符集转换是否应该作为长期方案保留。
- [ ] 改进 humanizer 安全检查与回归覆盖。
- [ ] 探索当课程确实要求多文件提交时的支持方式。
