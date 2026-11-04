# vct-claude-marketplace

Public agent skills and plugins by [@vcth4nh](https://github.com/vcth4nh).

## Install

Claude Code:

```
/plugin marketplace add vcth4nh/vct-claude-marketplace
/plugin install <plugin-name>@vct-public
```

Codex:

```bash
codex plugin marketplace add vcth4nh/vct-claude-marketplace
codex plugin add anti-slop@vct-public
codex plugin add public-hygiene@vct-public
```

Start a new session after installation. `anti-slop` and `public-hygiene`
share harness-agnostic instructions with brief Claude Code and Codex notes
in each skill. `codex-exec` and `retrospect` remain Claude Code workflows.

Claude Code invokes skills with `/plugin-name:skill-name`; Codex uses
`$plugin-name:skill-name`. Natural-language requests work in either.

## Plugins

| Plugin | Version | Description |
|---|---|---|
| [`codex-exec`](plugins/codex-exec/) | 0.1.0 | Consult Codex as a discussion peer with safe, folder-aware multi-turn execution and delegation checks. |
| [`anti-slop`](plugins/anti-slop/) | 0.3.3 | Remove AI-slop tone from prose with `deslop` (engineering) and `academic-voice` (papers). Supports standalone rewrites, file edits, and use within drafting tasks; includes a Claude Code-only ASD-STE100 output style. |
| [`public-hygiene`](plugins/public-hygiene/) | 0.4.1 | Check public-facing text: `leak-check` finds internal-context leaks, and `cold-read` finds missing context, with optional comprehension testing and experimental sequential reading. |
| [`retrospect`](plugins/retrospect/) | 0.3.0 | Mine past session transcripts with parallel per-project miners: corrections → approval-gated CLAUDE.md rules, plus failure patterns, friction, and wins; topic and project scoping. |
