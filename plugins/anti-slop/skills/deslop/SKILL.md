---
name: deslop
description: Use when writing, editing, or polishing engineering prose for a human reader (READMEs, docs, reports, write-ups, commit messages, PR descriptions, release notes, blog posts), or when the user says "deslop", "remove AI slop", "sounds like AI", "make this sound human", or "fix the tone".
---

# Deslop

Rewrite engineering prose so a careful human could have written it. Audit
against the ban list, rewrite, report what changed.

Resolve bundled links relative to this file's directory.

## Workflow

1. Read the [ban list](../../references/ban-list.md).
2. Audit the input: collect every violation as `span` + pattern class.
   Check every heading line and every `—`.
3. Rewrite. Change only what a ban or the replacement principle requires.
4. Output, in this order:
   1. The rewritten text, ready to paste.
   2. `Changes:` — one line per violation: `` `span` `` → `` `replacement` ``
      (or "cut").

If the text is already clean, output `Clean, no slop found.` and stop.

## Modes

| Invocation | Behavior |
|---|---|
| `deslop <text>` | audit + rewrite (default) |
| `deslop check <text>` | violation list only, no rewrite |
| `deslop <file path>` | Read the file, then proceed as above |

Claude Code: `/anti-slop:deslop`. Codex: `$anti-slop:deslop`.

## Hard constraints

- Preserve meaning and facts. Never add facts, numbers, names, or claims.
- Code blocks, commands, sample output, and quoted material stay
  byte-identical.
- The rewrite must not be longer than the original. Cutting beats rephrasing.
- Keep the author's technical terms. Replace slop, not vocabulary you would
  merely phrase differently.
- A contrast reveal ("It's not X. It's Y.") never confirms X. When cutting
  it, keep only the concrete claim both clauses share — do not assert X.

## Ordering

Style before gate: if the `public-hygiene` plugin is installed, it runs after
this skill, on the final text — never before.
