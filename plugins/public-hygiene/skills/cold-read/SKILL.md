---
name: cold-read
description: Use when audience-facing text is about to go out (before any publish, submit, release, tag, push, or presentation of slides, talk scripts, papers, READMEs, docs, blog posts, release notes, PR descriptions, or commit messages), after a slide deck or talk draft is written, or when the user says "cold read", "audience check", or "will readers follow this", or asks whether outsiders will understand a text.
---

# Cold Read

Check audience-facing text for spans that its target audience cannot
resolve. Each finding is a question, because only the author has the
missing facts.

## Workflow

1. Read `${CLAUDE_PLUGIN_ROOT}/references/audience-rules.md`. If the
   input is empty or the draft path does not exist, ask for the text or
   path.
2. Detect the type (rule 7).
3. Collect the companions. For slides, embedded speaker notes are the
   script (marp/HTML comments, reveal.js notes, beamer `\note{}`). An
   external script counts when the user names it or the deck links it.
   Every path after the first in the invocation is a companion.
4. Route by stakes. Send a whole document of these classes to the
   `cold-reader` agent at any length: slides and talk scripts, papers,
   READMEs and docs, blog posts, release notes, and PR descriptions. A
   commit message, or a fragment of any class (a paragraph or less, not a
   whole document), gets an inline pass: skip the terms in
   `.claude/leak-glossary.md` if it exists, apply the rules as the reader
   they describe, and report in the format below. Without a glossary,
   audit normally and make no offer to create one.
5. Clean handoff. The dispatch carries only the draft (path or pasted
   text), the companion paths, the detected type in one line (slide or
   doc), and the user's own words about the audience or venue. Leave out
   the author's notes and their paths, glossary meanings, your
   explanations, and any audience profile that the user did not give,
   because they carry internal context into the fresh reader.
6. Relay the agent's report verbatim, with its VERDICT line, as the
   whole context audit, and add no answers or guesses of your own.
7. Apply. Send the report, then wait: before the author answers, change
   no file and write no corrected draft. On "apply" after the answers,
   insert only the facts that the answers state, at the flagged span or
   at the place RESOLVE names (the slide text, or the script at or before
   slide N), and change nothing else. An answer can also be "cut it".
   Leave unanswered gaps unchanged and list them as open. If the author
   cannot answer, leave the span for the author to keep or cut. Never
   invent.

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
| `/cold-read <text>` | audit, report questions |
| `/cold-read <file>` | Read the file, then audit |
| `/cold-read <file> <companion>...` | each path after the first is a companion (a script, a named doc) |
| "apply" after answers | insert only facts the answers state |

## Ordering

Run `cold-read` first, because the answers add text that the later
gates must see. Style passes (`deslop`, `academic-voice`) run next,
and `leak-check` runs last, on the final text.
