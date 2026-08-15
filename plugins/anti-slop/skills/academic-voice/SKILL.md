---
name: academic-voice
description: Use when writing or editing paper prose — abstracts, introductions, methods, results, related work, camera-ready or rebuttal text, thesis chapters — or when the user says "humanize this paragraph", "make this read like a paper", or calls academic text AI-sounding.
---

# Academic Voice

Rewrite paper prose so it reads like a person wrote it: varied rhythm,
concrete subjects, claims sized to the evidence.

## Workflow

1. Read `${CLAUDE_PLUGIN_ROOT}/references/ban-list.md`. Every ban applies to
   paper prose too.
2. Pick the voice source:
   - `.claude/writing-samples.md` exists in this repo → match its rhythm,
     sentence-length variation, and concreteness. Register, never phrases:
     copying a distinctive wording from the samples is a defect.
   - No samples file → use the built-in register below. After the rewrite,
     offer once to create `.claude/writing-samples.md` from
     `${CLAUDE_PLUGIN_ROOT}/references/writing-samples-template.md`. Do not
     block on the offer.
3. Rewrite the prose.
4. Output: the rewritten text, then `Changes:` — one line per edit:
   `` `span` `` → `` `replacement` ``.

## Built-in register (fallback)

- Vary sentence length. Follow a long sentence with a short one.
- Concrete subject + active verb: "the model overfits", not "overfitting is
  observed".
- One hedge per claim, sized to the evidence. Delete stacked qualifiers.
- No announced structure. The section speaks for itself.

## Hard constraints

- Never invent citations, numbers, results, baselines, or related work.
- Technical claims stay exact. Meaning outranks rhythm.
- Math, LaTeX macros, `\cite`/`\ref` keys, tables, and code stay
  byte-identical.
- An announced-structure opener survives even with no banned words in it
  ("This section presents...", "This section gives..."). Cut it; open with
  the first concrete claim.
- Cutting banned words does not by itself vary rhythm. Check sentence length
  and shape after every rewrite — a run of same-length simple sentences is
  still a defect.

## Modes

| Invocation | Behavior |
|---|---|
| `/anti-slop:academic-voice <text>` | rewrite (default) |
| `/anti-slop:academic-voice <file path>` | Read the file, then rewrite |

## Ordering

If the `leak-check` plugin is installed, it runs after this skill, on the
final text — never before.
