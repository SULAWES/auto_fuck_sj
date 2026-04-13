# 待办事项 (TODO)

本文档追踪具体工作项。完成后请标记。

## 已完成

- [x] 创建仓库骨架和 CLI 入口
- [x] 实现工作区创建和产物目录布局
- [x] 增加分组测试用例加载能力
- [x] 增加分组测试用例的本地回退解析
- [x] 增加基于 Codex 的 JSON Schema 生成流程
- [x] 增加编译 / 运行 / 比对编排逻辑
- [x] 在 Windows 上验证 `get_input_data.exe`
- [x] 在 Windows 上验证 `txt_compare.exe` 行为
- [x] 在 Windows 上验证 `codex exec --output-schema`
- [x] 对 `5-b15.cpp` 完成真实 Windows 端到端运行
- [x] 在求解器执行前增加 demo 观测记录
- [x] 修复重试阶段 prompt 提交的 UTF-8 问题
- [x] 在评测阶段保留原始 stdout 字节
- [x] 对齐候选代码中文输出与 Windows 本地行为
- [x] 在 `docs/` 下补齐项目文档
- [x] 将分组测试用例过滤到当前子题前缀
- [x] 用结构化失败摘要替代原始比对日志
- [x] 增加回归式重复验证命令
- [x] 记录如何为回归覆盖增加新的样例子题
- [x] 补充或获取 `5-b16-demo.exe`
- [x] 将显式 `demo.exe` 参数支持接入运行主链路
- [x] 用 `--sub1` 跑通 `5-b16.cpp` 全流程
- [x] 用 `--sub2` 跑通 `5-b16.cpp` 全流程
- [x] 用 `--sub3` 跑通 `5-b16.cpp` 全流程
- [x] 用 `--sub4` 跑通 `5-b16.cpp` 全流程
- [x] 确认当前 prompt 和编码策略能泛化到另一个子题
- [x] 用至少两个真实任务验证 `run-regression`

## 进行中

- [ ] **工作区 000044 任务中断恢复**（5-b15.cpp 端到端运行）
  - [x] 工作区初始化完成
  - [x] 题目上下文提取完成
  - [x] 测试用例加载完成（5 个 provided cases）
  - [x] Demo 观测记录完成
  - [x] Attempt 01 Prompt 和 Schema 准备就绪
  - [ ] AI 代码生成（中断处）
  - [ ] 编译验证
  - [ ] 测试比对
  - [ ] 结果归档

## 下一步行动

- [ ] 在 Windows 机器上安装 `pdftotext`
- [ ] 验证当前样例 PDF 的文本提取质量
- [ ] 改进对 `string`、`scanf/printf`、`class`、`struct` 等禁用项的约束推断
- [ ] 增加稳定定位可运行 `codex.exe` 的方式
- [ ] 补一份从 PDF 子题描述到 `demo.exe` 参数标志的明确映射文档
- [ ] 将回归覆盖扩展到当前 `5-b16` 分组测试用例之外

## 后续行动

- [ ] 评估基于编译器参数的字符集转换是否应该作为长期方案保留
- [ ] 改进人性化处理的安全检查与回归覆盖
- [ ] 探索当课程作业确实要求多文件提交时的支持方式

## 已完成 ✓

- [x] 在抽象层接入 kimi-cli
  - [x] 设计 AI 适配器抽象基类 (`ai_adapter.py`)
  - [x] 重构 CodexAdapter 继承抽象基类
  - [x] 实现 KimiAdapter 支持 kimi-cli (`kimi_adapter.py`)
  - [x] 添加 `--ai-backend` 命令行参数
  - [x] 添加 `--kimi-model` 参数支持模型选择
  - [x] 实现 kimi-cli 的 JSON 输出约束（通过 prompt 增强）
  - [x] 测试 kimi-cli 集成（使用 5-b15 题目验证通过）

## AI 后端状态

| 后端 | 状态 | 说明 |
|------|------|------|
| **Codex** | ✅ **稳定可用** | 已通过多次端到端测试验证，包括 5-b15、5-b16 各子题 |
| **Kimi CLI** | 🔧 **测试/调试中** | 基础功能已实现，Windows 下可能存在中文编码问题，仍在测试稳定化 |

**默认后端**: Codex（推荐用于生产环境）

**使用 Kimi 后端**: `python main.py run ... --ai-backend kimi --kimi-model kimi-k2-5
