# Real-document writing pilot

This corpus tests the writing plugins on eight published artifacts. The
sources are pinned by revision and/or SHA-256; originals are not assumed
clean. [Results](results-0.3.1.md) distinguish useful findings, false alarms,
uncertain publication judgments, and execution failures.

## Inputs

- [Local README and archived PR](sources-local-pr.json)
- [Guide, PEP, incident report, and paper excerpt](sources-documents.json)
- [Two slide decks](sources-slides.json)

The manifests record audiences, exact scope, transformations, companions,
licenses, and hashes. Full third-party texts and images remain outside the
repository. The recorded `/tmp/writing-real-documents` locations identify
this run's cache; they are not permanent download URLs. Recreate inputs
from the manifests, verify their hashes, and adjust source paths before
rerunning on another machine. Mutable web pages may no longer reproduce
the recorded bytes.

Raft covers only the abstract and introduction. PEP style testing uses the
compatibility/distribution/performance excerpt; its context and leak checks
use the full PEP. Slide source, live rendered text/images, and archived PDFs
have separate provenance. The exports include complete same-slide notes.
Dynamic demonstrations, clipped-code visibility, and intermediate animation
states are outside the text test. The slide source includes one disabled
slide; the audience-facing export excludes it.

[cases.json](cases.json) preserves the initial raw requests, including a PR
style-request confound described in the results. Expected answers and
adjudications must never be included in a model's case inputs.
[control-cases.json](control-cases.json) records the separate follow-up
requests. [control-construction.json](control-construction.json) records
their synthetic additions and preparation; it is evaluator material and
must stay out of reader context.

## Runner

The runner accepts a JSON array or an object containing `cases`. Each case
has `id`, `source`, and `mode`; optional fields are `target`, `audience`,
`request`, `questions`, `companions`, and `setup_files`. Companion/setup
entries contain `source` and an optional workspace-relative `target`.
Setup files install private context such as a leak glossary without naming
it as a public companion. A source alone defaults to its basename.

Modes: `ordinary`, `comprehension`, `sequential`,
`sequential-comprehension`, `deslop`, `academic`, and `leak`.
Style cases explicitly edit an isolated copy. Review cases leave source and
companion copies unchanged. The native parent performs sequential chunk
preparation; the runner does not prepare its reading sequence for it.

```sh
python3 tests/writing-plugins/real-documents/run_native.py \
  tests/writing-plugins/real-documents/cases.json \
  --output /tmp/writing-next-run --case retrospect-comprehension \
  --backend claude --jobs 1
```

Use `--dry-run` to prepare and inspect prompts without a model call.
Outputs require a new directory and include plugin snapshots, source
copies, prompts, full native logs, extracted traces, usage, timings, and
before/after hashes. `--baseline` runs style cases with the same editing
request but without applying skills. `--model` and `--effort` set explicit
parent and child settings; omitted options retain backend defaults. For
example, use `--model claude-haiku-5-5 --effort medium` with Claude or
`--model gpt-6.1-terra --effort medium` with Codex. Claude child overrides
are forced per process; Codex child defaults can be overridden by an explicit
spawn configuration. Requested settings and observed response identities
are recorded separately. The JSON streams do not verify effective effort;
Codex's stream also does not identify the actual model. Claude has a
configurable dollar cap; Codex has only a timeout.

`--installed-config-root PATH` uses an existing isolated installation. Claude
invokes its registered slash command without `--plugin-dir`; Codex reads the
explicit installed skill path, which does not test automatic selection.
The runner neither installs plugins nor copies authentication. Use a profile
with one installed version of each tested plugin. Local-folder Claude
installations may read the registered marketplace folder instead of their
cache, so inspect the trace and hash that source too. This route loads the
profile's user settings; keep the profile dedicated to the test.

Codex is selected with `--backend codex`. Its default per-case sandbox is
workspace-write, permitting scratch reports. This environment could not start nested
sandboxing, so the recorded pilot explicitly used
`--codex-sandbox danger-full-access` with instruction boundaries and hash
checks. It did not establish filesystem isolation. Codex's exported logs
did not expose child handoffs or reads; only Claude traces support the
child-access findings in this report.

An exit code or completed response is not a quality result. Inspect the
actual rewrite and report, including preservation, supported questions,
child context, checkpoint order, and report delivery. For saved reviews,
verify that the final link exists, the chat verdict equals the saved verdict,
and the parent has not restated findings. For sequential reports, compare
each assembled checkpoint with its original bytes and inspect stage timing
and reviewer accesses separately. Preserve failures and
retests as separate attempts. A model-selected comprehension question is
not evidence that every important question was answered.
