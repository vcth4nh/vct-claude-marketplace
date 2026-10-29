---
name: academic-voice
description: Use when writing or editing paper prose — abstracts, introductions, methods, results, related work, camera-ready or rebuttal text, thesis chapters — or when the user says "humanize this paragraph", "make this read like a paper", or calls academic text AI-sounding.
---

# Academic Voice

Rewrite paper prose so it reads like a person wrote it: varied rhythm,
concrete subjects, claims sized to the evidence.

Resolve bundled links relative to this file's directory.

## Workflow

1. Read the [ban list](../../references/ban-list.md). Every ban applies to
   paper prose too.
2. Pick the voice source:
   - Use `.agents/writing-samples.md` in this repo, falling back to
     `.claude/writing-samples.md` if absent. Match its rhythm,
     sentence-length variation, and concreteness. Register, never phrases:
     copying a distinctive wording from the samples is a defect.
   - No samples file → use the built-in register below. In a standalone
     editing task, offer once after the rewrite to create
     `.agents/writing-samples.md` from the
     [template](../../references/writing-samples-template.md). Do not
     block on the offer or include it in a requested artifact.
3. Rewrite the prose. Compare it with the source for lost claims,
   negations, conditions, and citations as well as unsupported additions.
   Check for excessive editing as described in the replacement principle.
4. Return the result according to the mode below.

## Built-in register (fallback)

- Vary sentence length when it helps the argument; do not impose a fixed
  alternation of short and long sentences.
- Concrete subject + active verb: "the model overfits", not "overfitting is
  observed".
- One hedge per claim, sized to the evidence. Delete stacked qualifiers.
- No announced structure. The section speaks for itself.

## Hard constraints

- Never invent citations, numbers, results, baselines, or related work.
- Technical claims stay exact. Meaning outranks rhythm.
- Edit prose only. Math, LaTeX macros, `\cite`/`\ref` keys, tables, code,
  inline code, commands, sample output, quoted material, paths, YAML
  metadata, data, and link targets stay byte-identical. Check these
  protected spans against the source before returning or saving an edit.
- An announced-structure opener survives even with no banned words in it
  ("This section presents...", "This section gives..."). Cut it; open with
  the first concrete claim.
- Cutting banned words does not by itself repair monotonous rhythm. Check
  sentence length and shape after rewriting, while preserving clear cadence
  and useful explanation.

## Modes

| Request | Behavior |
|---|---|
| `academic-voice <text>` or `academic-voice <file path>` | Read and rewrite; return the text followed by `Changes:` with one line per edit: `` `span` `` → `` `replacement` ``. If unchanged, return the original text and say no edits were needed. |
| A review-only request | Report findings and suggested fixes without rewriting or changing files. |
| Explicitly edit or update a file | Apply prose edits to that file, then briefly summarize them. Do not write the change report into the file. Leave a clean file untouched and report that result. |
| Used within another drafting task, such as an abstract or rebuttal | Return only the requested artifact, including when no edits are needed. Add no preface or follow-up offer. Keep audit notes, `Changes:`, clean-status messages, and setup offers out of it. |

Choose the mode from the user's request. Naming a path alone reads the file;
an explicit request to edit it authorizes the write. A review-only request
takes precedence over the default rewrite behavior.

Claude Code: `/anti-slop:academic-voice`. Codex: `$anti-slop:academic-voice`.

## Ordering

When using `public-hygiene`, run `cold-read` and apply the author's
answers before this style pass. Run `leak-check` after this pass, on the
final text. If later edits add or change prose, repeat the affected checks.
