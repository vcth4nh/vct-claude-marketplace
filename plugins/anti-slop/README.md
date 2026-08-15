# anti-slop

Remove AI-slop tone from prose. Two skills, one shared ban list:

- **`deslop`** — engineering prose: READMEs, docs, commit messages, PR
  descriptions, release notes, blog posts.
- **`academic-voice`** — paper prose: abstracts, methods, results, related
  work, camera-ready text. Matches your voice from an optional per-repo
  samples file.

Both audit against [`references/ban-list.md`](references/ban-list.md),
rewrite, and report every change as `span` → `replacement`. Hard constraints:
no new facts, code blocks and math stay byte-identical, rewrites never get
longer than the original.

## Install

```
/plugin marketplace add vcth4nh/vct-claude-marketplace-public
/plugin install anti-slop@vct-public
```

## Usage

```text
Deslop this README section: <paste>
/anti-slop:deslop check <paste>              # report violations, no rewrite
Humanize this paragraph for the paper: <paste>
/anti-slop:academic-voice paper/intro.tex
```

Claude also applies the skills on its own when it writes public prose.

## Per-repo voice (optional)

Create `.claude/writing-samples.md` in your repo — `academic-voice` offers to
scaffold it from its template. Paste 2-3 paragraphs each of engineering and
paper prose you admire. The rewrite matches their rhythm and concreteness —
register, never phrases. Keep the file private; do not republish borrowed
excerpts.

## ASD-STE100 output style (opt-in)

The plugin ships an [ASD-STE100](https://www.asd-ste100.org/) (Simplified
Technical English) output style for Claude's own replies. It stays inert
until you select it: `/config` → Output style, or per repo in
`.claude/settings.json`:

```json
{ "outputStyle": "ASD-STE100" }
```

Not recommended for paper repos — STE's uniform short sentences fight paper
rhythm.

## Pipeline order

Style first, gate last: run [`public-hygiene`](../public-hygiene/) on the final text
after any rewrite here.

## Credits

- [petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop) — prior
  art for slop-removal skills.
- [matsuikentaro1/humanizer_academic](https://github.com/matsuikentaro1/humanizer_academic)
  — prior art for the academic register pass.
- [ASD-STE100](https://www.asd-ste100.org/) — the Simplified Technical
  English specification.

All pattern text in this plugin is original wording; no upstream text is
copied.
