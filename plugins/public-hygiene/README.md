# public-hygiene

Audit public-facing text for internal-context leaks before it ships: local
paths, run/experiment IDs, infra names, ticket IDs, private provenance,
dev-log narrative, unexpanded jargon, AI scaffolding.

Two layers:

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

## Usage

```text
Leak check this commit message: <paste>
/leak-check fix <paste>              # audit + sanitized text in one pass
/leak-check paper/intro.tex          # high-stakes → external reviewer
Is this changelog safe to publish?
```

Claude also runs the audit on its own before it publishes, submits, tags,
or pushes public-facing text.

## Per-repo glossary (recommended)

Create `.claude/leak-glossary.md` — the skill offers to scaffold it:

```markdown
| Internal term | Public replacement |
|---|---|
| hydra         | the retrieval service |

## Never public (omit entirely, no replacement)
- gpu-node-07
```

Internal-column terms are leaks by definition. Without the file, the audit
still covers the generic categories.

## Pipeline order

Gate last: run style passes ([`anti-slop`](../anti-slop/)) first — this
audit runs on the final text, never before a rewrite.

## Scope

Context leaks, not credentials. For actual secrets (keys, tokens), run
[gitleaks](https://github.com/gitleaks/gitleaks) or equivalent in CI —
never leave credentials to an LLM. v1 has no deterministic hook floor; a
commit-message denylist hook is planned future work.
