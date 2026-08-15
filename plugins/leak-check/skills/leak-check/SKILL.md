---
name: leak-check
description: Use when text is about to go public — before any publish, submit, release, tag, or push of papers, abstracts, camera-ready text, READMEs, release notes, commit messages, PR descriptions, or blog posts — or when the user says "leak check", "check for leaks", "sanitize", "is this safe to publish". Also use before finalizing any text written for an external audience.
---

# Leak Check

Audit text for internal-context leaks before it goes public. Report first;
rewrite only on request. Never end a turn by silently emitting text that
failed the audit.

## Workflow

1. Read `${CLAUDE_PLUGIN_ROOT}/references/hygiene-rules.md`.
2. Read `.claude/leak-glossary.md` in this repo if it exists. Terms in its
   internal column are leaks by definition, wherever they appear.
   - No glossary → still audit every generic category, then offer once to
     create the file from the template below. Do not block on the offer.
3. Route by stakes:
   - **High-stakes** (paper prose, release notes, public PR descriptions,
     blog posts): launch the `external-reviewer` agent with the draft or its
     file path. Relay its findings and verdict verbatim. Never audit
     high-stakes text inline — a context saturated with internal terms is
     exactly what stops seeing them.
   - **Routine** (commit messages, README fragments, short snippets): audit
     inline. Read the text as an external reader with no access to this
     team's infrastructure, chat history, or trackers. Flag every span that
     reader could not resolve or should not see — novel leak classes
     included. A codename is still a leak even when it reads as an ordinary
     word or matches nothing you recognize — do not exempt it for sounding
     plausible.
4. Report in the format below.
5. On "fix" or "apply": emit the corrected text, changing only flagged
   spans. Replacements come from the glossary or by generalizing — never
   invent facts, names, numbers, or citations to fill a redaction.
6. A term whose public status is unclear → ask the user. Never guess.

## Report format

```
N. QUOTE:    `exact span from the text`
   CATEGORY: path | run-id | infra | provenance | dev-log | jargon | meta | other
   FIX:      proposed replacement, or "delete"
```

End with `N findings` or `No leaks found.` — nothing else.

## Hard limits

- Check the first line of the input against the meta category before
  auditing anything else — scaffolding like "Here is the..." sits there
  and is easy to read past.
- An unfamiliar term that recurs in a URL, a path, and plain prose (such
  as a subject line) is a project codename — give every plain-prose
  occurrence its own jargon finding, glossary or not.

## Modes

| Invocation | Behavior |
|---|---|
| `/leak-check <text>` | audit, then offer to apply fixes |
| `/leak-check fix <text>` | audit and emit sanitized text in one pass (report first) |
| `/leak-check <file path>` | Read the file, then audit as above |

## Ordering

Run on final text only. Style passes (`deslop`, `academic-voice`) rewrite
sentences — they run before this gate, never after it.

## Glossary template (`.claude/leak-glossary.md`)

````markdown
# Leak glossary (internal -> public)
# Read by the leak-check plugin. Internal-column terms are leaks by definition.

| Internal term | Public replacement |
|---|---|
| <codename>    | <public name>      |

## Never public (omit entirely, no replacement)
- <hostname, bucket, ticket prefix, ...>
````
