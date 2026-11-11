"""The Part 1 coding agent: fix a software issue and submit a git patch."""

from __future__ import annotations

import json
from typing import Any

from assignment.agent.base import (
    DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
    DEFAULT_COMPACTION_MAX_TOKENS,
    Agent,
    format_tool_output,
)
from assignment.agent.tools import EXECUTE_TOOL, SEND_MESSAGE_TOOL
from assignment.env import Environment

class CodeAgent(Agent):
    """An agent that fixes a software issue and submits a git patch."""

    def __init__(
        self,
        task: str,
        environment: Environment,
        model: str | None = None,
        logs_save_path: str | None = None,
        step_limit: int = 100,
        skills_path: str | None = None,
        auto_stop_environment: bool = True,
        compact_threshold_tokens: int | None = None,
        compaction_keep_recent_steps: int = DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
        compaction_max_tokens: int = DEFAULT_COMPACTION_MAX_TOKENS,
    ):
        super().__init__(
            environment=environment,
            model=model,
            logs_save_path=logs_save_path,
            step_limit=step_limit,
            skills_path=skills_path,
            auto_stop_environment=auto_stop_environment,
            compact_threshold_tokens=compact_threshold_tokens,
            compaction_keep_recent_steps=compaction_keep_recent_steps,
            compaction_max_tokens=compaction_max_tokens,
        )
        self.task = task
        self.submitted_patch = ""

        # TODO(Part 1.3): Make the `execute` and `send_message` tools available
        # to the agent.
        self.tools.extend( [EXECUTE_TOOL, SEND_MESSAGE_TOOL])
        # DONE(1.1.b): Construct the system prompt and task_prompt. These
        # should be usable by the `Agent.build_prompt` method.
        system_information = json.dumps(
            {
                "machine": self.env.machine,
                "release": self.env.release,
                "system": self.env.system,
                "version": self.env.version,
            },
            indent=2,
            ensure_ascii=False,
        )
        self.system_prompt = (
            "You are a helpful assistant that focus on code task.\n"
            "Use the available tools to inspect files, modify code, and run commands.\n"
            "Read relevant code before making changes. Keep changes focused on the task.\n"
            "Verify your changes with relevant tests or checks, and report results accurately.\n"
            "Use tool observations to decide your next action.\n"
            "Follow the provided submission instructions when the task is complete.\n"
            "\n"
            "<system_information>\n"
            f'{system_information}'
            "</system_information>"
        )
        self.task_prompt = task
        # TODO(1.4): If any skills are available to the agent, make their
        # descriptions/metadata available to the agent in the prompt.

    def execute_tool_calls(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Execute ``execute`` and ``send_message`` calls in the code sandbox."""
        observations = []

        for call in tool_calls:
            function = call["function"]
            name = function["name"]

            try:
                arguments = json.loads(function["arguments"])

                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be a JSON object.")

                if name == "execute":
                    allowed = {"command", "shell", "cwd", "timeout", "env"}

                    if "command" not in arguments:
                        raise ValueError("Missing required argument: command.")

                    extra = arguments.keys() - allowed
                    if extra:
                        raise ValueError(
                            f"Unexpected arguments: {', '.join(sorted(extra))}"
                        )

                    result = self.env.execute(**arguments)
                    content = format_tool_output(result)

                elif name == "send_message":
                    if set(arguments) != {"summary"}:
                        raise ValueError(
                            "send_message requires exactly one argument: summary."
                        )

                    summary = arguments["summary"]
                    if not isinstance(summary, str):
                        raise ValueError("summary must be a string.")

                    # 本作业把这个工具用作最终提交信号。
                    print(summary, flush=True)
                    self.finished = True
                    content = "Submission received. Task finished."

                else:
                    raise ValueError(f"Unknown tool: {name}")

            except (ValueError, TypeError) as exc:
                # JSONDecodeError 也是 ValueError 的子类。
                # 把参数错误反馈给模型，让它有机会修正。
                content = f"<tool_error>{exc}</tool_error>"

            observations.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": content,
            })

        return observations
