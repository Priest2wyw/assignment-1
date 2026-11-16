"""Offline Task 1.4 checks; run with pytest explicitly (no Modal or API calls)."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from assignment.agent.base import Agent
from assignment.agent.code_agent import CodeAgent


def write_skill(root, directory="folder", name="sample", description="Read a guide."):
    path = root / directory / "SKILL.md"
    path.parent.mkdir(parents=True)
    content = (
        "---\n"
        + yaml.safe_dump({"name": name, "description": description})
        + "---\n\nOnly the full skill mentions patch.txt.\n"
    )
    path.write_text(content, encoding="utf-8")
    return path, content


def load_skills(path):
    # The loader needs no client, environment, or constructor side effects.
    return Agent.load_skills(Agent.__new__(Agent), path)


@pytest.fixture
def make_agent(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:0/v1")

    def make(skills_path=None):
        environment = SimpleNamespace(
            machine="x86_64", release="test", system="Linux", version="test"
        )
        return CodeAgent(
            "Fix the software issue.", environment, model="test-model",
            skills_path=skills_path,
        )

    return make


def skill_call(arguments, call_id="skill_call"):
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": "invoke_skill", "arguments": arguments},
    }


def test_loader_uses_frontmatter_names_and_preserves_complete_content(tmp_path):
    _, first = write_skill(tmp_path, "a-directory", "first", "说明：读取指南。")
    _, second = write_skill(tmp_path, "b-directory", "second")
    (tmp_path / "README.md").write_text("Not a skill")
    skills = load_skills(tmp_path)

    assert list(skills) == ["first", "second"]
    assert skills["first"]["content"] == first
    assert skills["second"]["content"] == second
    assert "说明：读取指南。" in skills["first"]["metadata"]
    assert "name: first" in skills["first"]["metadata"]
    assert "patch.txt" not in skills["first"]["metadata"]


def test_loader_supports_multiline_yaml_description(tmp_path):
    path, _ = write_skill(tmp_path)
    path.write_text(
        "---\nname: sample\ndescription: >\n  Read this\n  useful guide.\n---\nBody\n"
    )
    assert "Read this useful guide." in load_skills(tmp_path)["sample"]["metadata"]


@pytest.mark.parametrize("kind", ["missing", "file"])
def test_loader_rejects_invalid_root(tmp_path, kind):
    path = tmp_path / "skills"
    if kind == "file":
        path.write_text("not a directory")
    with pytest.raises(ValueError, match=str(path)):
        load_skills(path)


def test_loader_rejects_child_without_skill_file(tmp_path):
    directory = tmp_path / "broken"
    directory.mkdir()
    with pytest.raises(ValueError, match=str(directory / "SKILL.md")):
        load_skills(tmp_path)


@pytest.mark.parametrize("content", [
    "No frontmatter", "---\nname: sample\n", "---\n---\nBody",
    "---\nname: [invalid\n---\nBody", "---\n- sample\n---\nBody",
    "---\ndescription: guide\n---\nBody", "---\nname: sample\n---\nBody",
    "---\nname: 42\ndescription: guide\n---\nBody",
    "---\nname: ' '\ndescription: guide\n---\nBody",
    "---\nname: sample\ndescription: false\n---\nBody",
    "---\nname: sample\ndescription: ''\n---\nBody",
])
def test_loader_rejects_bad_frontmatter_with_file_path(tmp_path, content):
    path, _ = write_skill(tmp_path)
    path.write_text(content)
    with pytest.raises(ValueError, match=str(path)):
        load_skills(tmp_path)


def test_loader_rejects_duplicate_frontmatter_names(tmp_path):
    write_skill(tmp_path, "first", "same")
    second, _ = write_skill(tmp_path, "second", "same")
    with pytest.raises(ValueError) as error:
        load_skills(tmp_path)
    assert "same" in str(error.value)
    assert str(second) in str(error.value)


@pytest.mark.parametrize("empty_directory", [False, True])
def test_no_skills_has_no_catalog_tool_or_submission_instructions(
    tmp_path, make_agent, empty_directory
):
    agent = make_agent(str(tmp_path) if empty_directory else None)
    assert agent.skills == {}
    assert "invoke_skill" not in [tool["function"]["name"] for tool in agent.tools]
    prompt = json.dumps(agent.build_prompt())
    assert "patch.txt" not in prompt
    assert "submission instructions" not in prompt
    assert "<skills>" not in prompt


def test_skill_body_enters_conversation_only_after_invocation(tmp_path, make_agent):
    _, content = write_skill(tmp_path, name="submit-task")
    write_skill(tmp_path, "another-folder", "another-skill", "Another guide.")
    agent = make_agent(str(tmp_path))
    assert "submit-task" in agent.system_prompt
    assert "Read a guide." in agent.system_prompt
    assert "another-skill" in agent.system_prompt
    assert "Another guide." in agent.system_prompt
    assert "patch.txt" not in json.dumps(agent.build_prompt())
    assert "invoke_skill" in [tool["function"]["name"] for tool in agent.tools]

    action = {
        "role": "assistant", "content": None,
        "tool_calls": [skill_call('{"name": "submit-task"}')],
    }
    result = agent.execute_tool_calls(action["tool_calls"])
    assert result == [{"role": "tool", "tool_call_id": "skill_call", "content": content}]
    agent.message_history.extend([action, *result])
    assert agent.build_prompt()[-1] == result[0]
    assert not agent.finished


@pytest.mark.parametrize("arguments", [
    "{bad-json", "[]", "{}", '{"name": 42}', '{"name": []}',
    '{"name": ""}', '{"name": "missing"}', '{"name": "../folder"}',
    '{"name": "sample", "extra": true}',
])
def test_bad_invocation_recovers_for_next_call(tmp_path, make_agent, arguments):
    _, content = write_skill(tmp_path)
    agent = make_agent(str(tmp_path))
    result = agent.execute_tool_calls([
        skill_call(arguments, "bad"), skill_call('{"name": "sample"}', "good")
    ])
    assert len(result) == 2
    assert result[0]["tool_call_id"] == "bad"
    assert result[0]["content"].startswith("<tool_error>")
    assert result[1] == {"role": "tool", "tool_call_id": "good", "content": content}
    assert not agent.finished
