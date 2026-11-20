# Chess skill invocation implementation plan

The user approved the skill-loading design explained in the conversation and
requested implementation, a commit of current code changes, and a push.

**Goal:** Let ChessAgent load a named strategy into its conversation through
`invoke_skill`, with recoverable errors and progressive disclosure.

**Architecture:** Reuse the base agent's conditional tool registration and cached
skill catalog. The chess helper validates raw JSON arguments and returns cached
full content; the dispatcher links that content to the original tool call. Fix
the shared loader's name lookup and validation because chess invocation depends
on it. Keep existing unrelated student changes intact.

**Tech stack:** Python, PyYAML, pytest, httpx mock transport.

## Implementation steps

- [x] Add `scripts/local/test_chess_skills.py` covering full-content return,
  malformed/non-object/missing/extra/non-string/unknown arguments, conditional
  registration, metadata-only initial prompts, linked observations, and recovery
  from an invalid invocation before a valid one. Use a temporary skill whose
  directory and frontmatter names differ to check the shared loader contract.
- [x] Run `.venv/bin/python -m pytest -q scripts/local/test_chess_skills.py`
  before implementation and confirm the missing helper/dispatch is exposed.
- [x] Implement `_invoke_skill` in `src/assignment/agent/chess_tools.py`:
  `json.loads(arguments)`, validate exactly one nonempty string `name`, look up
  `skills[name]["content"]`, and turn failures into `<chess_error>` observations.
- [x] Add the registered `invoke_skill` branch to `ChessAgent.execute_tool_calls`
  in `src/assignment/agent/chess_agent.py`. Preserve the original call ID and do
  not update live-game state when reading instructions.
- [x] Fix `Agent.load_skills` in `src/assignment/agent/base.py` to scan sorted
  subdirectories, validate root/files/YAML/nonempty name and description,
  reject duplicate frontmatter names, expose only name/description metadata,
  and retain the complete original content. Errors identify the offending path.
  Update the tool argument description in `src/assignment/agent/tools.py` to
  identify the frontmatter name.
- [x] Run the new tests and existing loader checks, then all offline public and
  local checks. Record any unrelated baseline failures without changing the
  supplied tests or rewriting other assignment parts. Results: 17 new chess-skill
  checks pass; the complete run reports 71 passed, 4 preexisting failures, and
  4 deselected Modal cases. Failures concern the old chess registration
  expectation, two CodeAgent prompt cases, and the old compaction-filter fixture.
- [x] Review changes and update `AI_USAGE.md`. Independent review found no
  critical or important Part 3.5 issues. Syntax and whitespace checks pass.

Delivery: stage source/tests/supporting docs while leaving runtime artifacts
local, commit, and push `main` to `origin` as explicitly requested by the user.

## Validation and scope

Tests use stub credentials and HTTP mock transport; they do not call a model or
launch a paid sandbox. The assignment's live skill/search trajectory is separate
from these implementation checks and will not be presented as verified.
Do not modify `tests/`, `tasks/`, or `chess_app/`. Preserve compaction experiments
and provider/viewer changes already present in the working tree.
