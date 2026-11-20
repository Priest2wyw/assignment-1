# 象棋实验的模型服务配置

默认运行仍使用 `.env` 中的 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY`。
Make 的 `MODEL` 或 CLI 的 `--model` 优先于环境变量中的模型名。

GPT-OSS 的两组实验使用独立配置：

```dotenv
GPT_OSS_URL=https://openrouter.ai/api/v1
GPT_OSS_NAME=openai/gpt-oss-120b
GPT_OSS_KEY=你的OpenRouter密钥
```

填写在本地 `.env` 后，直接运行：

```bash
make run-obs-gpt-oss-no-legal
make run-obs-gpt-oss-legal
```

两个目标分别保存 `artifacts/part3-no-legal-moves-gpt-oss.json` 和
`artifacts/part3-legal-moves-gpt-oss.json`，正常结束时还会保存对应的
`-result.json`。缺少配置时会在启动 Modal 沙箱之前退出，不会回退到
DeepSeek 的地址或密钥。密钥本身不会出现在 Make 命令中。

CLI 也支持直接覆盖 URL，并通过变量名选择密钥：

```bash
uv run assignment-play-chess \
  --model openai/gpt-oss-120b \
  --base-url https://openrouter.ai/api/v1 \
  --api-key-env GPT_OSS_KEY \
  --patch artifacts/fix.patch \
  --trajectory artifacts/part3-legal-moves-gpt-oss.json \
  --result artifacts/part3-legal-moves-gpt-oss-result.json
```

`--base-url-env`（默认 `OPENAI_BASE_URL`）、`--model-env`（默认
`OPENAI_MODEL`）也可以选择其他配置变量。显式的 `--base-url` 和
`--model` 优先于对应环境变量。密钥仅支持环境变量选择，避免将它写入
进程参数或 shell 历史。

Make 可用 `CHESS_BASE_URL=...` 覆盖 URL；可用 `GPT_OSS_MODEL=...`
覆盖 GPT-OSS 的模型 ID。普通象棋运行的配置变量是
`CHESS_BASE_URL_ENV`、`CHESS_API_KEY_ENV`、`CHESS_MODEL_ENV`。
GPT-OSS 专用目标将它们设为 `GPT_OSS_URL`、`GPT_OSS_KEY`、`GPT_OSS_NAME`。

2026-11-18 的真实连通性检查成功，模型 `openai/gpt-oss-120b` 返回
`play_move({"move":"e2e4"})`，输入 192 token、输出 150 token，耗时
3.89 秒。该检查没有执行实际棋局，不替代四组完整实验。
