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
- **`external-reviewer` agent** — a fresh-context, read-only reviewer for
  high-stakes text (papers, release notes, public PR descriptions, blog
  posts). Its ignorance is the mechanism: what it cannot resolve, the
  public cannot resolve. Returns quoted findings and a BLOCK/PASS verdict;
  ambiguous terms come back as questions, never guesses.

## Install

```
/plugin marketplace add vcth4nh/vct-claude-marketplace-public
/plugin install public-hygiene@vct-public
```

The bare forms `/leak-check` and `/cold-read` work, and so do the
namespaced forms `/public-hygiene:leak-check` and
`/public-hygiene:cold-read`.

## leak-check

```text
Leak check this commit message: <paste>
/leak-check fix <paste>              # audit + sanitized text in one pass
/leak-check paper/intro.tex          # high-stakes → external reviewer
Is this changelog safe to publish?
```

Claude also runs the audit on its own before it publishes, submits, tags,
or pushes public-facing text.

## Per-repo glossary (recommended)

Create `.claude/leak-glossary.md` (the `leak-check` skill offers to
scaffold it, and `cold-read` does not):

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
fresh-context `cold-reader` agent, which sees only the text the audience
sees. Commit messages and short fragments get an inline pass. The report
names the audience the check assumed, so you can correct it.

```text
/cold-read talk/deck.md
/cold-read talk/slides.tex talk/script.md   # deck plus script
/cold-read README.md
Will readers follow this release note? <paste>
```

Claude also runs the check on its own before it publishes, submits, tags,
or pushes audience-facing text.

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
