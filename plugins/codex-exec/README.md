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
  verdict is quoted verbatim, then Claude gives its own take.
- **Default flags only.** No `-s/--sandbox`, `--full-auto`, `--cd`, or model
  overrides — your `~/.codex/config.toml` governs. Tested finding: unprompted
  sandbox flags *broke every single baseline run* on a containerized machine
  (Codex's bubblewrap sandbox can't nest), and `-s` doesn't exist on `resume`.
- **Background execution** with `-o <file>` output capture — Codex runs take
  minutes; foreground runs blow Bash's 2-minute default timeout.
- **Preflight once per session** (`codex login status`) with fix suggestions,
  never auto-install.
- **Delegation hygiene.** When Codex edits files, the result is verified with
  `git diff` and a quick test — never its prose summary.

## Install

```bash
/plugin marketplace add vcth4nh/vct-claude-marketplace-public
/plugin install codex-exec@vct-public
```

## Requirements

- [Codex CLI](https://developers.openai.com/codex/cli/) (`npm install -g @openai/codex`), logged in (`codex login`)
- Codex usage is billed to your ChatGPT plan / OpenAI API key

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
failures; with it present, follow-up runs passed every dimension. Scenarios and
verbatim results live in the design spec history.
