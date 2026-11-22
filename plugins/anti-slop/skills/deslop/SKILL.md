---
name: deslop
description: Use when the task calls for drafting or revising technical prose for readers, such as a design note, customer incident update, README, or commit message. Also use when the user says "deslop", "remove AI slop", "sounds like AI", "make this sound human", or "fix the tone".
---

# Deslop

Rewrite engineering prose so a careful human could have written it. Audit
against the ban list and make the necessary edits.

Resolve bundled links relative to this file's directory.

## Workflow

1. Read the [ban list](../../references/ban-list.md).
2. Audit prose only, outside the protected spans listed below: collect
   every violation as `span` + pattern class.
   Check every heading line, every `—`, and every mid-sentence colon.
   Also check for dramatic framing, personification of tools or systems,
   and story-like headings, even when none of their words appear in the
   vocabulary ban.
3. Rewrite. Change only what a ban or the replacement principle requires.
   Compare the result with the source for lost facts, negations, and
   conditions as well as unsupported additions. Check for excessive
   editing as described in the replacement principle.
4. Return the result according to the mode below.

When revising a draft that has already had a style pass, check the changed
passages in context. Reread any other passage whose meaning the edit affects.
Reuse the completed pass wherever the wording and context stay the same,
including when a draft is committed or published. Run a fresh pass on request.

## Modes

| Request | Behavior |
|---|---|
| `deslop <text>` or `deslop <file path>` | Read and rewrite; return the text followed by `Changes:` with one line per edit: `` `span` `` → `` `replacement` `` (or "cut"). If clean, return `Clean, no slop found.` |
| `deslop check <text or file path>`, or a review-only request | Report violations and suggested fixes only; do not rewrite or change files. If clean, return `Clean, no slop found.` |
| Explicitly edit or update a file | Apply prose edits to that file, then briefly summarize them. Do not write the change report into the file. Leave a clean file untouched and report that result. |
| Used within another drafting task, such as a customer incident update or commit message | Return only the draft in its intended format. Leave plain-text messages unfenced. Omit prefaces, audit notes, `Changes:`, clean-status messages, and follow-up offers even when the draft needs no edits. |

Choose the mode from the user's request. Naming a path alone reads the file;
an explicit request to edit it authorizes the write. A review-only request
takes precedence over the default rewrite behavior.

Claude Code: `/anti-slop:deslop`. Codex: `$anti-slop:deslop`.

## Hard constraints

- Preserve meaning and facts. Never add facts, numbers, names, or claims.
- Edit prose only. Code blocks, inline code, commands, sample output,
  quoted material, paths, YAML metadata, data, and link targets stay
  byte-identical. Check these protected spans against the source before
  returning or saving an edit.
- The rewrite must not be longer than the original, except for words
  needed to move factual heading content into a grammatical body sentence.
- Keep the author's technical terms. Replace slop, not vocabulary you would
  merely phrase differently.
- When removing rhetorical contrast, keep the concrete behavior and any
  factual limitations. A denied or minimized label in the reveal is not
  a new fact to assert or a function to infer. Use it as a positive claim
  only when the source states that claim independently of the reveal.

## Ordering

When using `public-hygiene`, run `cold-read` and apply the author's
answers before this style pass. Run `leak-check` after this pass, on the
final text. If later edits add or change prose, repeat the affected checks.
