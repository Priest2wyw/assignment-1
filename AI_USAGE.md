# AI assistance record

On 2026-11-10, OpenAI Codex assisted with cloning the upstream assignment and
its pinned submodule, preparing an isolated Conda Python interpreter and a
project `.venv`, installing the upstream locked dependencies, checking the
environment, and writing local setup documentation and helper scripts.

This assistance did not implement student TODOs or change the assignment's
source code, tests, task definitions, or chess application. Keep this record
updated with any further AI assistance before submitting the assignment.

On 2026-11-11, OpenAI Codex translated `ASSIGNMENT.md` into
`ASSIGNMENT-cn.md`, checked that the translation preserved the assignment
structure and technical examples, and reviewed the `Agent.build_prompt`
implementation using isolated offline checks. The review did not modify the
agent implementation.

On 2026-11-12, OpenAI Codex reviewed the working-tree changes for logical Git
commits, ran the offline test suite, checked Python and shell syntax, and ran
the tool-calling demonstration in offline mode. It removed trailing whitespace
from `base.py` and organized the existing changes into commits. The offline
suite reported 10 passed, 5 failed, and 4 deselected; the failures concern
unfinished compaction, skill loading, and chess tools.

On 2026-11-15 and 2026-11-16, OpenAI Codex explained Part 1 skill discovery,
YAML frontmatter parsing with regular expressions, tool registration and
dispatch, and patch submission. It provided code examples, added supplemental
offline checks in `scripts/local/test_skills.py` and a skill-loading plan, and
reviewed local code and trajectories to diagnose model selection and malformed
API messages. It also explained the chess repair and Django bulk-update tasks,
reviewed the initial context-compaction implementation, and suggested how to
construct summary requests and preserve recent complete tool steps.

At the user's request, Codex prepared the current code as a Task 2 version-one
checkpoint. The offline public suite reported 11 passed, 4 failed, and 4
deselected. The compaction test fails because the current implementation
replaces all history with a summary and drops the latest complete tool step;
the other three failures concern unfinished Part 3 chess tools. Skill-loader
validation also remains incomplete. This checkpoint is not a claim that
Task 2 is complete or that the generated patches passed fresh-testbed
evaluation. Runtime artifacts and diagnostic logs remain outside this commit.

On 2026-11-17, OpenAI Codex analyzed the repeated compaction behavior using
saved trajectories and implemented a read-only JSON artifact viewer under
`scripts/local/`. The viewer lists artifacts, displays all compaction events,
and provides field selectors for full-file and individual-event inspection.
Codex added offline file-access tests and checked the HTTP endpoints against
the saved trajectory. At the user's request it checked ports 8101–8120 and
started the viewer on 0.0.0.0:8105, the lowest available port.

Later on 2026-11-17, at the user's explicit request, Codex implemented an
experimental compaction-input filter that excludes role=tool observations
before summarization while preserving original API audit records. It added
an offline test demonstrating that outputs are omitted and that actions and
prior memory remain available to the summarizer. The summary instruction now
distinguishes attempted actions from confirmed outcomes. This experiment
differs from the assignment's original requirement to summarize observations;
it does not address the existing loss of recent complete tool steps.

Codex subsequently compared the two current Django trajectories, separately
summed action and summary API usage, inspected per-step context sizes and
summary quality, and wrote `artifacts/token-usage-analysis.md`. The report
records input-file hashes, cache statistics, experimental limitations, and
the lack of independent patch-replay verification during this analysis.

On 2026-11-18, Codex diagnosed slow chess-agent requests by inspecting saved
usage data, checking SDK request serialization with a mock transport, and
making two small-budget live DeepSeek requests to compare output-limit fields.
It consulted the DeepSeek API reference and recorded the parameter
compatibility findings in `artifacts/chess-token-limit-diagnosis.md` without
changing the assignment's provided model-request implementation.

Codex then added model-provider overrides to the chess CLI and Make targets
at the user's request. GPT-OSS targets resolve GPT_OSS_URL, GPT_OSS_KEY and
GPT_OSS_NAME from the environment/.env; defaults retain the OPENAI_* setup.
Credentials are selected by variable name, not command-line secret values.
It added offline selection tests, checked Make's expanded commands, and made
one small live OpenRouter tool-call test which successfully returned an e2e4
play_move call (342 total tokens). The connectivity check did not run a full
chess game or execute the four observation experiments.

On 2026-11-20, Codex explained the Part 3 move, simulation, sandboxed Python,
and chess-skill tools, provided implementation examples for Parts 3.1–3.4,
and checked the student's implementation with offline stand-ins. At the user's
request it implemented Part 3.5: cached full-content skill invocation,
recoverable argument errors, and dispatch restricted to a registered tool.
It also repaired the shared skill loader's frontmatter-name lookup, duplicate
and malformed-file validation, and metadata-only catalog for chess skills.
Supplemental tests were added under `scripts/local/`; provided tests, tasks,
and the chess submodule were not changed.

The new Part 3.5 checks reported 17 passed. The complete offline public and
local check run reported 71 passed, 4 failed, and 4 deselected. The four
remaining failures were present before this work: the public chess test
expects only play_move even after simulate_move is registered; two CodeAgent
cases object to unconditional submission-instruction wording; and the older
compaction-filter experiment's fixture does not initialize the current
compaction settings. An independent code review found no critical or important
Part 3.5 issues. No real model request, Modal sandbox, or required live
skill/search trajectory was run as part of this implementation verification.
The user requested committing and pushing all current code and supporting
documentation, including existing provider/viewer and compaction work;
generated runtime artifacts remain outside the commit.
