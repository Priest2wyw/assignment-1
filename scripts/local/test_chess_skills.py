"""Offline Part 3.5 checks; run explicitly without changing provided tests."""

import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from assignment.agent.chess_agent import ChessAgent
from assignment.agent.chess_tools import _invoke_skill


CONTENT = (
    "---\nname: choose-move\ndescription: Choose a chess move.\n---\n\n"
    "UNIQUE_FULL_STRATEGY: search with simulate_move before play_move.\n"
)
SKILLS = {
    "choose-move": {
        "metadata": "name: choose-move\ndescription: Choose a chess move.",
        "content": CONTENT,
    }
}
INITIAL_STATE = {
    "fen": "initial-position",
    "game_over": False,
    "turn": "white",
    "squares": {},
    "legal_moves": ["e2e4"],
}


def skill_call(arguments, call_id="skill-call"):
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": "invoke_skill", "arguments": arguments},
    }


@pytest.fixture
def make_agent(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://model.test/v1")
    directory = tmp_path / "directory-with-another-name"
    directory.mkdir()
    (directory / "SKILL.md").write_text(CONTENT, encoding="utf-8")
    requests = []

    def handler(request):
        requests.append(request)
        assert request.url.path == "/api/state"
        assert request.method == "GET"
        return httpx.Response(200, json=INITIAL_STATE)

    with httpx.Client(
        base_url="http://chess.test", transport=httpx.MockTransport(handler)
    ) as client:
        def make(with_skills=True, skills_path=None):
            return ChessAgent(
                SimpleNamespace(),
                model="test-model",
                skills_path=str(skills_path or tmp_path) if with_skills else None,
                http_client=client,
                reset_game=False,
                auto_stop_environment=False,
            )

        yield make, requests


def test_invoke_returns_complete_cached_content():
    assert _invoke_skill(SKILLS, '{"name": "choose-move"}') == CONTENT


@pytest.mark.parametrize("arguments", [
    "{bad-json", "[]", "null", "{}", '{"name": 42}', '{"name": []}',
    '{"name": ""}', '{"name": " "}', '{"name": "missing"}',
    '{"name": "../directory-with-another-name"}',
    '{"name": "choose-move", "extra": true}',
])
def test_invalid_invocation_is_recoverable(arguments):
    result = _invoke_skill(SKILLS, arguments)
    assert result.startswith("<chess_error>")
    assert result.endswith("</chess_error>")
    assert _invoke_skill(SKILLS, '{"name": "choose-move"}') == CONTENT


def test_catalog_discloses_only_metadata_and_registers_once(make_agent):
    make, _ = make_agent
    agent = make()
    names = [tool["function"]["name"] for tool in agent.tools]
    assert names.count("invoke_skill") == 1
    assert list(agent.skills) == ["choose-move"]
    assert "choose-move" in agent.system_prompt
    assert "Choose a chess move." in agent.system_prompt
    assert "UNIQUE_FULL_STRATEGY" not in json.dumps(agent.build_prompt())


def test_dispatch_links_full_content_and_preserves_game_state(make_agent):
    make, requests = make_agent
    agent = make()
    requests.clear()
    before_state = agent.last_state
    results = agent.execute_tool_calls([
        skill_call('{"name": "missing"}', "bad"),
        skill_call('{"name": "choose-move"}', "good"),
    ])
    assert results[0]["tool_call_id"] == "bad"
    assert results[0]["content"].startswith("<chess_error>")
    assert results[1] == {
        "role": "tool", "tool_call_id": "good", "content": CONTENT,
    }
    assert agent.last_state is before_state
    assert agent.finished is False
    assert requests == []


@pytest.mark.parametrize("empty_directory", [False, True])
def test_no_skills_does_not_register_or_execute_skill_tool(
    make_agent, tmp_path, empty_directory
):
    make, _ = make_agent
    empty = tmp_path / "empty"
    empty.mkdir()
    agent = make(with_skills=empty_directory, skills_path=empty)
    assert "invoke_skill" not in [tool["function"]["name"] for tool in agent.tools]
    assert "<skills>" not in agent.system_prompt
    # A cached entry alone must not grant access to an unregistered tool.
    agent.skills = SKILLS
    result = agent.execute_tool_calls([skill_call('{"name": "choose-move"}')])
    assert result[0]["content"].startswith("<chess_error>")


def test_repository_chess_skill_loads_through_dispatch(make_agent):
    make, _ = make_agent
    root = Path(__file__).resolve().parents[2] / "tasks/chess-skills"
    agent = make(skills_path=root)
    result = agent.execute_tool_calls([skill_call('{"name": "select-move"}')])
    assert result[0]["content"] == (root / "select-move/SKILL.md").read_text()
