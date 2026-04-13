# 设计概览

## 1. 项目概述

**auto_fuck_sj** 是一个 Windows 平台下的 C++ 课程作业自动解题编排器。它通过编排外部 AI Agent（Codex CLI）和本地 Windows 工具链，实现从题目 PDF 到可提交 C++ 代码的全自动转换。

### 1.1 核心目标

- **输入**：题目 PDF + 标准答案程序 `demo.exe` + 可选测试数据
- **输出**：符合题目要求的、风格像学生作品的 C++ 代码
- **约束**：通过 `demo.exe` 的所有测试用例，遵守题目硬性限制（禁用语法等）

### 1.2 运行环境

- **平台**：Windows（依赖 Windows 控制台编码和本地可执行文件）
- **编译器**：g++ (MinGW)
- **AI 后端**：Codex CLI（通过命令行调用）

---

## 2. 设计原则

### 2.1 编排器主导（Orchestrator-Centric）

不采用"多 Agent 自由协作"的复杂架构，而是：**一个中心编排器 + 多个独立阶段**。阶段之间不直接通信，仅通过工作区文件交换信息。

**优点**：
- 调试简单，可单独复现任一阶段
- 避免上下文污染（解题 Agent 不会被测试细节干扰）
- 易于替换 Agent 实现

### 2.2 文件即接口（Files as API）

每个阶段的输入输出都是明确定义的文件：

| 阶段 | 输入文件 | 输出文件 |
|------|----------|----------|
| 题目摄入 | `problem.pdf` | `problem_context.md`, `constraint_hints.json` |
| 测试生成 | `problem_context.md` | `generated_cases.json` |
| 求解器 | `problem_context.md`, `merged_cases.json`, `demo_observations.json` | `candidates/v1/*.cpp`, `solver_notes.json` |
| 评测器 | 候选代码 + 测试用例 | `evaluation_summary.json`, `compare_result.json` |
| 人性化处理 | 候选代码 + 风格警告 | `humanized/*.cpp` |

### 2.3 工作区隔离

每次运行创建独立工作区 `workspaces/000001/`，保留完整过程痕迹：
- 便于人工复查失败原因
- 支持并发运行（未来扩展）
- 可归档历史记录

### 2.4 反馈闭环

评测失败时，提取结构化摘要（而非完整日志）反馈给求解器：
- 编译错误摘要
- 首个不匹配测试用例的输入/期望/实际输出预览
- 约束违规提示

---

## 3. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI 入口 (cli.py)                     │
│                   - 命令行解析                               │
│                   - 配置组装                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   编排器 (orchestrator.py)                   │
│              主编排器：调度各阶段，管理全局状态               │
└──────┬─────────┬─────────┬─────────┬─────────┬──────────────┘
       │         │         │         │         │
       ▼         ▼         ▼         ▼         ▼
   ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐
   │题目摄入│  │测试生成│  │求解器 │  │评测器 │  │人性化处理 │
   └──────┘  └──────┘  └──────┘  └──────┘  └──────────┘
       │         │         │         │         │
       └─────────┴─────────┴─────────┴─────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   Codex 适配器   │  ← 封装 Codex CLI 调用
              └─────────────────┘
```

### 3.1 核心组件

#### 编排器（`AutomaticGC` 类）

- **职责**：全流程编排、状态管理、循环控制
- **关键方法**：
  - `run()`：主入口，管理多轮尝试循环
  - `_ingest_problem()`：题目摄入
  - `_build_testcases()`：测试数据构建
  - `_run_solver()`：调用 AI 生成代码
  - `_evaluate_attempt()`：编译评测
  - `_run_humanizer()`：风格降级
- **循环逻辑**：最多 N 轮尝试，每轮失败则反馈优化，成功则进入风格降级
- **AI 适配器管理**：通过 `_create_ai_adapter()` 根据配置实例化对应的后端适配器

#### AI 适配器抽象层

```
┌─────────────────────────────────────┐
│         AIAdapter (抽象基类)         │
│  - render_prompt()                  │
│  - run_json_task()                  │
└─────────────┬───────────────────────┘
              │
     ┌────────┴────────┐
     ▼                 ▼
