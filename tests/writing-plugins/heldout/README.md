# Held-out document comparison

This set contains three public artifacts absent from the earlier pilot:
a complete CLI README, an incident postmortem with three figures, and a
paper's title, authors, and complete abstract. It is held out from the
earlier plugin revisions, not guaranteed absent from model training.

[sources.json](sources.json) records exact scopes, audiences, source links,
licenses, transformations, and hashes. [cases.json](cases.json) contains
only the raw tasks: comprehension, sequential comprehension, engineering
style, leak checking, and academic style. The two comprehension conditions
use the same three questions. No expected answers enter model prompts.
Previously published sources are not assumed free of leaks or context gaps.

Prepare full third-party text and images outside the repository:

```sh
python3 tests/writing-plugins/heldout/prepare.py --output /tmp/writing-next-heldout
```

The script verifies extracted document and asset hashes. The README is
pinned to a Git commit and the abstract to arXiv v1. The postmortem figures
and packaging badge are separate web snapshots, which may stop reproducing
if their publishers change them. `--reuse-downloads` verifies a retained
cache. Case source paths refer to the default recorded temporary location;
adjust them if preparing elsewhere.

Run a fresh isolated native parent for each case:

```sh
python3 tests/writing-plugins/real-documents/run_native.py \
  tests/writing-plugins/heldout/cases.json \
  --output /tmp/heldout-haiku --backend claude \
  --model claude-haiku-5-5 --effort medium --jobs 2 --timeout 900
```

Use `claude-sonnet-5-5` for Sonnet. Codex conditions use `--backend codex`
and either `gpt-6.1-terra` or `gpt-6-luna`. Where nested sandboxing is
unavailable, an explicit `--codex-sandbox danger-full-access` runs with
instruction boundaries and source hash checks, not filesystem isolation.
The trusted-fixture Claude runner also permits parent shell execution;
inspect actual reviewer tools and accesses separately.

For each model, repeat only `sd-deslop` with `--baseline` in a new output
directory. This preserves the editing request and inputs while omitting
the plugin. One run per condition is a small comparison, not a model
ranking or a statistical estimate of reliability.

Assess saved reports against their source, and compare style edits with
both the original and the baseline. Count unsupported findings as well as
missed issues. Review factual scope, conditions, negations, code, links,
numbers, and author intent before judging tone. For sequential mode,
inspect tool traces for checkpoint timing, future reads, and assembly;
a well-formed final report alone does not prove sequential exposure.
Retain failed attempts and distinguish requested model/effort from what
the runtime actually reports.
