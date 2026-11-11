# 作业 1：构建智能体运行框架（Agent Harness）

智能体运行框架（agent harness）提供一套接口，让语言模型（生成具有一定概率的字符串的模型）能够观察环境并在其中采取行动。[ReAct](https://arxiv.org/abs/2210.03629) 是构建智能体运行框架最常用的框架之一，它在语言模型的提示词中交错组织环境观察、推理／思维链和智能体行动所对应的文本。本次作业中，你将基于 ReAct 框架构建一个智能体运行框架。

在第 1 部分，你将实现基类 [`Agent`](./src/assignment/agent/base.py) 的 ReAct 循环，并通过其子类 [`CodeAgent`](./src/assignment/agent/code_agent.py) 创建一个在终端中操作、解决软件问题的智能体。你的 ReAct 循环将具有抽象性，能够应用于多个领域，帮助你理解智能体运行框架的一般结构。你将实现让编程智能体观察终端环境并在其中采取行动的机制，还将应用可复用的智能体技能来解决任务。随后，你将让这个编程智能体修复一个国际象棋应用中的问题。

在第 2 部分，你将研究编程智能体在解决更复杂的软件问题时如何使用上下文。你将实现一种简单的上下文压缩方法，管理智能体对语言模型上下文窗口的使用量。

在第 3 部分，你将使用已经构建的 `Agent` 基类，通过 `ChessAgent` 子类创建国际象棋智能体，在由 `CodeAgent` 修复的应用中下棋。你将实现该智能体的工具规格，让语言模型能够在应用中与一个基于规则的机器人对弈（你可以观战！）。你还将探索程序化工具调用，把程序的能力引入智能体行动，让智能体通过执行 Python 代码来实施更复杂的策略。

这三个部分的关系如下：

```text
                SWE-Bench 问题
                      |
                      v
有缺陷的象棋应用 -> CodeAgent -> fix.patch -> 修复后的象棋服务器
                                              ^
                                              |
                                    ChessAgent 工具
```

## 环境配置

安装 [uv](https://docs.astral.sh/uv/)，然后运行：
```bash
make setup
```
这会使用 `uv` 配置 Python 环境，并下载、安装相关依赖。如果指定版本的 `chess_app` 源码（用于智能体将要处理的任务）缺失，或者其提交版本不正确，配置就会失败。

本作业将使用云端代码运行平台 [Modal](https://modal.com/)。该平台允许你在云端机器上安全地运行智能体生成的代码。智能体的运行环境位于远程 Modal 沙箱中，执行智能体行动的代码也在其中运行。首先，注册 Modal 账户（如果你还没有），然后按照后续发送给你的说明获取 Modal 计算额度。接着运行：
```bash
uv run modal setup
```
以登录并在你的环境中配置 Modal。

完成 Modal 配置后，运行：
```bash
cp .env.example .env
```
创建用于保存环境机密信息的文件，主要保存 LLM API 的相关配置。如果你已选修本课程，将收到获取 LLM 服务商额度的说明。请按照说明生成 API 密钥，并确保正确配置服务的基础 URL。

```dotenv
OPENAI_BASE_URL=<OpenAI-compatible base URL>
OPENAI_API_KEY=...
OPENAI_MODEL=deepseek/deepseek-v4-flash-0731
OPENAI_MAX_RETRIES=5
```
如上所示，默认使用 DeepSeek-V4-Flash 模型。在作业明确要求时，应使用其他模型。如果额度允许，你也可以探索同一服务商提供的其他模型，但本作业预期使用该模型即可完成。

我们将任何消耗 API 额度的活动（来自 Modal 或 LLM 服务商）称为*计费活动*。在完成作业的过程中，你将运行多次计费评估。建议通过相关控制面板监控用量，合理使用 API 额度。

在进行计费运行之前，先检查子模块、Modal 身份验证以及模型端点；此检查不会启动沙箱或生成 token：
```bash
make doctor
```

*（可选）*如果你想测试所有 Modal 组件是否正常运行，可以执行：
```bash
make test-modal
make test-chess-modal
```

一个通用建议是，可以使用：
```bash
modal container list
```
检查是否有正在运行的计费 Modal 沙箱。如果环境未能正常关闭，沙箱可能仍在运行并持续消耗额度。可以使用 `modal container stop <container ID>` 停止未正常终止的沙箱。

## 公开测试

`make test` 运行速度快、完全离线且不产生费用。初始代码中，学生需要完成的 TODO 对应测试会故意失败。请将这些阶段性目标作为参考；如果后续增加用于澄清要求的测试，pytest 的具体测试数量可能发生变化。

通过公开测试并不能证明实现完全正确。私有测试还会覆盖失败时的清理、重复或格式错误的技能、并行象棋调用、传输错误、产物一致性、补丁重放，以及真实的 Modal 集成。

## 规则

- 不要修改 `tests/`、`tasks/`、`chess_app/`。
- 不要更改已提供的日志记录／清理逻辑，也不要在子类中重复实现共享的 ReAct 循环。
- 不要为了通过测试而将智能体任务的预期解法硬编码。智能体应自行生成给定任务所需的走法或补丁。
- **绝不要泄露、记录到日志或提交 API 密钥等凭据。** 请谨慎处理 `.env` 文件中的内容。
- 在本作业中，你将使用多个智能体以及这些智能体的多个版本。任何时候，都只能使用为当前智能体指定的工具集。

## 第 1 部分：构建编程智能体并修复象棋应用

共享的 `Agent` 必须实现常规的 ReAct 循环：构建请求，获取助手行动，执行其工具调用，添加与调用关联的观察结果，并重复这一过程直至完成。

### 1. 构建提示词

语言模型的提示词是一系列消息，在交互的每一步都用于查询语言模型。消息是一个字典对象，至少包含 `role` 和 `content` 键，也可以包含其他信息。消息的 `content` 可以是字符串，也可以是包含推理 token 的结构化对象，或者图像（本作业不涉及）。消息的 `role` 可以取以下几种值。

`system` 角色用于提供长期有效的指令，例如领域说明、环境信息、必须遵守的规则，以及可能适用于多个任务的通用策略等。`user` 角色提供任务信息[^1]，必要时还包含解决任务的附加指导。`assistant` 角色消息表示 LLM 生成的内容，`tool` 角色消息表示工具调用的结果，即对环境的观察。你的任务是组织这些消息的序列。按照惯例，最前面恰好有一条 `system` 消息，随后在任何助手消息之前有一条 `user` 消息。由于 LLM 每次生成一个响应，`assistant` 消息后应跟随展示工具调用结果的 `tool` 消息，或一条 `user` 消息。有关这些消息结构的信息，请参阅 [OpenAI API 参考文档](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create)，以及 vLLM 文档中的这个[示例](https://docs.vllm.ai/en/v0.7.2/getting_started/examples/openai_chat_completion_client_with_tools.html)。

你需要实现 `Agent.build_prompt` 方法。根据智能体类属性中的系统提示词和任务提示词，以及你可能添加的其他状态记录，此方法应准备好语言模型的输入。我们已经提供 `Agent.query_language_model` 方法，它会直接使用此方法的输出来查询语言模型 API。你的实现需要为该查询提供正确的输入。`Agent.query_language_model` 会向语言模型 API 提供工具和推理参数，并返回包含所有相关信息的结构。它还维护步数，即 API 被查询的次数。API 会将提示词和工具渲染为一个 token 序列，你无需处理这一过程。该方法还包含记录请求以供评分的机制，请不要修改。

智能体的 LLM 客户端在服务商出现临时故障时，最多重试 `OPENAI_MAX_RETRIES` 次。

> **TODO(1.1.a)**
> 添加状态维护机制，记录智能体采取的行动及其观察到的结果。构建组成语言模型提示词的消息序列，其中应包含长期有效的指令、任务规格，以及之前各轮交互中的观察、推理和行动。注意，此方法应与具体领域无关，其构建提示词的方式应适用于任何继承它的领域专用智能体。

接下来，为 `CodeAgent` 构建系统提示词和任务提示词。系统消息**必须**原样包含以下区块，其中的值使用环境提供的信息：
```text
<system_information>
{
  "machine": <machine>,
  "release": <release>,
  "system": <system>,
  "version": <version>
}
</system_information>
```

> **TODO(1.1.b)**
> 为 `CodeAgent` 构建系统提示词和 `task_prompt`。它们应能够供 `Agent.build_prompt` 方法使用。

### 2. 运行 ReAct 循环

实现 `Agent.run` 的方法体。

> **TODO(1.2)**
> 运行 ReAct 循环。协调以下过程：提示语言模型生成推理和行动，提取模型生成的工具调用，并执行这些调用，为下一步获取智能体的观察结果。确保识别智能体何时完成任务，并设置 `Agent.finished`。如果智能体超过 `step_limit`，抛出 `StepLimitError`。

### 3. 执行编程工具

实现 `CodeAgent.execute_tool_calls`。编程智能体支持两个工具：`execute` 和 `send_message`。你可以在[这里](./src/assignment/agent/tools.py)找到它们的定义。你需要实现执行这些工具的机制，并准备好用于展示给语言模型的输出。这些输出也是消息，格式为 `{"role": str, "tool_call_id": str, "content": str}`。每条消息都是执行一个工具后得到的观察结果，使用名为 `tool` 的特殊角色。[^2] 你应使用 `Environment.execute` 方法，确保在正确的 Modal 沙箱中执行代码。可选参数可以保留当前默认值，但应允许智能体在工具调用中覆盖这些参数。

> **TODO(1.3)**
> 让智能体能够使用 `execute` 和 `send_message` 工具。解析每个调用，执行已识别的工具，并为每个调用返回一条消息（智能体的一次响应中可能包含多个工具调用！）。格式错误的 JSON 和未知工具必须转化为可供智能体恢复处理的观察结果，而不是抛出异常。

### 4. 加载技能

你可能觉得现在已经可以让智能体处理软件问题了，但还差一步！`CodeAgent` 最后还需要知道如何提交解答。我们采用的具体协议是：智能体解决问题后，将解答保存到名为 `patch.txt` 的文件中。这个文件将从环境中提取出来用于评估。

我们将使用一个技能来教会智能体这一协议。技能通过专门且可复用的工作流扩展智能体能力。[Agent Skills 协议](https://agentskills.io/home)定义了技能应遵循的标准，以便多个智能体框架都能支持这些技能。`tasks/code-skills/submit-task` 按照这一协议定义了一个用于提交解答的基础技能。该协议还有一些可供探索的高级特性，但本作业只使用一个最小化的技能。

你需要实现的核心特性是*渐进式披露（progressive disclosure）*。为了让智能体能够使用大量技能（其中每个技能都可能很复杂），技能信息会按照逐步增加的详细程度向智能体展示，由智能体按需获取。本作业要求实现一种简单的渐进式披露：在**系统提示词中**向智能体提供所有可用技能的描述，同时提供 `invoke_skill` 工具，允许智能体通过技能名称查看完整技能。因此，当智能体查看完整的 `submit-task` 技能时，就会知道如何提交修复以供评分。我们会检查系统提示词是否提及技能名称和描述。如果智能体没有可用技能，则提示词的任何部分都不应提及 `patch.txt`，也不应提供提交说明。

技能文件位于[本地](./tasks/code-skills/)。当智能体运行且使用技能时，`Agent.skills_path` 会指向该位置；否则设为 `None`。注意，本作业中的智能体只会使用一个技能，即 `./tasks/code-skills/` 下的一个子文件夹。但原则上，智能体可能使用许多技能，这也使渐进式披露更加重要和实用。

> **TODO(1.4)**
> 验证 `skills_path`，在每个子目录中发现一个 `SKILL.md`，解析其 YAML frontmatter（文件开头两个 `---` 标记之间的内容），并返回以前置信息中的 `name` 为键的映射。每个值必须包含一个简洁的 `metadata` 字符串，用于模型的技能目录，以及技能文件的完整 `content`，供 `invoke_skill` 使用。对于重复名称以及格式错误或缺失的 frontmatter，应抛出清晰的 `ValueError`。如果智能体有可用技能，则在提示词中提供这些技能的描述／元数据。

例如，`SKILL.md` 的 `content` 为：
```
---
name: hello-world
description: Write "hello, world" to the terminal
---

echo "hello, world"
```
对应的 `metadata` 为：
```
name: hello-world
description: Write "hello, world" to the terminal
```

### 5. 运行并检查修复

现在，让智能体修复一个软件问题。

```bash
make run-code-agent
make check-part1
```

默认模型为 `deepseek/deepseek-v4-flash-0731`。智能体接收 `tasks/chess-terminal-move/problem_statement.md`，在 `/testbed` 中工作，并且必须复现、修复和验证该故障。一次运行会生成：

- `artifacts/fix.patch`
- `artifacts/part1-trajectory.json`

`make check-part1` 会将生成的补丁应用到一个全新的测试环境，并运行公开回归测试及象棋应用的测试套件。不要直接编辑 `chess_app/` 中的目标代码。

完成第 1 部分后，你的解答应通过与提示词构建、截断、步数限制、格式错误／未知工具以及补丁提交有关的测试。

## 第 2 部分：实现上下文压缩

过长的 ReAct 交互记录会增加成本，并最终挤占有用上下文的空间。随着智能体执行越来越复杂、耗时越来越长的任务，也会最终触及语言模型上下文窗口的上限。为了让智能体高效处理运行时间更长的任务，我们希望只保留与先前行动和观察相关的信息。实现方式是将上下文压缩为工作记忆。现在，你将在共享的 `Agent` 中实现由模型生成的工作记忆；不要使用服务商专有的上下文压缩端点。

> **TODO(2.1)**
> 实现 `Agent.compact_context`。提示模型压缩上下文。用于压缩的系统提示词应要求生成简洁、基于事实的工作记忆，并保留目标、约束、文件、命令、编辑、具体结果、失败的尝试、测试、阻碍因素以及下一步行动。只总结较早的一段前缀；原始系统／任务消息必须原样保留，并且至少保留最近一次完整的助手行动及其所有关联工具观察。生成的摘要应改变 `build_prompt` 的输出，并缩短提示词长度。

**不要**修改智能体类的 `api_prompt` 和 `api_responses` 属性。它们用于记录和评估。

> **TODO(2.2)**
> 在共享循环中，每次发起新的行动请求之前调用 `maybe_compact_context()`。它已经实现了当前有效上下文 token 数的估算、阈值处理，以及用于日志记录的压缩事件跟踪。

以 6,000 token 为阈值，运行仓库中附带的 `django__django-15368` 任务：

```bash
COMPACT_THRESHOLD=6000 \
SWEBENCH_PATCH=artifacts/django__django-15368.patch \
SWEBENCH_TRAJECTORY=artifacts/django__django-15368-trajectory.json \
make run-swebench-agent INSTANCE=django__django-15368
make check-swebench INSTANCE=django__django-15368
```

将 `COMPACT_THRESHOLD=0`，即可省略压缩标志，运行保留完整上下文的基线实验。如果要保留两次运行结果，请使用不同的输出文件名，例如：

```bash
COMPACT_THRESHOLD=0 \
SWEBENCH_PATCH=artifacts/django__django-15368-baseline.patch \
SWEBENCH_TRAJECTORY=artifacts/django__django-15368-baseline-trajectory.json \
make run-swebench-agent INSTANCE=django__django-15368
```

提交的压缩运行必须至少触发一次压缩，显著减少当前有效上下文，并生成能够通过 `check-swebench` 的补丁。生成过程具有随机性，因此它不必比每一次基线运行都使用更少的 ReAct 步数。

生成使用压缩和不使用压缩的两份运行轨迹后，比较它们的 token 用量。在 `artifacts/token-usage-analysis.md` 中呈现观察结果，并简要解释你看到的趋势。使用压缩与不使用压缩时，上下文使用方面存在哪些权衡？

## 第 3 部分：构建 `ChessAgent`

你的智能体已经在第 1 部分修复了象棋应用中的问题，现在可以构建一个下棋的智能体。`ChessAgent` 完整复用第 1、2 部分的同一个循环。它执白棋，服务器的确定性机器人执黑棋。每次白棋合法落子后，服务器会自动走出黑棋的应手。

### 1. 实现 `play_move`

首先定义一个新工具，让智能体能够在应用中运行的棋局里落子。请遵循 [OpenAI 函数调用指南](https://developers.openai.com/api/docs/guides/function-calling)定义工具。

> **TODO(3.1.a)**
> 定义一个名为 `play_move` 的 OpenAI 函数工具 schema。它必须恰好接受一个名为 `move` 的必需字符串参数，说明走法采用 [UCI 记法](https://en.wikipedia.org/wiki/Universal_Chess_Interface)（例如 `e2e4` 和 `e7e8q`），并拒绝额外参数。

接着，实现运行该工具的机制。[^3]

> **TODO(3.1.b)**
> 在 `chess_tools.py` 中实现 `_play_move`。解析参数，并向 `/api/move` POST `{"move": <uci move>}`。返回其序列化后的 JSON 对象。捕获工具抛出的任何错误，将错误信息放在 `<chess_error></chess_error>` 之间返回，让智能体处理。覆盖以下情况：JSON 参数格式错误、参数不是对象、`fen` 缺失或不是字符串、`move` 不是字符串、服务器拒绝局面或走法，以及传输失败。

> **译注：** 原文此处包含“`fen` 缺失或不是字符串”的要求，但前面的 `play_move` 定义只接收 `move` 参数；此处按原文保留，可能是与后文 `_simulate_move` 要求重复的笔误。

你可以查看 `chess_app` 以了解 API 的工作方式。

使用 `format_state` 方法格式化成功返回的状态，更新 `last_state`，并根据 `game_over` 设置 `finished`。使用原始的 `tool_call_id` 关联观察结果。格式错误的 JSON、未知工具、非法走法和网络错误都应转换成 `<chess_error>...</chess_error>` 观察结果。由于落子后实时局面会改变，一组并行调用中最多执行一次落子，并以可恢复的错误方式拒绝其余调用。

初始观察和成功落子后的观察已经展示棋盘、黑棋的应手以及下一步的合法走法，无需另设读取棋盘的工具。

运行：

```bash
make run-chess-agent
```

这会应用你的 `fix.patch`，启动修复后的服务器，并保存：

- `artifacts/part3-trajectory.json`
- `artifacts/game-result.json`

输出的 HTTPS URL 提供棋盘页面和 API。智能体下棋时，棋盘页面会轮询实时状态；页面按钮只刷新状态，不会重置棋局。`CHESS_TIMEOUT=1800` 控制沙箱的存活时间。

### 2. 运行观察信息 A/B 实验

为了了解工具接口对智能体行为的影响，你将针对两个模型比较“仅棋盘”的观察信息与“棋盘加合法走法”的观察信息。运行程序会配置这些选项，无需修改源码，并使用不同的文件名：

```bash
make run-obs-deepseek-no-legal
make run-obs-deepseek-legal
make run-obs-gpt-oss-no-legal
make run-obs-gpt-oss-legal
```

对这四次运行，分别记录 `play_move` 调用总数、因走法非法而被拒绝的调用数、无效走法比例，以及是否达到 `game_over: true`。在 `artifacts/observation-experiment.md` 中写一份简短的比较报告。评分依据是实验及其证据，而不是某个特定结果或是否赢得棋局。

### 3. 添加 `simulate_move`

为了让智能体能够规划更复杂的策略，你将为它提供模拟走法的能力。模拟允许智能体了解某一步棋的效果，但不会实际改变真实棋盘的状态。你将定义并注册 `SIMULATE_MOVE_TOOL`，实现 `_simulate_move`，并将其添加到现有的分发器中。

> **TODO(3.3.a)**
> 仿照 `play_move` 工具，定义 `simulate_move` 工具。

`simulate_move(fen, move=None)` 调用 `POST /api/simulate`。

仅向 `simulate_move` 传入完整的六字段 [FEN](https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation)，会返回该局面及其合法走法。传入 FEN 和 UCI 走法，会返回任意一方恰好走一步（一个半回合，ply）后的局面。返回 JSON，以便 Python 使用 `fen`、`squares`、`turn`、`legal_moves` 以及终局结果字段。

> **TODO(3.3.b)**
> 在 `chess_tools.py` 中实现 `_simulate_move`。解析参数，使用 FEN 和可选的走法调用已提供的 `/api/simulate` 端点，并返回其序列化后的 JSON。捕获工具抛出的任何错误，将错误信息放在 `<chess_error></chess_error>` 之间返回，让智能体处理。覆盖以下情况：JSON 参数格式错误、参数不是对象、`fen` 缺失或不是字符串、`move` 不是字符串、服务器拒绝局面或走法，以及传输失败。

应使用 `ChessAgent.chess_client` 发送 POST 请求。

### 4. 添加 `run_python`

有了模拟棋盘走法的能力，智能体就能够进行更复杂的规划。执行代码的能力将使智能体更可靠地实施自己的计划，你将通过程序化工具调用实现这一点。定义并注册 `RUN_PYTHON_TOOL`，实现 `_run_python`，并将其添加到分发器中。模型提供 `run_python(code)`，代码片段可以像调用普通同步 Python 函数一样调用 `simulate_move` 和 `play_move`。

> **TODO(3.4)**
> 解析参数，在沙箱中运行代码，并让代码能够通过名称访问已注册的工具。`/opt/assignment/sandbox_python.py` 是 `env` 沙箱上的一个脚本，可以访问本文件中的同一组工具定义。使用它运行模型作为 `run_python` 工具参数生成的代码。该脚本接受两个位置参数：`port` 和经过 base64 编码的代码字符串（避免引号处理问题）。实现这一工具调用。
> 脚本会打印一个 JSON 对象，其中包含代码运行的 `stdout`、`stderr` 和 `error`；将该字符串原样返回。非零返回码表示沙箱本身失败，而不是模型代码失败。将 `exception_info` 或 `stderr` 作为 `<chess_error>` 报告。
> 如果发生类型不匹配或解析失败等问题，返回 `<chess_error>{message}</chess_error>`。

模型编写的代码不得在本地智能体进程中运行。`_run_python` 应通过 `env.execute` 将 base64 编码的代码发送到已提供的沙箱执行程序：

```text
python /opt/assignment/sandbox_python.py <port> <base64-code>
```

返回执行程序的 JSON 字符串，其中包含 `stdout`、`stderr` 和 `error`。沙箱命令返回非零退出码时，应转化为 `<chess_error>`。代码片段抛出 Python 异常时，仍属于执行程序调用成功，该异常应放在其 `error` 字段中。每次代码片段执行后，重新读取实时棋盘，更新 `last_state` 和 `finished`，并将格式化后的状态附加到观察结果中；否则，模型可能重复执行代码片段已经落下的一步棋。

使用以下命令启用这些工具：

```bash
uv run assignment-play-chess --programmatic-tools
```

完成实现后，智能体应能够生成一段用于选择走法的代码，并在棋局中走出这一步。你可能仍然发现，象棋智能体未能充分利用已有工具走出好棋，而是经常直接使用 `play_move` 行动。为了赋予它更明确的结构和策略，我们再次使用前面探索过的技能。

### 5. 加载并使用象棋技能

虽然运行 Python 代码让智能体可以执行复杂计划，但智能体未必会主动这样做。为了给智能体提供可执行的具体策略，我们在 `tasks/chess-skills/select-move` 中提供了另一个技能。为了让模型使用它，你需要让 `ChessAgent` 具备 `CodeAgent` 的部分技能使用能力。由于工具执行机制略有不同，你必须在 `_invoke_skill(skills, arguments)` 中重新实现 `ChessAgent` 对 `invoke_skill` 工具的处理，仅在加载了技能时注册 `INVOKE_SKILL_TOOL`，并返回指定技能的完整内容。

> **TODO(3.5)**
> 解析参数并返回指定名称的技能内容。如果发生类型不匹配或解析失败等问题，返回 `<chess_error>{message}</chess_error>`。

```bash
uv run assignment-play-chess \
  --programmatic-tools \
  --skills-path tasks/chess-skills \
  --trajectory artifacts/part3-python-skill-trajectory.json
```

运行轨迹必须展示先调用 `invoke_skill`，然后通过 `run_python` 运行代码，在代码中调用 `simulate_move` 进行搜索，再调用一次 `play_move` 实际落子。读取技能后每轮直接调用一次 `play_move`，不能证明这些工具实现了协同工作。棋局无需结束，也无需获胜。

## 评分

本作业总分为 **100 分**。评分表中的每一行独立评分；某次具有随机性的模型运行失败，不会影响其他无关实现项的得分。

| 部分 | 评分标准 | 分值 | 证据 |
|---|---|---|---|
| 1 | 提示词构建及有效的行动／观察历史 | 6 | 私有单元测试 |
| 1 | ReAct 生命周期、纯文本响应后的恢复、步数限制、清理、运行轨迹 | 6 | 私有单元测试 |
| 1 | 编程工具分发、可恢复错误、补丁提交 | 6 | 私有单元测试 |
| 1 | 象棋补丁能够应用，并通过私有／回归测试 | 8 | 在全新测试环境中重放补丁 |
| 1 | 技能发现及 `invoke_skill` 行为 | 4 | 私有测试 |
| 2 | 压缩触发及模型生成的摘要 | 6 | 私有测试和运行轨迹 |
| 2 | 原始指令及最近完整的工具步骤保持有效 | 6 | 私有测试和运行轨迹 |
| 2 | 可审计的压缩显著减少当前有效上下文 | 4 | 压缩事件和用量 |
| 2 | 完整上下文与压缩上下文的 token 用量分析报告 | 4 | 报告 |
| 2 | SWE-bench 补丁通过 FAIL_TO_PASS 和 PASS_TO_PASS | 8 | 补丁重放 |
| 3 | `play_move` 的 schema 和注册 | 4 | 私有测试 |
| 3 | `play_move` 状态更新及可恢复错误 | 6 | 私有测试 |
| 3 | 基础象棋运行轨迹达到终局状态 | 4 | 运行轨迹和结果 |
| 3 | 完成四次运行的观察信息 A/B 实验 | 4 | 四份运行轨迹、四份结果 |
| 3 | 观察信息 A/B 实验报告 | 4 | 报告 |
| 3 | `simulate_move` 的无状态行为及错误处理 | 6 | 私有单元／集成测试 |
| 3 | `run_python` 的沙箱执行、状态刷新及错误处理 | 6 | 使用沙箱替身的私有测试 |
| 3 | 技能运行轨迹结合技能、程序化搜索及实际落子 | 6 | 运行轨迹重放 |
| — | 完整、可解析且符合规则的提交 | 2 | 压缩包验证 |
| | **总计** | **100** | |

评分程序会重放补丁和提交的运行轨迹，不会发起新的 LLM 调用。证据缺失或不一致只会影响对应评分行的得分。教师测试和参考补丁不包含在本仓库中。

## 提交

提交一个 ZIP 压缩包，包含 `src/assignment/agent/` 下你修改过的文件，以及以下产物：

```text
artifacts/fix.patch
artifacts/part1-trajectory.json
artifacts/django__django-15368.patch
artifacts/django__django-15368-trajectory.json
artifacts/token-usage-analysis.md
artifacts/part3-trajectory.json
artifacts/game-result.json
artifacts/part3-no-legal-moves-deepseek.json
artifacts/part3-no-legal-moves-deepseek-result.json
artifacts/part3-legal-moves-deepseek.json
artifacts/part3-legal-moves-deepseek-result.json
artifacts/part3-no-legal-moves-gpt-oss.json
artifacts/part3-no-legal-moves-gpt-oss-result.json
artifacts/part3-legal-moves-gpt-oss.json
artifacts/part3-legal-moves-gpt-oss-result.json
artifacts/observation-experiment.md
artifacts/part3-python-skill-trajectory.json
```

仅当你修改了 `src/assignment/prompts.py` 时，才将其一并提交。**不要**提交凭据、`.env`、任务文件、测试、子模块内容或教师文件。ZIP 中应包含 `src/` 和 `artifacts` 子文件夹，以及一个 `AI_USAGE.md` 文件。`AI_USAGE.md` 应详细说明你在本作业中对任何 AI 技术的使用情况。列出使用过的所有工具，并清楚说明如何使用每个工具。如果没有使用任何 AI 辅助，请在该文件中声明。我们不会对提交的 `AI_USAGE.md` 文件评分，但会通过一次测验检查你对所提交代码的理解（具体信息另行通知）。

[^1]: 在这类离线评估场景中，通常将任务组织为用户请求来指定任务。更多示例请参阅这些[文档](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/chatgpt?tabs=python-key%2Cdotnet-secure%2Cjavascript-secure&pivots=programming-language-python)。

[^2]: 服务商返回重复的 `call_0` ID 是有效的：应将每条工具观察与同一次助手行动中的调用匹配，不要假设 ID 在整个运行轨迹中全局唯一。

[^3]: `_play_move` 和其他工具被单独放在 `chess_tools.py` 中，以便能够在远程沙箱中执行这些工具。请遵循现有代码结构，正确使用 Modal 沙箱执行象棋走法。