┌──────────┐     ┌──────────┐
│CodexAdapter│   │KimiAdapter│
└──────────┘     └──────────┘
```

- **`AIAdapter`**：抽象基类，定义统一的 `render_prompt()` 和 `run_json_task()` 接口
- **`CodexAdapter`**：封装 `codex exec` 命令行调用，使用 `--output-schema` 约束输出格式
- **`KimiAdapter`**：封装 `kimi chat` 命令行调用，通过 prompt 增强实现 JSON 输出约束

**多后端支持**：通过 `--ai-backend` 参数切换后端（`codex` 或 `kimi`），通过 `--kimi-model` 选择 Kimi 模型。

#### 工作区管理

- 管理工作区目录结构
- 提供统一的文件读写接口（JSON、Text）
- 自动创建编号目录（`000001`, `000002`...）

#### 约束检查器

- 硬约束：字符串匹配检查禁用语法（STL、递归、lambda 等）
- 软约束：由人性化处理评估"是否太像专业代码"

### 3.2 外部工具集成

| 工具 | 集成方式 | 用途 |
|------|----------|------|
| `g++` | 子进程调用 | C++ 编译（UTF-8 输入 → GBK 输出，适配 Windows 控制台） |
| `demo.exe` | 子进程调用（stdin 输入） | 生成标准答案 |
| `txt_compare.exe` | 子进程调用 | 输出比对 |
| `get_input_data.exe` | 子进程调用 | 读取分组测试数据 |
| `codex` | 子进程调用 | AI 代码生成 |

---

## 4. 数据流

### 4.1 单次运行流程

```
1. 创建工作区 workspaces/{seq}/
   │
2. 题目摄入阶段
   ├── 复制输入文件到 input/
   ├── 提取 PDF 文本 → extracted/problem_context.md
   └── 生成约束提示 → extracted/constraint_hints.json
   │
3. 构建测试集
   ├── 调用 get_input_data.exe 读取给定数据
   ├── 本地解析回退（若工具不可用）
   ├── 调用 Codex 生成补充测试用例
   └── 合并 → testcases/merged_cases.json
   │
4. Demo 观察（用于输出格式推断）
   ├── 选取代表性测试用例
   ├── 运行 demo.exe 捕获输出
   └── 保存 → testcases/demo_observations.json
   │
