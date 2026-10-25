# codex-exec

Use OpenAI Codex from Claude Code as a **discussion peer**: get an independent
second opinion, push back, iterate — and delegate whole tasks only when you ask
for it or Claude genuinely trusts Codex with them.

One skill. No scripts, no hooks, no broker process, no state files. If you want
managed background jobs, native review commands, or session transfer, use
[OpenAI's official plugin](https://github.com/openai/codex-plugin-cc) instead —
this is the lightweight alternative for people who just want `codex exec` used
*well*.

## What the skill encodes

- **Discussion first.** New topic → `codex exec`; every follow-up on that topic
  → `codex exec resume <session-id>` so Codex keeps its context. Codex's
  verdict is quoted verbatim, then Claude gives its own take. Discussion
  prompts explicitly prohibit file or external-state changes.
- **Folder-aware sessions.** Codex runs from the folder each topic is about —
  usually the repo root, a subfolder or elsewhere when that fits better — with
  `--skip-git-repo-check` added in non-Git folders.
- **Default flags only.** No `-s/--sandbox`, `--full-auto`, `--cd`, or model
  overrides — Codex's configuration and built-in defaults govern. Explicit
  sandbox flags can fail under nested sandboxing, and `-s` isn't accepted by
  `resume`.
- **Background execution.** Long runs go in the background with a per-topic
  `-o` file; its exit status and non-empty contents are checked before Claude
  quotes it, so a failed or empty run is reported, never a stale file.
- **Preflight once per session** (`codex login status`) with fix suggestions,
  never auto-install.
- **Delegation hygiene.** After Codex edits files, changes are verified with
  `git status` + `git diff` and a quick test — never just Codex's prose
  summary. In non-Git folders, file contents are noted before and compared
  after.

## Install

```bash
/plugin marketplace add vcth4nh/vct-claude-marketplace
/plugin install codex-exec@vct-public
```

## Requirements

- [Codex CLI](https://developers.openai.com/codex/cli/) (`npm install -g @openai/codex`), logged in (`codex login`)
- Usage counts toward your ChatGPT plan's Codex limits or API billing

## Usage

No commands to learn — just talk:

```text
Ask codex whether this retry design is sound.
Tell codex I disagree — the caller can't act on failures anyway.
Have codex fix the parser bug directly, I trust it with small stuff.
```

Claude also consults Codex on its own when it's stuck after repeated failed
attempts or about to commit to a risky approach (announced first, never
silent).

## How it was built

TDD for documentation: 7 baseline (no-skill) agent runs were recorded first —
7/7 invented sandbox flags and every one broke or degraded the run, 0 checked
login state, 0 used background execution. The skill targets exactly those
failures; with it present, follow-up runs passed every dimension.
