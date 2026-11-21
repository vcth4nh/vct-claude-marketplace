---
name: leak-check
description: Check the final wording for information that should stay private before it reaches an external audience. Examples include a customer email, a conference talk, and a public GitHub issue. Also use when asked to check text for leaks, sanitize it for publication, or assess whether it is safe to share.
---

# Leak Check

Audit text for internal-context leaks before sharing it outside the team. Report first;
rewrite only on request. Never end a turn by silently emitting text that
failed the audit.

## Workflow

1. Read the [hygiene rules](../../references/hygiene-rules.md), resolving
   the link relative to this file.
2. Read `.agents/leak-glossary.md` in this repo if it exists, falling back
   to `.claude/leak-glossary.md`. Terms in its internal column are leaks
   by definition, wherever they appear.
   - No glossary → still audit every generic category, then offer once to
     create the file from the template below. Do not block on the offer.
3. If a prior leak check [still applies](../../references/report-delivery.md#reusing-a-review), reuse its result.
   Route a new review by stakes.
   - For **high-stakes text**, launch a fresh subagent reviewer. This includes
     paper prose, release notes, public GitHub issues and PR descriptions,
     blog posts, whole READMEs and docs, slides and talk scripts, and messages
     that contain information restricted to particular recipients. Use the
     [reviewer instructions](../../agents/external-reviewer.md). Pass it
     the absolute instruction-file path (not just an agent type or a
     paraphrase of its rules), the draft or its file path, and the
     new absolute report output path, and the user's own words about the
     audience, venue, anonymity requirements, and names approved for that
     audience. Leave out your explanations and private
     background, and do not inherit the conversation. Follow
     [report delivery](../../references/report-delivery.md): the draft stays
     read-only; the reviewer may write only its designated temporary report.
     Choose the reviewer model and effort using
     [reviewer selection](../../references/reviewer-models.md), preserving
     explicit user choices and fresh context.
     Verify the saved report and unchanged inputs, then return a link and
     its exact verdict line without restating the findings.
     Never audit high-stakes text inline — a context saturated with
     internal terms is exactly what stops seeing them.
     If a fresh reviewer cannot run, report the independent check as
     incomplete instead of issuing a PASS.
   - **Routine** (commit messages, README fragments, short snippets): audit
     inline. Read the text as an external reader with no access to this
     team's infrastructure, chat history, or trackers. Apply the hygiene
     rules' evidence test, including to novel leak classes. An explicitly
     private codename remains a leak even when its spelling looks ordinary;
     unfamiliarity or absent separate approval alone does not make a name
     private.
4. For an inline audit, report in the format below. A subagent review keeps
   the reviewer's findings and verdict format.
5. On "fix" or "apply": reread a delegated review's saved report, then
   emit the corrected text, changing only flagged
   spans. Replacements come from the glossary or by generalizing — never
   invent facts, names, numbers, or citations to fill a redaction.
6. A supported disclosure concern whose intended publication is unclear
   needs the user's answer. For an inline audit, ask the user. In a
   delegated review, the question belongs
   in the saved report; do not repeat it in the delivery message. Before
   applying a requested fix, ask for any answers still missing. Never guess.

## Report format

```
N. QUOTE:    `exact span from the text`
   CATEGORY: path | run-id | infra | provenance | dev-log | jargon | meta | other
   FIX:      proposed replacement, or "delete"
```

The inline report ends with `N findings` or `No leaks found.` — nothing
else in the report.

## Hard limits

- Check the first line of the input against the meta category before
  auditing anything else — scaffolding like "Here is the..." sits there
  and is easy to read past.
- A term recurring in a URL, a path, and prose warrants checking for an
  internal codename; repetition alone does not establish private status.
  Apply the hygiene rules' installation-identifier exception and any
  explicit glossary or publication constraints.
- FIX text is assembled only from the glossary and from facts the
  source states — a role or characterization the source never states
  ("on-call", "default", "legacy", "temporary") is invention, even offered
  as an example.

## Modes

| Invocation | Behavior |
|---|---|
| `leak-check <text>` | audit, then offer to apply fixes |
| `leak-check fix <text>` | audit and emit sanitized text in one pass (report first) |
| `leak-check <file path>` | Read the file, then audit as above |

## Harness notes

- **Claude Code:** invoke `/public-hygiene:leak-check`; use the bundled
  `external-reviewer` agent for subagent reviews.
- **Codex:** invoke `$public-hygiene:leak-check`; start a fresh subagent
  with the linked reviewer instructions.

## Ordering

Run on final text only. Style passes (`deslop`, `academic-voice`) rewrite
sentences — they run before this gate, never after it.

## Glossary template (`.agents/leak-glossary.md`)

````markdown
# Leak glossary (internal -> public)
# Read by the public-hygiene plugin. Internal-column terms are leaks by definition.

| Internal term | Public replacement |
|---|---|
| <codename>    | <public name>      |

## Never public (omit entirely, no replacement)
- <hostname, bucket, ticket prefix, ...>
````
