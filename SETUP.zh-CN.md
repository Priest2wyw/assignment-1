# Assignment 1：本机环境与开始作业指南

准备日期：2026-11-10。项目目录：`/home/youwei/github/assignment-1`。

**现在可以阅读题目、编写 TODO、运行本地测试。** 本机环境已安装并验证，已有 Modal 登录有效；运行真实 Agent 前还需要在 `.env` 填写模型服务地址和 API Key。云端沙箱集成测试尚未运行。

## 1. 每次开始作业

在 Bash 终端执行：

```bash
cd /home/youwei/github/assignment-1
source scripts/local/activate.sh
python --version
which python
```

预期 Python 为 `3.11.18`，解释器路径以 `assignment-1/.venv/bin/python` 结尾。

脚本会激活项目独立的 Conda 解释器，再激活 `.venv`，并让 uv 使用官方 PyPI 和现有锁文件。它只调整当前终端，不修改全局 Conda、uv 或 shell 配置。切换其他项目时建议新开终端，避免继承这些项目专用变量。

目录用途：

| 路径 | 用途 |
| --- | --- |
| `.local/conda-python/` | Conda 提供 Python 和基础运行库 |
| `.venv/` | 作业运行环境和 Python 依赖 |
| `.local/conda-pkgs/` | 项目专用 Conda 缓存，避开共享缓存权限问题 |
| `.env` | 模型配置，已从模板创建，权限为 `600`，被 Git 忽略 |
| `artifacts/local-setup/` | 安装日志、测试基线、版本快照；被本地 Git 排除 |
| `scripts/local/check.sh` | 一键运行本地检查并保存带时间戳的日志 |

## 2. 补齐模型配置

用编辑器打开项目根目录 `.env`，将下面两项占位符替换为课程或服务商提供的真实值：

```dotenv
OPENAI_BASE_URL=https://你的服务地址/v1
OPENAI_API_KEY=你的密钥
OPENAI_MODEL=deepseek/deepseek-v4-flash-0731
OPENAI_MAX_RETRIES=5
```

`OPENAI_BASE_URL` 应是服务商明确提供的 OpenAI 兼容 HTTPS 地址；是否包含 `/v1` 以服务商说明为准。默认模型名来自当前上游作业，需确认你的服务支持它。不要把密钥粘贴进聊天、截图、Git 或作业提交文件。

然后运行：

```bash
make doctor
```

此命令检查源码、凭据配置和模型 `/models` 接口，不创建沙箱，也不生成模型回答。它通过后，仍需通过真实运行验证模型名、工具调用能力和账户额度；`doctor` 本身不验证这些。

**Modal 已有配置且通过在线认证查询**，无需重复登录。若以后凭据过期，可在本机终端重新执行：

```bash
uv run modal setup
```

按终端显示的链接在浏览器登录；课程额度是否到账需要自行查看 Modal 控制台。本次未变更现有 Modal 配置。

## 3. 环境验证结果

| 检查 | 2026-11-10 实测结果 |
| --- | --- |
| 官方 `make setup` | 通过 |
| `make verify-sources` | 通过：子模块提交和工作区符合题目要求 |
| `uv pip check --python .venv/bin/python` | 通过：依赖兼容 |
| 基础测试 `test_smoke.py`、`test_infrastructure.py` | 3 passed |
| 五个 `assignment-*` 命令的 `--help` | 全部成功 |
| `uv run modal profile list --json` | 成功，现有活动 workspace 认证有效 |
| `make doctor` | 未通过：缺少真实 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY` |
| 官方 `make test` | 4 passed、11 failed、4 deselected |
| Modal 沙箱集成测试 | 未运行 |

**11 项失败是 starter 的作业基线，不是安装失败。** 10 项触发了待实现方法中的 `NotImplementedError`，另 1 项来自尚未定义的 `PLAY_MOVE_TOOL` schema。4 项被排除的测试需要真实 Modal 沙箱；默认 `make test` 不运行它们。

可随时重新检查：

```bash
bash scripts/local/check.sh
```

脚本会显示 Doctor 和作业测试各自的退出码。有缺失配置或未完成 TODO 时脚本返回非零，这是预期行为，详细原因见日志。官方 `make test` 的测试失败经 Make 转换后退出码为 `2`。

首次验证日志位于 `artifacts/local-setup/check-20261110-194134/`。其他留档：

- `make-setup.log`、`conda-create.log`：安装过程。
- `doctor.log`、`modal-auth.log`、`cli-help.log`：配置、认证和命令入口检查。
- `environment.json`：解释器、依赖版本、提交号、SWE-bench 镜像名和测试基线。
- `python-packages.txt`、`conda-explicit.txt`、`uv-lock.sha256`：环境复现资料。

## 4. 开始做作业的顺序

先读根目录 [`ASSIGNMENT.md`](ASSIGNMENT.md)。本次保留了全部作业 TODO，未修改 `src/`、`tests/`、`tasks/` 或 `chess_app/`。

| 阶段 | 阅读/实现位置 | 检查方式 |
| --- | --- | --- |
| Part 1：ReAct、coding tools、skills | `src/assignment/agent/base.py`、`code_agent.py`、`tools.py` | 本地 `make test`，实现后再运行 CodeAgent |
| Part 2：上下文压缩 | `base.py`，题目 Part 2 | 本地测试，之后运行 Django SWE-bench 实例 |
| Part 3：棋局工具和编程式调用 | `chess_agent.py`、`chess_tools.py`、`tools.py` | 本地测试，之后运行 ChessAgent |

本地测试可以不填 API Key 先做：

```bash
make test
uv run pytest tests/test_agent.py -q
uv run pytest tests/test_chess_agent.py -q
```

完成对应 TODO、确认 `make doctor` 通过并核对账户额度后，再按题目运行下列命令。它们会使用 Modal 和/或模型服务额度：

```bash
# 可选：先验证沙箱基础设施（不需要完成 Agent TODO）
make test-modal
# test-modal 已包含棋局沙箱测试；单独重试它可用 make test-chess-modal

