# vct-claude-marketplace-public

Public Claude Code plugins by [@vcth4nh](https://github.com/vcth4nh).

## Install

```
/plugin marketplace add vcth4nh/vct-claude-marketplace-public
/plugin install <plugin-name>@vct-public
```

## Plugins

| Plugin | Version | Description |
|---|---|---|
| [`codex-exec`](plugins/codex-exec/) | 0.1.0 | Consult Codex as a discussion peer with safe, folder-aware multi-turn execution and delegation checks. |
| [`anti-slop`](plugins/anti-slop/) | 0.2.0 | Remove AI-slop tone from prose: `deslop` (engineering) + `academic-voice` (papers), plus an opt-in ASD-STE100 output style. |
| [`public-hygiene`](plugins/public-hygiene/) | 0.2.0 | Check public-facing text before it ships: `leak-check` finds internal-context leaks (BLOCK/PASS), and `cold-read` finds context the audience lacks (NEEDS CONTEXT/PASS). |
| [`retrospect`](plugins/retrospect/) | 0.3.0 | Mine past session transcripts with parallel per-project miners: corrections → approval-gated CLAUDE.md rules, plus failure patterns, friction, and wins; topic and project scoping. |
