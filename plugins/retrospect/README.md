# retrospect

Run a retrospective over your past Claude Code sessions in a project:
**quick recon → parallel per-session miner subagents → reconcile**. You get a
chat report — recurring failure patterns, workflow friction, what went well —
plus CLAUDE.md rule proposals built from your own corrections, each one traced
to a verbatim quote. Read-only throughout; only the diffs you approve are
written. Everything runs locally.

One skill (`/retrospect:retrospect`) plus one agent
(`retrospect:session-insight-miner`). No scripts, no hooks, no state.

## What it encodes

- **Recon that doesn't guess.** The transcript-folder mangle rule; top-level
  `*.jsonl` only; `subagents/agent-*.jsonl` and `isSidechain` turns are
  Claude's own prompts, never mined; the current session is excluded;
  relocated (worktree) and still-live sessions are detected and labeled.
- **Fan-out for scale.** One read-only miner per session file, all in
  parallel, each returning one small JSON object — the main context never
  reads a transcript. Big files are `jq`-prefiltered inside the miner.
- **Evidence discipline.** Every proposed rule carries the user's words
  verbatim; quoteless proposals land in a marked "inferred" list; pasted
  third-party text (reviews) counts only where the user endorsed it; dropped
  one-offs are listed so the user can veto the filtering.
- **Reconciliation.** Semantically similar corrections merge into one
  imperative rule with all source sessions cited; conflicts surface with both
  dates; proposals already covered by existing CLAUDE.md files are dropped;
  public repos route private workflow rules to `CLAUDE.local.md` or the global
  file.
- **A hard write gate.** The report is chat-only. CLAUDE.md changes appear as
  exact diffs and are written only after explicit approval, then re-read.

## Install

```text
/plugin marketplace add vcth4nh/vct-claude-marketplace-public
/plugin install retrospect@vct-public
```

`jq` is recommended for multi-megabyte transcripts (miners fall back to
`grep`/`rg`).

## Usage

```text
/retrospect:retrospect                       full retro, last 10 sessions
/retrospect:retrospect 20                    full retro, last 20 sessions
/retrospect:retrospect 30d                   full retro, last 30 days
/retrospect:retrospect all                   full retro, every transcript
/retrospect:retrospect folder structure      targeted: everything you said about a topic
/retrospect:retrospect 30d naming rules      targeted, last 30 days
```

Targeted mode hunts one specific, recurring instruction across your history:
it shortlists sessions by grep, mines only those, and reports a dated timeline
of every statement you made about the topic, the current effective version,
and Claude's compliance — with a consolidated rule proposal when it recurs.

Longer transcript retention means more material: raise `cleanupPeriodDays` in
`~/.claude/settings.json`.

## How it was built

TDD for documentation. A baseline (no-skill) agent ran first: it located the
transcripts and filtered well, but did everything in one context (~9 minutes,
sequential, a hard ceiling at real session counts), never judged whether
corrections were complied with, and improvised its output shape. The skill
targets exactly those gaps. In the GREEN pass, two miners ran in parallel on
real 631KB and 2.7MB transcripts: both returned contract-valid JSON, every
spot-checked quote matched the raw file verbatim, and one miner correctly
recovered a session that had relocated into a worktree project folder
mid-test — behavior the agent definition now encodes.
