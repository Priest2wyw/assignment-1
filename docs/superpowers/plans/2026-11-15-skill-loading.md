# Task 1.4: skill loading

The user approved the design explained in the conversation and requested its
implementation in the current workspace.

## Design

`Agent.load_skills(Path)` scans sorted immediate child directories, reads each
`SKILL.md` as UTF-8, parses its leading YAML frontmatter with `yaml.safe_load`,
and returns a mapping keyed by frontmatter `name`. Each entry holds a concise
name/description `metadata` string and the complete original `content`.
Names and descriptions must be nonempty strings. Invalid paths, missing skill
files, missing/malformed frontmatter, and duplicate names raise a `ValueError`
identifying the offending path. Regular files in the root are ignored; an
empty directory returns an empty mapping.

`CodeAgent` advertises metadata only in its system prompt. The base constructor
already registers `invoke_skill` for nonempty catalogs. Its executor validates
the single `name` argument and returns the cached content in a linked tool
observation. Bad arguments or unknown names yield recoverable tool errors.
Loading instructions does not execute commands or finish the task. No-skill
prompts contain no built-in submission instructions.

## Implementation and validation

- [ ] Add offline tests in `scripts/local/test_skills.py` (assignment rules
  prohibit editing `tests/`). Cover YAML validation, multiple skills, duplicate
  names, empty/no skills, prompt disclosure, and invocation error recovery.
- [ ] Run `.venv/bin/python -m pytest -q scripts/local/test_skills.py` and
  confirm failures expose the unimplemented behavior.
- [ ] Implement the loader in `src/assignment/agent/base.py`, prompt catalog
  and tool dispatch in `src/assignment/agent/code_agent.py`, and correct the
  argument documentation in `src/assignment/agent/tools.py` to refer to the
  frontmatter name rather than the directory name.
- [ ] Run the local tests and the public skill-catalog test, then the complete
  offline suite; distinguish existing failures for other assignment parts.
- [ ] Review the diff and update `AI_USAGE.md` with assistance and validation.

No changes to provided tests, tasks, chess application, model-call logging,
cleanup, compaction, or chess tool implementations are required.