5. 解题循环（最多 max_attempts 轮）
   │
   ├── 5.1 求解器生成代码
   │       └── candidates/v{attempt}/*.cpp
   │
   ├── 5.2 编译
   │       └── outputs/v{attempt}/candidate.exe
   │
   ├── 5.3 评测
   │       ├── 对每个测试用例：
   │       │   ├── 运行 demo.exe → expected.txt
   │       │   ├── 运行 candidate → actual.txt
   │       │   └── txt_compare 比对
   │       └── 生成 outputs/v{attempt}/evaluation_summary.json
   │
   ├── 5.4 约束检查
   │       └── outputs/v{attempt}/constraint_report.json
   │
   └── 5.5 判断是否通过
       ├── 通过 → 进入人性化处理
       └── 失败 → 构建反馈 → 下一轮求解器
   │
6. 风格降级（人性化处理）
   ├── 输入：最佳候选代码 + 风格警告
   ├── 调用 Codex 改写
   ├── 输出：candidates/v{attempt+100}/*.cpp
   └── 重新全量评测验证正确性
   │
7. 发布最终产物
   └── final/
       ├── *.cpp（最终代码）
       └── final_manifest.json
```

### 4.2 反馈构建策略

评测失败时，`_build_feedback()` 生成结构化提示：

```python
feedback_items = [
    "Case 3-b13-01 failed: output mismatch.",
    "Compare hint: 第[3]行不同.",
    "Expected preview: 42 | 0 | 1",
    "Actual preview: 42 | 1 | 0",
    "Hard constraint violation: Found 'vector' usage.",
]
```

这些摘要会被传递给下一轮求解器，而非原始日志全文。

---

## 5. 工作区目录结构

```
workspaces/000001/
├── input/                          # 原始输入文件副本
│   ├── problem.pdf
│   ├── demo.exe
│   └── hw_data.txt
│
├── extracted/                      # 题目解析产物
│   ├── problem_context.md          # 题目描述 + 提取说明
│   ├── problem_text.txt            # 纯文本提取（如果有）
│   └── constraint_hints.json       # 约束提示
│
├── testcases/                      # 测试数据
│   ├── provided_cases.json         # 给定测试用例
│   ├── generated_cases.json        # AI 生成测试用例
│   ├── merged_cases.json           # 合并后的测试集
│   ├── provided_cases_selection.json  # 用例选择记录
│   └── demo_observations.json      # Demo 运行观察
│
├── candidates/                     # 候选代码
│   ├── v1/                         # 第 1 轮求解器输出
│   │   ├── main.cpp
│   │   └── solver_notes.json
│   ├── v2/                         # 第 2 轮（若失败重试）
│   └── v101/                       # 人性化处理输出
│
├── outputs/                        # 评测结果
│   └── v1/
│       ├── candidate.exe           # 编译产物
│       ├── compile_result.json     # 编译日志
│       ├── evaluation_summary.json # 评测摘要
│       ├── constraint_report.json  # 约束检查报告
│       └── cases/                  # 逐用例详情
│           ├── 001_3_b13_01/
│           │   ├── input.txt
│           │   ├── expected.txt    # demo 输出
│           │   ├── actual.txt      # candidate 输出
│           │   ├── compare_result.json
│           │   ├── demo_stderr.txt
│           │   └── candidate_stderr.txt
│           └── ...
│
├── logs/                           # 运行日志
│
├── final/                          # 最终输出
│   ├── main.cpp
│   └── final_manifest.json
│
└── run_manifest.json               # 本次运行配置
```

---

## 6. 关键设计决策

### 6.1 为什么不用真正的多 Agent 架构？

原始需求提到 4 个 Agent（解题、造数据、校验、风格调整），但实际实现采用**编排器 + 子任务**模式：

| 方案 | 优点 | 缺点 | 本项目的取舍 |
|------|------|------|-------------|
| 自由协作多 Agent | 理论上更灵活 | 调试困难、成本高、上下文污染、难复现 | ❌ 放弃 |
| 编排器 + 文件接口 | 简单、可复现、易调试、易替换 Agent | 需要预定义文件格式 | ✅ 采用 |

### 6.2 为什么固定使用 Codex？

MVP 阶段聚焦流程跑通，而非多后端适配。Codex CLI 提供：
- 结构化的 JSON Schema 输出
- 相对稳定的代码生成质量

未来可通过 `CodexAdapter` 的抽象层扩展其他 CLI Agent。

### 6.3 为什么需要 Demo 观察阶段？

很多课程作业题目的输出格式有特定要求（如空格、换行、提示语）。直接让 AI 猜测格式容易出错。通过实际运行 `demo.exe` 观察：
- 输入 X 对应输出 Y 的真实样本
- 返回码行为
- stderr 输出

求解器 Prompt 会包含这些观察，显著提升首次通过率。

### 6.4 编码处理策略

Windows 控制台默认使用 GBK，而现代工具通常使用 UTF-8。项目采用：
- 源代码文件：UTF-8
- 编译时：`-finput-charset=UTF-8 -fexec-charset=GBK`
- 运行时 IO：按系统默认编码处理

这样确保中文输出在 Windows 控制台正确显示。

### 6.5 评测比对策略

使用 `txt_compare.exe` 进行宽松比对：
- `--trim right`：忽略行尾空格
- `--ignore_blank`：忽略空行

这符合课程作业评测的一般惯例，避免因格式细节误判。

---

## 7. 扩展点

### 7.1 支持更多 AI 后端

AI 适配器架构已支持多后端扩展。如需添加新的 AI 后端：

1. 创建新的适配器类继承 `AIAdapter`：
   ```python
   # src/auto_fuck_sj/new_adapter.py
   from .ai_adapter import AIAdapter
   
   class NewAdapter(AIAdapter):
       def render_prompt(self, prompt_name: str, **values: str) -> str:
           # 实现 prompt 渲染
           pass
       
       def run_json_task(self, *, task_name, prompt, schema, workdir, sandbox="read-only") -> dict:
           # 实现 JSON 任务执行
           pass
   ```

2. 在 `orchestrator.py` 的 `_create_ai_adapter()` 中添加后端选择逻辑

3. 在 `cli.py` 中添加新的 `--ai-backend` 选项

已支持的后端：
- **Codex**（默认）：OpenAI Codex CLI，使用 `--output-schema` 约束输出
- **Kimi**：Moonshot Kimi CLI，使用 prompt 增强实现 JSON 约束

### 7.2 并行评测

当前评测是顺序执行，可改为：
- 多进程并行运行测试用例
- 多候选版本并行评测（竞速生成多个解法，择优提交）

### 7.3 更智能的约束推断

当前硬约束基于字符串匹配，可扩展：
- AST 级分析（调用 libclang）
- 从 PDF 自动提取约束（NLP）

### 7.4 题型特化

针对不同题型（字符串处理、数组操作、递归题等）提供不同的：
- 求解器 Prompt 模板
- 测试数据生成策略
- 约束检查规则

---

## 8. 限制与已知问题

1. **PDF 提取**：依赖外部工具（pdftotext/mutool），复杂排版提取效果有限
2. **多文件题目**：需要手动指定 `--cpp-name`，无法自动推断文件结构
3. **子问题处理**：如 `5-b16` 的 `--sub1`/`--sub2` 需要人工指定参数
4. **人性化处理风险**：风格降级可能引入隐性 bug，虽已做回归验证但仍非 100% 安全
5. **Kimi CLI 集成**：
   - 没有原生的 `--output-schema` 参数，JSON 输出依赖 prompt 约束
   - Windows 下存在编码问题：生成的代码中的中文字符可能出现乱码
   - 需要通过 `--quiet` 模式运行避免交互式输出
   - 工作目录需要设置为项目根目录以便找到配置

---

## 9. 总结

auto_fuck_sj 是一个**务实的工程化方案**：用简单的编排器架构 + 文件接口，串联起 AI 代码生成和 Windows 本地工具链。它没有追求复杂的多 Agent 理论模型，而是以"最快跑通、最易调试"为首要目标，在实际课程作业场景中达到了可用的自动化水平。

**核心设计哲学**：_files over APIs, orchestration over collaboration, pragmatism over elegance_.
