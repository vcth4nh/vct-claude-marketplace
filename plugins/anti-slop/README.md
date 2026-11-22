# anti-slop

Remove AI-slop tone from prose. Two skills, one shared ban list:

- **`deslop`** applies when a task calls for drafting or revising technical
  prose for readers, such as an internal design note, customer incident
  update, README, or PR description.
- **`academic-voice`** for paper prose: abstracts, methods, results, related
  work, camera-ready text. Matches your voice from an optional per-repo
  samples file.

Both audit against [`references/ban-list.md`](references/ban-list.md) and
check the rewrite for lost facts, unsupported additions, and excessive
editing. Meaningful uncertainty, clear cadence, and useful explanations
survive the edit. Factual negations, conditions, and literal technical terms
take priority over style patterns. Rewrites cannot grow except where a
claim moves out of a heading into the body.

The audit includes dramatic framing, personification of tools, and
story-like headings. Rewrites state observations and hypotheses directly,
preserving factual chronology, causal links, and uncertainty. Literal
technical terms such as "test harness" and conventional wording such as
"the compiler reports" stay.

## Install

Claude Code:

```
/plugin marketplace add vcth4nh/vct-claude-marketplace
/plugin install anti-slop@vct-public
```

Codex:

```bash
codex plugin marketplace add vcth4nh/vct-claude-marketplace
codex plugin add anti-slop@vct-public
```

## Usage

```text
Deslop this README section: <paste>
deslop check <paste>                        # report violations, no rewrite
Humanize this paragraph for the paper: <paste>
academic-voice paper/intro.tex
Edit paper/intro.tex in place with academic-voice
```

Claude Code uses `/anti-slop:<skill>`; Codex uses `$anti-slop:<skill>`.

Standalone rewrites include a change report. Naming a file alone reads it
and returns a rewrite; asking to edit it applies the changes to the file
and returns a brief summary. Review-only requests leave files untouched.
Within a drafting task, either skill returns only the requested text.
For a customer incident update, that’s the message customers will read.

File edits change prose only. Code, commands, paths, YAML metadata, data,
and link targets stay byte-identical; `academic-voice` also protects math,
LaTeX macros, citation/reference keys, and tables.

## Per-repo voice (optional)

Create `.agents/writing-samples.md` in your repo, or let `academic-voice`
scaffold it from its template. An existing `.claude/writing-samples.md` is
used when the shared file is absent. Paste 2-3 paragraphs each of engineering
and paper prose you admire. The rewrite matches their rhythm and
concreteness, never their phrases. Keep the file private; do not republish
borrowed excerpts.

## ASD-STE100 output style (opt-in)

The plugin ships an [ASD-STE100](https://www.asd-ste100.org/) (Simplified
Technical English) output style for Claude Code replies only. It stays inert
until you select it: `/config` → Output style, or per repo in
`.claude/settings.json`:

```json
{ "outputStyle": "anti-slop:ASD-STE100" }
```

Not recommended for paper repos, because STE's uniform short sentences fight
paper rhythm.

## Pipeline order

When using [`public-hygiene`](../public-hygiene/), run `cold-read` and
apply the author's answers first, then `deslop` or `academic-voice`, and
finally `leak-check`. Context answers can add prose, so the style and leak
checks must see those additions. Repeat the affected checks after later edits.

## Credits

- [petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop), prior
  art for slop-removal skills and checks for excessive compression and
  loss of the author's voice.
- [matsuikentaro1/humanizer_academic](https://github.com/matsuikentaro1/humanizer_academic),
  prior art for the academic register pass.
- [blader/humanizer](https://github.com/blader/humanizer), a related skill
  with an explicit audit for added or dropped claims, separate embedded
  and file output modes, and protection for non-prose file content.
- [ASD-STE100](https://www.asd-ste100.org/), the Simplified Technical
  English specification.

All pattern text in this plugin is original wording; no upstream text is
copied.
