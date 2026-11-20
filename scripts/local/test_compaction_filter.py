"""Offline checks for the experiment that omits tool outputs from summaries."""
from copy import deepcopy
import json
from types import SimpleNamespace

from assignment.agent.base import Agent


def test_compaction_omits_tool_outputs_but_preserves_actions_and_audit_history():
    agent = Agent.__new__(Agent)
    agent.model = "offline-test"
    agent.compaction_max_tokens = 1200
    agent.system_prompt = "System instructions"
    agent.task_prompt = "Task instructions"
    action = {
        "role": "assistant", "content": "Inspect the repository.",
        "tool_calls": [{"id": "call_1", "type": "function", "function": {
            "name": "execute", "arguments": '{"command": "ls"}',
        }}],
    }
    observation = {"role": "tool", "tool_call_id": "call_1",
                   "content": "UNIQUE_TOOL_OUTPUT_DO_NOT_SUMMARIZE"}
    agent.message_history = [
        {"role": "user", "content": "Previous working memory"},
        action, observation,
    ]
    original_history = deepcopy(agent.message_history)
    agent.api_prompts = [deepcopy(original_history)]
    agent.api_responses = [{"original": True}]
    original_audit = deepcopy((agent.api_prompts, agent.api_responses))
    captured = []
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="Inspected via ls; result unknown."))],
        model_dump=lambda **kwargs: {"summary_response": True},
    )

    def create(**kwargs):
        captured.append(kwargs)
        # Input filtering must not mutate history while a request is in flight.
        assert agent.message_history == original_history
        return response

    agent.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    prompt, raw = agent.compact_context()
    serialized = json.dumps(prompt)
    assert "UNIQUE_TOOL_OUTPUT_DO_NOT_SUMMARIZE" not in serialized
    assert "Inspect the repository." in serialized
    assert "Previous working memory" in serialized
    assert "call_1" in serialized
    assert "System instructions" in serialized
    assert "Task instructions" in serialized
    assert all(isinstance(message["content"], str) for message in prompt)
    assert captured[0]["messages"] == prompt
    assert raw == {"summary_response": True}
    assert (agent.api_prompts, agent.api_responses) == original_audit
    assert "UNIQUE_TOOL_OUTPUT_DO_NOT_SUMMARIZE" not in json.dumps(agent.build_prompt())
    assert "result unknown" in json.dumps(agent.build_prompt())
