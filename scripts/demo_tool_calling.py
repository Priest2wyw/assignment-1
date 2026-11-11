"""演示 Chat Completions 工具调用；execute 使用模拟结果，不执行命令。

运行：.venv/bin/python scripts/demo_tool_calling.py
离线：.venv/bin/python scripts/demo_tool_calling.py --offline
"""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletion

from assignment.agent.tools import EXECUTE_TOOL, SEND_MESSAGE_TOOL


def show(title, value):
    print(f"\n--- {title} ---")
    print(json.dumps(value, ensure_ascii=False, indent=2))


def offline_response(message):
    """构造与 SDK 返回值同类型的示例响应，不访问网络。"""
    return ChatCompletion.model_validate({
        "id": "chatcmpl-offline-demo",
        "object": "chat.completion",
        "created": 0,
        "model": "offline-demo",
        "choices": [{
            "index": 0,
            "finish_reason": "tool_calls" if message.get("tool_calls") else "stop",
            "message": message,
        }],
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="使用固定响应，不调用 API")
    args = parser.parse_args()

    # 与 Agent 相同：现有进程环境变量优先，.env 补充未设置的值。
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    model = "offline-demo" if args.offline else os.environ.get("OPENAI_MODEL")
    client = None
    if not args.offline:
        required = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL")
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            parser.error("请在 .env 中配置：" + ", ".join(missing))
        try:
            max_retries = int(os.environ.get("OPENAI_MAX_RETRIES", "5"))
        except ValueError:
            parser.error("OPENAI_MAX_RETRIES 必须是非负整数")
        if max_retries < 0:
            parser.error("OPENAI_MAX_RETRIES 必须是非负整数")
        client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ["OPENAI_BASE_URL"],
            max_retries=max_retries,
            timeout=60.0,
        )

    try:
        demonstrate(client, model)
    finally:
        if client is not None:
            client.close()


def demonstrate(client, model):
    print("离线固定响应演示" if client is None else "真实模型请求 + 模拟工具执行")
    tools = [EXECUTE_TOOL, SEND_MESSAGE_TOOL]
    messages = [
        {
            "role": "system",
            "content": (
                "这是工具调用教学演示。execute 只返回模拟结果，不执行命令。"
                "收到工具结果后，请明确说明结果是模拟的。"
            ),
        },
        {"role": "user", "content": "请调用 execute，command 为 echo hello，然后解释工具结果。"},
    ]
    request = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": {"type": "function", "function": {"name": "execute"}},
        "reasoning_effort": "medium",
        "max_completion_tokens": 4096,
    }
    show("1. 请求参数：messages 是上下文，tools 是工具定义", request)
    if client is None:
        response = offline_response({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": "call_demo_1",
                "type": "function",
                "function": {"name": "execute", "arguments": '{"command":"echo hello"}'},
            }],
        })
    else:
        response = client.chat.completions.create(**request)

    show("2. 完整 API 响应：对应 api_responses 中的一项", response.model_dump(mode="json"))
    message = response.choices[0].message.model_dump(exclude_none=True)
    show("3. 提取的 assistant 消息：应追加到 message_history", message)
    messages.append(message)
    calls = message.get("tool_calls") or []
    if not calls:
        print("模型未返回工具调用，本次演示结束；请检查模型对工具调用的支持。")
        return

    for call in calls:
        name = call["function"]["name"]
        try:
            arguments = json.loads(call["function"]["arguments"])
            show("4. arguments 经 json.loads 后的 Python 数据", arguments)
            if not isinstance(arguments, dict):
                raise ValueError("工具参数必须是 JSON 对象")
            if name == "execute":
                if arguments.get("command") != "echo hello":
                    raise ValueError("本演示只模拟 command='echo hello'")
                result = {"simulated": True, "output": "hello\n", "returncode": 0}
            else:
                raise ValueError(f"本演示未实现工具：{name}")
        except (ValueError, TypeError) as exc:
            result = {"error": str(exc)}
        observation = {
            "role": "tool",
            "tool_call_id": call["id"],
            "content": json.dumps(result, ensure_ascii=False),
        }
        show("5. 工具观察：tool_call_id 对应助手工具调用的 id", observation)
        messages.append(observation)

    show("6. 第二次请求的 messages：system → user → assistant → tool", messages)
    if client is None:
        final_response = offline_response({
            "role": "assistant",
            "content": "模拟工具返回 hello 和退出码 0；本演示没有真正执行命令。",
        })
    else:
        final_response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="none",
            reasoning_effort="medium",
            max_completion_tokens=4096,
        )
    show("7. 模型根据工具结果生成的回答", final_response.choices[0].message.model_dump(exclude_none=True))


if __name__ == "__main__":
    main()
