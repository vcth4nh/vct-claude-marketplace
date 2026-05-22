---
description: Show recent claude-auto-retry events and pending retry timers. Use when the user asks "what's pending", "did my retry fire", "show auto-retry log", "claude-auto-retry status", or invokes /claude-auto-retry:status.
argument-hint: ""
allowed-tools: [Bash]
---

# claude-auto-retry status

Run this command and show the raw output verbatim:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/hooks/auto_retry.py --status
```

If the command exits non-zero, report the exit code and any stderr — do not
re-render or interpret. The output is two tables (PENDING and RECENT) already
formatted for terminal display.
