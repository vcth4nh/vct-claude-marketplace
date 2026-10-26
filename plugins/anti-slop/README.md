# anti-slop

Remove AI-slop tone from prose. Two skills, one shared ban list:

- **`deslop`** for engineering prose: READMEs, docs, reports, write-ups,
  commit messages, PR descriptions, release notes, blog posts.
- **`academic-voice`** for paper prose: abstracts, methods, results, related
  work, camera-ready text. Matches your voice from an optional per-repo
  samples file.

Both audit against [`references/ban-list.md`](references/ban-list.md),
rewrite, and report every change as `span` → `replacement`. Hard constraints:
no new facts, code blocks and math stay byte-identical, rewrites never get
longer than the original, except where a claim moves out of a heading into
the body.

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
```

Claude Code uses `/anti-slop:<skill>`; Codex uses `$anti-slop:<skill>`.
The skills also apply automatically when the agent writes prose for a
human reader.

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
{ "outputStyle": "ASD-STE100" }
```

Not recommended for paper repos, because STE's uniform short sentences fight
paper rhythm.

## Pipeline order

Style first, gate last: run [`public-hygiene`](../public-hygiene/) on the final text
after any rewrite here.

## Credits

- [petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop), prior
  art for slop-removal skills.
- [matsuikentaro1/humanizer_academic](https://github.com/matsuikentaro1/humanizer_academic),
  prior art for the academic register pass.
- [ASD-STE100](https://www.asd-ste100.org/), the Simplified Technical
  English specification.

All pattern text in this plugin is original wording; no upstream text is
copied.
