# public-hygiene

Two checks for public-facing text before it ships:

- `leak-check` audits internal-context leaks: local paths, run/experiment
  IDs, infra names, ticket IDs, private provenance, private working notes,
  unexpanded jargon, AI scaffolding.
- `cold-read` finds context the audience lacks. See [cold-read](#cold-read).

`leak-check` has two layers:

- **`leak-check` skill** — inline audit for routine text (commit messages,
  README fragments). Quotes every offending span, names the category,
  proposes a fix. Applies fixes only on request; never invents facts to
  fill a redaction.
- **Fresh subagent reviewer** — a reviewer that keeps the draft read-only for
  high-stakes text (papers, release notes, public PR descriptions, blog
  posts, whole READMEs and docs, slides and talk scripts). It uses the
  audience's field knowledge without private project context.
  Returns quoted findings and a BLOCK/PASS verdict;
  ambiguous terms come back as questions, never guesses.

Independent reviews are saved to temporary report files outside the source
tree. The response links the report and shows its verdict, preserving the
reviewer's quotes and findings. Reviewers may write only their designated
report; supplied drafts and companions are checked for changes. The harness
must permit that temporary write, which may require its normal permission
prompt or a writable scratch directory. A denied write leaves the check
incomplete. Reports can contain private spans: keep them out of source control.

Deliberate public history and design rationale are reviewed for concrete
disclosures. A genre label or prior publication does not exempt private
paths, infrastructure, glossary terms, or anonymity constraints.

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

On Claude Code 2.1.271 or later, the bundled reviewers use `omitClaudeMd`
to exclude initial user, project, and local instructions. This limits
context carryover; it is not a sandbox. Managed policy and path-scoped
instructions can still load. Reviewers must not use private definitions
as evidence of what the audience knows. On either harness, an unavailable
fresh reviewer leaves the independent check incomplete.

## leak-check

```text
Leak check this commit message: <paste>
Leak check and fix this text: <paste>
Leak check paper/intro.tex          # high-stakes → fresh subagent reviewer
Is this changelog safe to publish?
```

The skill also applies before publishing, submitting, tagging, or pushing
public-facing text.

The reviewer receives any venue, anonymity requirements, and public-name
approvals you state, so those constraints survive the fresh handoff.

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
fresh subagent reviewer with a limited handoff of audience-reachable text
and your stated constraints. Commit messages and short fragments get an
inline pass. The report names the audience the check assumed, so you can
correct it.

For a particular commit or PR, the handoff includes its exact diff and
relevant metadata visible to readers. If the target change is unclear,
the skill asks which change to review.

```text
Cold read talk/deck.md
Cold read talk/slides.tex talk/script.md   # deck plus script
Cold read README.md
Will readers follow this release note? <paste>
cold-read comprehension proposal.md
cold-read sequential guide.md             # experimental, text/Markdown
```

The skill also applies before publishing, submitting, tagging, or pushing
audience-facing text.

Two additional modes run only when requested:

- **Comprehension** adds a readback: the requested action when the document
  calls for one, and answers to your questions or a few questions about its
  main claims. Each answer cites the supporting passage. Ambiguous answers
  become context questions; informational text needs no call to action.
  The readback demonstrates an interpretation, not factual verification.
  It cannot supply the author answers required before applying a correction.
- **Sequential** is experimental. A fresh reviewer reads ordered text
  chunks, returning a first-read report before receiving the next chunk.
  A later definition
  cannot erase a first-use gap unless the text explicitly pointed to it.
  Slides retain their same-slide notes and script timing. Preparation uses
  a Python 3 helper to create temporary verbatim copies and leaves the
  source untouched. Each stage saves a checkpoint before the next is supplied;
  a second helper assembles those records without rewriting them. A missing
  chunk or unavailable independent reader leaves the check incomplete.

Both modes require a fresh reviewer, including for short inputs. They may
be combined. Sequential reading adds tool calls; testing has not established
a reliability advantage over the ordinary audit. Its read trace must be checked to
verify that the reviewer followed the sequence. See the
[mode procedures](references/reader-modes.md) for supported inputs and
forward-reference handling.

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
rule-based commit hook yet; a commit-message denylist hook is planned.

## Related reader workflows

- [Anthropic's doc-coauthoring](https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring)
  supplies the reader-answer testing idea used in comprehension mode.
- [cold-read-gate](https://github.com/laurigates/claude-plugins/tree/main/agent-patterns-plugin/skills/cold-read-gate)
  motivates the requested-action check and publication-surface context.
- [cold-reader-skill](https://github.com/brendanlong/cold-reader-skill)
  motivates sequential exposure and recorded first-read observations.

These are related approaches, not dependencies. This plugin keeps separate
leak and context checks, slide/script timing rules, and corrections drawn
only from the author's answers.
