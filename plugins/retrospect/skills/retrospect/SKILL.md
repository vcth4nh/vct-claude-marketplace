---
name: retrospect
description: Use when the user wants a retrospective, reflection, or introspection over past Claude Code sessions in this project — what they corrected, what kept failing, where the workflow ground, what worked — or wants session history mined into CLAUDE.md rules.
argument-hint: "[N | Nd | all] [everywhere | /path] [topic]"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(ls:*), Bash(find:*), Bash(wc:*), Bash(stat:*), Bash(date:*), Bash(jq:*)
---

# Retrospect

Mine past session transcripts of this project with parallel subagents, then
reconcile their findings into (a) a chat retrospective — recurring failure
patterns, workflow friction, wins — and (b) proposed CLAUDE.md rules built
from the user's own corrections. Read-only throughout; only user-approved
CLAUDE.md diffs ever touch disk, in the final step.

**Arguments:** `$ARGUMENTS` = `[N | Nd | all] [everywhere | <project>] [topic…]`.
Leading tokens, in this order:

- **Scope** — `N` (last N sessions), `Nd` (last N days), `all`. Default: 10
  for full mode, `all` for targeted mode.
- **Place** — `everywhere` = all projects; one token that starts with `/`,
  `~`, or `.` = that project; absent = the current project.

Everything after the leading tokens is a **topic** and switches on targeted
mode — hunt every instruction the user ever gave about that topic.

## 1. Recon (main context)

- Transcript folders live under `~/.claude/projects/<mangled>/`, where
  `<mangled>` is a project's absolute path with every non-alphanumeric
  character replaced by `-`. Current project: mangle the working directory.
  Specific project: expand the token, mangle it, and look for the exact
  folder; none there → match the token against the existing folder names.
  `everywhere`: every project folder. If no folder matches or several could,
  show the candidates and ask — do not guess.
- In scope: **top-level** `*.jsonl` only (`find <dir> -maxdepth 1 -name '*.jsonl'`).
  Session subdirectories hold `subagents/agent-*.jsonl` — never mine those.
- Exclude the current session: by `$CLAUDE_SESSION_ID` when set; otherwise
  exclude the newest-mtime file and tell the user you did (the current session
  is always the one being written). Other sessions can be live too (parallel
  windows, worktrees) — miners flag relocated or still-growing files in
  `parse_note`; label those sessions partial in the report.
- Apply the scope by mtime. Report session count, date range, total size —
  per project in `everywhere` mode. More than 20 sessions in scope → state the
  subagent count and get a go-ahead before the fan-out.
- Fewer sessions than expected? `~/.claude/history.jsonl` still holds the
  typed prompts of cleaned-up sessions — say so, and see the retention note in
  step 5.
- Targeted mode only: derive 3–5 search terms for the topic (synonyms
  included) and `grep -l` them across the in-scope files. Dispatch miners only
  to matching sessions. Report the terms used and the sessions skipped, so the
  user can judge the recall.

## 2. Fan out

Dispatch one `retrospect:session-insight-miner` subagent per session file —
all in a single message so they run in parallel. Each dispatch prompt is the
absolute transcript path and the project directory — plus, in targeted mode,
one `Topic: …` line. The extraction rules live in the agent, not in your
prompt. Miners return one
JSON object each; a miner that returns prose instead gets one retry, then is
dropped with a note in the report.

## 3. Reconcile (main context)

- **Corrections → rules:** merge semantically similar corrections (any
  wording) into one imperative rule each, citing all source sessions. Where
  corrections conflict, provisionally prefer the most recent but list both
  versions with dates for the user to decide.
- **Patterns, friction, wins:** group across sessions; label what only one
  session shows as single-session.
- **Existing memory:** check the project `CLAUDE.md`, `CLAUDE.local.md`, and
  `~/.claude/CLAUDE.md`. Drop proposals already covered; flag proposals that
  contradict existing content instead of silently overriding.
- **Routing:** project-specific conventions → project `CLAUDE.md`; universal
  preferences → global `~/.claude/CLAUDE.md`. In a public repo, route private
  workflow rules to `CLAUDE.local.md` or global, never the committed file.
- **Place modes:** the dedup check and the write targets are always the
  global file plus the current or specified project's files. A correction
  that recurs across different projects is strong evidence for the global
  file — say so. In `everywhere` mode, a rule bound to some other project is
  listed for information, never written there.

## 4. Report (chat only — no report file)

**Targeted mode** reports a timeline instead of the sections below: every user
statement about the topic in date order, how the instruction evolved, the
current effective version, and whether Claude complied each time — in
`everywhere` mode, name the project on each entry. A recurring instruction
becomes one consolidated rule proposal, through the same step-5 gate. Full
mode:

Three sections with evidence: failure patterns, friction, wins (`everywhere`
mode: grouped by project). Then a
numbered table: **# | Proposed rule | User's words | Session/date | Complied? |
Target file | Confidence**. Below it, one line each so the user can veto your
filtering: conflicts awaiting decision, proposals already covered, inferred
proposals with no direct quote (clearly marked — never presented as rules),
and one-off corrections you dropped.

## 5. Approve, then write

The user approves all, picks numbers, or edits wording. Show the exact diff
per target file — match the file's existing structure, or add a
`## Working preferences` section; imperative rules, one line each. Write only
after explicit approval, only what was approved, then re-read the files to
confirm. If history looked thin, note that `cleanupPeriodDays` in
`~/.claude/settings.json` controls how long transcripts are kept.

## Common mistakes

| Mistake | Reality |
|---|---|
| Mining `subagents/agent-*.jsonl` or `isSidechain` turns | Those "user" messages are Claude's own prompts, not the user. |
| Reading transcripts in the main context | That is the miners' job. The main context sees only their JSON. |
| Leaving the current session in scope | It contains this very retrospective request; skip it. |
| Presenting a quoteless rule as a rule | It goes to the inferred list, clearly marked. |
| Treating pasted review text as the user's words | Third-party text counts only where the user endorsed it. |
| Writing CLAUDE.md right after the report | The gate is explicit approval of an exact diff. |
| Repeating extraction rules in dispatch prompts | The agent definition owns them; duplicated copies drift. |
| Stretching thin topic matches into findings | An empty targeted result is correct. Report the terms tried and stop. |
| Writing a rule into an unrelated project from `everywhere` mode | Write targets are only the global file and the current or specified project. |