# Part 1：让 CodeAgent 生成补丁，然后评分
make run-code-agent
make check-part1

# Part 2：保留不同文件名，避免覆盖 baseline 与压缩实验结果
COMPACT_THRESHOLD=0 \
SWEBENCH_PATCH=artifacts/django-baseline.patch \
SWEBENCH_TRAJECTORY=artifacts/django-baseline-trajectory.json \
make run-swebench-agent INSTANCE=django__django-15368

COMPACT_THRESHOLD=6000 \
SWEBENCH_PATCH=artifacts/django__django-15368.patch \
SWEBENCH_TRAJECTORY=artifacts/django__django-15368-trajectory.json \
make run-swebench-agent INSTANCE=django__django-15368
make check-swebench INSTANCE=django__django-15368

# Part 3：使用 Part 1 生成的 artifacts/fix.patch
make run-chess-agent
```

其余棋局 observation A/B、`simulate_move`、programmatic tools 实验，继续按 `ASSIGNMENT.md` 操作。Makefile 默认使用题目模型名；更换服务商时可显式传入 `MODEL=你的模型名`，仅修改 `.env` 不会覆盖 Makefile 的默认 `MODEL`。

## 5. 下载内容与运行位置

- 仓库提交：`67498d87e36f7b45a2a4ce82d65d1139fb6a51c0`。
- 唯一 Git 子模块 `chess_app`：`4aaabca1194ef5f175ccae4fecf902bc71cc303b`。以上数量以当前 `.gitmodules` 和 Makefile 为准；上游说明中的 “either pinned source” 是残留表述。
- Django SWE-bench 的问题描述、测试补丁和实例配置已随仓库下载，无需额外下载整个数据集。
- Python 依赖按上游 `uv.lock` 安装，锁文件未修改。核心版本：Modal `1.5.3`、OpenAI SDK `2.54.0`、SWE-ReX `1.4.0`、pytest `9.1.1`。
- 模型通过 API 调用；没有下载大模型权重，也不需要占用本机 GPU。
- 沙箱和 SWE-bench 镜像在 Modal 云端首次运行时构建/拉取；本机 Docker 不参与官方流程，未安装 Kubernetes。当前尚未预构建云端镜像。

## 6. 安装中遇到的问题与复现

GitHub 默认 DNS 返回的节点 `20.205.243.166` 连接超时；`140.82.112.3` 当时可连。本机 Git `2.34.1` 不支持 `http.curloptResolve`，因此下载时临时启动了仅监听 localhost、仅允许 `github.com:443` 的 CONNECT 转发，连接可用节点。Git 继续校验证书。下载结束后转发已停止，未修改系统 DNS、hosts、Git 全局配置，也未保存永久代理。

完整下载辅助脚本留档于 `artifacts/local-setup/download-via-github-node.py`，它仅用于在**目标目录不存在**时克隆；不要对现有作业目录重复运行。固定 IP 只是当次网络诊断结果，未来失效时应重新排查网络。

若未来需要在本机重建 Python 环境（已有目录时先自行备份，不要直接覆盖作业文件）：

```bash
cd /home/youwei/github/assignment-1
CONDA_PKGS_DIRS="$PWD/.local/conda-pkgs" \
  /home/youwei/anaconda3/bin/conda create \
  --prefix "$PWD/.local/conda-python" python=3.11 pip -y
.local/conda-python/bin/python -m venv .venv
source scripts/local/activate.sh
make setup
```

此次使用项目专用 Conda 缓存，避免此前共享缓存中 root 所有文件导致的权限问题。uv 使用官方 PyPI，是为了与上游锁文件一致并绕开本机全局镜像配置。

[`AI_USAGE.md`](AI_USAGE.md) 已记录本次 AI 仅协助环境准备；之后如继续使用 AI 做作业，请按课程要求更新该文件。提交时按题目指定清单打包，不要打包整个工作目录和本机环境。
