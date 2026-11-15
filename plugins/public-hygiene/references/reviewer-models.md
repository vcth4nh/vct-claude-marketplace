# Selecting reviewer models

The parent uses this policy before dispatching a reviewer. Keep the
inline-versus-delegated routing in [cold-read](../skills/cold-read/SKILL.md)
and [leak-check](../skills/leak-check/SKILL.md); model selection does not
add review stages or require subagents for routine snippets.

Honor user-specified reviewer models and effort, and enforced
harness settings. The defaults below are starting choices, not a measured
ranking or a guarantee of review quality.

| Task | Default |
|---|---|
| Input hashes and report structure | Scripts or existing validation helpers |
| Bounded extraction or explicit pattern checks, when already needed | Haiku or GPT-6 Luna |
| Context interpretation, disclosure decisions, or meaning-preservation review | Sonnet or GPT-6.1 Terra at medium effort |
| Dense technical claims, dependencies across several documents, or difficult sequential reviews | Increase effort or use a stronger available reviewer, within the user's constraints |

Small-model scans stay read-only and return candidates with source quotes
to the parent. Keep those candidates out of a fresh reviewer's handoff.
Scans do not replace the full review or issue its publication verdict.
Send substantive reviews directly to the chosen reviewer; do not routinely
run a small scan first.
Choose the reviewer and effort upfront from the task's complexity. Do not
use a small model's confidence as the only escalation trigger; a confident
answer can still miss a problem.

## Harness settings

- **Claude Code:** the bundled `cold-reader` and `external-reviewer` agents
  default to `model: sonnet` and `effort: medium`. Pass an explicit model or
  effort override through the Agent tool's `model` and `effort` parameters,
  where supported, when the user requests it or the task warrants escalation.
  Respect enforced settings; do not change global configuration.
- **Codex:** when the spawning tool exposes model and effort controls,
  request `gpt-6.1-terra` and `medium` for a substantive review. Start with
  fresh context and pass the linked reviewer instructions; Claude agent
  frontmatter does not configure a Codex reviewer.
- If a default model is unavailable, choose another available model suitable
  for the full review, including the parent model when suitable, within the
  user's constraints. This fallback applies only to defaults, not a
  user-specified model or effort, unless the user authorized a fallback.
  If a user-specified setting cannot be honored, or the harness reports
  that a different setting was used, use [report delivery](report-delivery.md)'s incomplete
  delivery with the selection failure as its reason. Preserve any saved
  report, but deliver `VERDICT: INCOMPLETE` even if its verdict was PASS.
- Use only model identifiers the harness supports. Disclose a fallback in
  progress and in the final report link label, distinguishing requested
  settings from active settings reported by the harness. Keep the saved report and its
  verdict unchanged. If no fresh reviewer can run, use report delivery's
  incomplete-review procedure.

## Review integrity

For a full review, keep the clean handoff and
[report delivery](report-delivery.md) checks for every model.
Validate report completeness and unchanged inputs before
accepting the result; these checks do not establish finding quality.
An incomplete review remains incomplete under that procedure. Preserve
its evidence; a model change cannot supply missing author facts or release
approval. Never retry merely to obtain PASS or discard conflicting findings.
