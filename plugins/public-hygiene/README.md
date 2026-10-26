# public-hygiene

Two checks for public-facing text before it ships:

- `leak-check` audits internal-context leaks: local paths, run/experiment
  IDs, infra names, ticket IDs, private provenance, dev-log narrative,
  unexpanded jargon, AI scaffolding.
- `cold-read` finds context the audience lacks. See [cold-read](#cold-read).

`leak-check` has two layers:

- **`leak-check` skill** — inline audit for routine text (commit messages,
  README fragments). Quotes every offending span, names the category,
  proposes a fix. Applies fixes only on request; never invents facts to
  fill a redaction.
- **Fresh subagent reviewer** — a read-only reviewer for
  high-stakes text (papers, release notes, public PR descriptions, blog
  posts). Its ignorance is the mechanism: what it cannot resolve, the
  public cannot resolve. Returns quoted findings and a BLOCK/PASS verdict;
  ambiguous terms come back as questions, never guesses.

## Install

Claude Code:

```
/plugin marketplace add vcth4nh/vct-claude-marketplace
/plugin install public-hygiene@vct-public
```

Codex:

```bash
codex plugin marketplace add vcth4nh/vct-claude-marketplace
codex plugin add public-hygiene@vct-public
```

Start a new session after installation. Both harnesses use the same
skills, rules, and reviewer instructions.

## Harness notes

- **Claude Code:** invoke `/public-hygiene:leak-check` or
  `/public-hygiene:cold-read`. The bundled `external-reviewer` and
  `cold-reader` agents provide the fresh reviews.
- **Codex:** invoke `$public-hygiene:leak-check` or
  `$public-hygiene:cold-read`. The skills link the instructions for a
  fresh subagent to read, without inheriting the conversation.

## leak-check

```text
Leak check this commit message: <paste>
Leak check and fix this text: <paste>
Leak check paper/intro.tex          # high-stakes → fresh subagent reviewer
Is this changelog safe to publish?
```

The skill also applies before publishing, submitting, tagging, or pushing
public-facing text.

## Per-repo glossary (recommended)

Create `.agents/leak-glossary.md` (the `leak-check` skill offers to
scaffold it, and `cold-read` does not). Both skills fall back to an
existing `.claude/leak-glossary.md`:

```markdown
| Internal term | Public replacement |
|---|---|
| hydra         | the retrieval service |

## Never public (omit entirely, no replacement)
- gpu-node-07
```

Internal-column terms are leaks by definition. Without the file, the
`leak-check` audit still covers the generic categories. `cold-read` skips
the terms in this file, because `leak-check` handles them.

## cold-read

`leak-check` asks whether the audience may see a span. `cold-read` asks
whether the audience can understand it. It reads the text as its target
audience would, with only the text they can reach, and quotes each span
they could not resolve: a term nobody introduced, a number without its
base, a "we" or "the tool" with no clear referent, a quote with no source.
Each finding is a question for you, because only the author knows the
missing fact. When you answer and say "apply", it inserts your answers and
invents nothing.

Slides and documents get different standards:

- **Documents** must stand alone or resolve through the documents they
  link or name. The check reads those documents before it flags a term.
- **Slides** may leave facts to the speaker. A gap is fine when your script
  covers it by that slide: speaker notes in the deck, or a script file you
  name. A slide that misleads on its own, such as a "we" that reads as your
  team when you mean the whole industry, must change on the slide.

The type comes from the file and your request. High-stakes text goes to a
fresh subagent reviewer, which sees only the text the audience
sees. Commit messages and short fragments get an inline pass. The report
names the audience the check assumed, so you can correct it.

```text
Cold read talk/deck.md
Cold read talk/slides.tex talk/script.md   # deck plus script
Cold read README.md
Will readers follow this release note? <paste>
```

The skill also applies before publishing, submitting, tagging, or pushing
audience-facing text.

## Pipeline order

Context first, style next, leaks last:

```text
cold-read -> answer its questions, apply -> deslop / academic-voice -> leak-check -> publish
```

`cold-read` adds text from your answers, so the later passes must see it.
Style passes ([`anti-slop`](../anti-slop/)) rewrite sentences, so the leak
audit runs on the final text, never before a rewrite.

## Scope

Context leaks and missing context, not credentials. For actual secrets
(keys, tokens), run [gitleaks](https://github.com/gitleaks/gitleaks) or
equivalent in CI. Never leave credentials to an LLM. Neither skill has a
deterministic hook floor yet; a commit-message denylist hook is planned
future work.
