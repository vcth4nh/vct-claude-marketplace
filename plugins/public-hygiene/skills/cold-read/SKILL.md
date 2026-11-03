---
name: cold-read
description: Use when audience-facing text is about to go out (before any publish, submit, release, tag, push, or presentation of slides, talk scripts, papers, READMEs, docs, blog posts, release notes, PR descriptions, or commit messages), after a slide deck or talk draft is written, or when the user says "cold read", "audience check", or "will readers follow this", or asks whether outsiders will understand a text.
---

# Cold Read

Check audience-facing text for spans that its target audience cannot
resolve. Each context finding is a question, because only the author has
the missing facts. Optional modes also test comprehension or record a
reader's experience in order.

## Workflow

1. Read the [audience rules](../../references/audience-rules.md), resolving
   the link relative to this file. If the input is empty or the draft
   path does not exist, ask for the text or path.
2. Detect the type (rule 7). Use the ordinary context audit unless the user
   requests `comprehension` or `sequential` reading. For either mode, read
   [reader modes](../../references/reader-modes.md) for preparation,
   handoff, and reporting. The modes may be combined; both require a
   fresh reviewer even for a short fragment.
3. Collect the companions. For slides, embedded speaker notes are the
   script (marp/HTML comments, reveal.js notes, beamer `\note{}`). An
   external script counts when the user names it or the deck links it.
   Mode words precede the draft argument; every path after the draft path
   is a companion.
   For a review of a particular commit or PR, collect its exact diff as
   text or a read-only file, plus relevant metadata quoted verbatim from
   the publication surface or the user's supplied text.
   If the target change is unclear, ask which change to review; do not
   substitute an unrelated working-tree diff.
4. For a requested mode, follow its fresh-reviewer procedure. Otherwise
   route by stakes. For slides and talk scripts, papers, READMEs and docs,
   blog posts, release notes, and PR descriptions, send the whole document
   at any length to a fresh, read-only subagent reviewer using the
   [reader instructions](../../agents/cold-reader.md), without inherited
   conversation. A commit message, or a fragment of any class (a paragraph
   or less, not a whole document), gets an inline pass unless an optional
   mode was requested. For the inline pass, skip the terms in
   `.agents/leak-glossary.md` (falling back to `.claude/leak-glossary.md`)
   if it exists, apply the rules as the reader they describe, and report
   in the format below. Without a glossary, audit normally and make no
   offer to create one.
   If a fresh reviewer cannot run, report the independent check as
   incomplete instead of issuing a PASS or silently substituting an inline
   review.
5. Clean handoff. The dispatch carries the absolute reader instruction-file
   path (not just an agent type or a paraphrase of its rules),
   the draft (path or pasted text), the companions (paths or quoted public
   text, including the diff), the detected
   type in one line (slide or doc), and the user's own words about the
   audience or venue. Leave out
   the author's notes and their paths, glossary meanings, your
   explanations, and any audience profile that the user did not give,
   because they carry internal context into the fresh reader.
   Sequential mode sends one chunk at a time and waits for each returned
   checkpoint. Follow reader modes instead of sending the full draft,
   its path, or the complete chunk manifest to the reviewer.
   Include the requested mode and, for comprehension, the user's questions
   verbatim when supplied; never include an expected-answer key.
6. Relay the agent's report verbatim, with its VERDICT line and any
   requested mode's readback or first-read record. Add no
   answers, guesses, or context questions of your own, even about code
   blocks.
7. Apply. Send the report, then wait: before the author answers, change
   no file and write no corrected draft. On "apply" after the answers,
   insert only the facts that the answers state, at the flagged span or
   at the place RESOLVE names (the slide text, or the script at or before
   slide N), and change nothing else. An answer can also be "cut it".
   Leave unanswered gaps unchanged and list them as open. If the author
   cannot answer, leave the span for the author to keep or cut. Never
   invent. A comprehension readback is the reviewer's interpretation,
   never an author answer or permission to edit.

## Report format

```
AUDIENCE: <inferred reader, one line>
N. QUOTE:    `exact span from the text`
   CATEGORY: term | number | referent | attribution | other
   QUESTION: the question this audience would ask
   RESOLVE:  on the slide | in the script by slide N
```

`RESOLVE` appears only for the slide type. The inline pass ends with
`N context gaps` (`1 context gap` for one) or `No context gaps found.`,
with nothing else in the report.

## Modes

| Invocation | Behavior |
|---|---|
| `cold-read <text>` | audit, report questions |
| `cold-read <file>` | Read the file, then audit |
| `cold-read <file> <companion>...` | each path after the first is a companion (a script, a named doc) |
| `cold-read comprehension <text or file>` | context audit plus source-backed answers and, where applicable, the requested action |
| `cold-read sequential <text or file>` | experimental context audit in ordered chunks, recording gaps before reading on |
| "apply" after answers | insert only facts the answers state |

## Harness notes

- **Claude Code:** invoke `/public-hygiene:cold-read`; use the bundled
  `cold-reader` agent for subagent reviews.
- **Codex:** invoke `$public-hygiene:cold-read`; start a fresh subagent
  with the linked reader instructions.

## Ordering

Run `cold-read` first, because the answers add text that the later
gates must see. Style passes (`deslop`, `academic-voice`) run next,
and `leak-check` runs last, on the final text.
