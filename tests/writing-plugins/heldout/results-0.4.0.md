# Writing-plugin comparison at medium effort

This comparison found useful implementation fixes, but no general advantage
for the plugins over ordinary model editing. Saved review files and the
sequential assembler preserve report bytes when the workflow completes.
Finding quality and instruction following still vary. Sequential reading
remains experimental. The resulting versions are public-hygiene 0.4.0 and
anti-slop 0.3.2; the initial matrix and subsequent retests use separately
recorded snapshots.

## Design and scope

The [source manifest](sources.json) pins three artifacts absent from the
earlier eight-document pilot:

- The complete [sd README](https://github.com/chmln/sd/blob/44febdf86343c653255ae4f20f5e1882dad6be17/README.md),
  1,062 words, with a separately captured packaging badge.
- Spike's [incident-grouping postmortem](https://spike.sh/blog/postmortem-incident-grouping/),
  762 words and all three in-body figures.
- The title, authors, and complete [FaultProfIT v1 abstract](https://arxiv.org/abs/2402.17583v1),
  256 words. This does not test the full paper.

Each model received five tasks: README comprehension, sequential
comprehension, README style editing, postmortem leak checking, and abstract
style editing. A sixth task repeated the README edit without the plugin.
The matched style requests used identical inputs and audiences. The two
comprehension conditions used the same three questions; parents chose
their own sequential boundaries. Expected answers and grading notes stayed
outside tested contexts. Published inputs were not presumed clean.

The initial matrix contains 24 native CLI attempts, one per condition.
Assessment was qualitative and unblinded. These artifacts are held out from
earlier plugin development, not necessarily from model training. Neither
the sample size nor the baseline coverage supports a model ranking or an
overall effectiveness score. Academic edits have no no-plugin control.

The complete ledger contains 38 attempts: 24 initial matrix runs, two early
smokes affected by test-harness restrictions, four installed invocations,
three installed report/stage retests, one Terra sequential retest, and four
academic retests. Two academic retests use an independent synthetic
regression; the other two repeat the published abstract. Availability probes
and final documentation reviews are separate from this count.

Claude Code 2.1.317 reported `claude-sonnet-5-5` and `claude-haiku-5-5`
for both parents and children. Codex 0.165.0 was configured with
`gpt-6.1-terra` or `gpt-6-luna`; its evaluation JSON does not identify the
actual parent or child model. Separate preflight startup headers matched
the requested Codex model names. All conditions requested medium effort.
Preflight status/header checks confirmed medium configuration, but the
evaluation streams do not independently report effective effort.

## Report delivery and sequential reading

The initial candidate was `9be9aa8`, with runner `d5934c6`. It replaced
parent-generated copies of reviewer reports with child-written scratch
files. The response links the saved report and copies its verdict.
Sequential readers save separate checkpoints; a Python helper inserts
their original bytes into the final report exactly once. This addresses
the omitted and rewritten checkpoints found in the earlier pilot.

| Model | Ordinary README review | Sequential README review | Elapsed seconds, ordinary / sequential |
|---|---|---|---|
| Sonnet | Report write rejected; incomplete | Four checkpoints, assembled report, seven findings | 100 / 179 |
| Haiku | Saved report, three findings | Nine checkpoints; last stage incorrectly marked incomplete; no consolidation | 59 / 251 |
| Terra | Saved report, one finding | Five checkpoints, assembled report, three findings | 54 / 170 |
| Luna | Saved report, one finding | Seven checkpoints, assembled report, two findings | 78 / 291 |

All three completed sequences had byte-exact source chunks and every raw
checkpoint appeared once in the assembled report. Sonnet's trace showed
checkpoints returned before subsequent dispatches, public-prefix reads,
and no original-source, manifest, or unprovided future-chunk reads. Codex
logs did not expose child handoffs or reads, so their final artifacts cannot
prove fresh context or reading order. Haiku also omitted a supplied badge
mapping and skipped some supplied earlier checkpoint files.

The README's unexplained phantom-match wording was a useful recurring
finding. Other questions sought details already available in examples or
in the surrounding benchmark subsection. Sequential mode added some
plausible questions, including an unspecified file-size unit, but also
unnecessary ones. These results do not establish a net reliability gain.

Two Sonnet report writes were rejected by Claude Code's input validator,
not by the model or an ordinary file permission. Local binary inspection
found a subagent Write check for Markdown basenames beginning with REPORT,
SUMMARY, FINDINGS, or ANALYSIS. The successful filenames did not match that
check. The plugin now chooses neutral `.txt` filenames before dispatch.
Both affected installed-plugin retests saved `review-001.txt` on their first
Write and delivered working links with matching verdicts.

The installed Haiku sequential retest still failed: after six completed
stage calls, the assembler rejected a checkpoint whose first line was an
AUDIENCE line instead of its FIRST READ header. The parent should have caught
that before advancing. It ultimately returned INCOMPLETE, preserved the
records, and created no assembled output. This is a successful structural
rejection, not a successful reading test.

Other corrections make a completed reading distinct from a passing
publication verdict, permit supplied checkpoint files and explicitly mapped
public snapshots, require the status as the file's last line, and prohibit
restating unsaved findings after an incomplete result. A further shared-rule
fix permits introduced code examples as evidence for meaning, while still
excluding code correctness checks and execution. The previous blanket rule
against looking inside code contradicted comprehension of CLI documentation.

The Terra retest at `70a4f14` combined the filename, stage-status,
checkpoint/companion handoff, and example-reading changes since `9be9aa8`.
It retained nine checkpoints exactly and
answered the three core questions correctly. The two earlier questions
already answered by code examples disappeared; the remaining findings
concerned the file-size unit and phantom-match wording. Several instructions
and chunk boundaries changed between these runs, so this single retest
does not isolate the example-rule change's effect.

These are instruction limits and structural checks. The helper cannot
enforce model behavior, semantic consolidation, file authorship, or read
order. Some parents added narration or questions instead of limiting the
response to the link and verdict. Some inspected only report markers rather
than the full saved report. Those are retained as adherence issues. A
conflicting instruction also told the leak-check parent to ask clarification
questions while report delivery forbade repeating findings. The final
contract puts those questions in the saved findings and requires answers
before applying a fix.

## Leak-check quality

The postmortem test exposed over-flagging. Haiku treated several explicitly
explained service/data terms as undefined private vocabulary, classified an
informal published caption as working scrap, and proposed an on-call role
that the source did not state. It also put a real chronology inconsistency
in the leak report. That inconsistency belongs to comprehension and does
not itself demonstrate a leak.

The screenshot's visible operational identifier is a reasonable item to
check for intended disclosure. However, the supplied publication context
does not establish that redaction is mandatory. Likewise, asking whether a
service name was intentionally published differs from proving that it is
private. The assessment separates those uncertainties from unsupported
claims. No precision or recall percentage is assigned to this corpus.

## Style quality

All eight initial README edits preserved the original fenced commands,
benchmark-table lines, existing inline-code values, and link targets.
Plugin edits were generally conservative; the no-plugin baselines often
explained the examples more clearly. Some baselines weakened selection or
recommendation qualifiers, and one expanded an ambiguous size unit without
source support. Haiku's plugin edit introduced an awkward repeated verb.
There was no consistent plugin advantage in this comparison.

All four initial academic edits retained the title, authors, and links.
Terra's rewrite was source-faithful in this assessment. Sonnet introduced a
single-category interpretation not established by the excerpt. Luna tied
cumulative counts to a deployment interval and changed scientific qualifiers
and lower-bound wording. These are meaning-preservation issues even when
the prose reads more smoothly. The academic workflow was updated to compare
quantity bounds, time bases, claim strength, and classification scope.

Sonnet and Luna then each repeated the abstract and edited a new
materials-inspection regression. Both retained its lower and upper numerical
bounds, separate operating duration and cumulative counts, verification
claim, classification subject, and two distinct technical properties.
On the abstract, Luna restored the cumulative count basis,
bound notation, and omitted technical property; it still weakened a
verification claim. Sonnet still imposed a one-fault-per-incident reading.
The new check helped some failures but did not eliminate semantic drift.

## Installation and validation

Both CLIs support real local-marketplace installation. Fresh installs and
upgrades were tested in isolated profiles. Claude's local-folder install
can read the registered marketplace source; Codex reads its installed cache.
The checks distinguish those paths instead of claiming every invocation
reads an identical kind of cache.

Final package validation at `1b04541` covered public-hygiene 0.4.0 and
anti-slop 0.3.2: fresh installs and upgrades from the prior 0.3.1 version passed on
both CLIs, with 76 final-version file comparisons and no mismatches. Each
profile discovered all four skills; Claude also discovered the two agents.
Three manifest validators, four skill validators, and 23 relative file
targets passed. Claude's same-version update retained an earlier cache, so
the final exact-file comparison used new isolated profiles rather than
manually changing caches. Behavioral results remain tied to their recorded
snapshots; this final check verifies packaging and discovery.

Four installed invocations tested comprehension and academic editing on
Haiku and Terra. Claude traces confirmed registered slash-command dispatch
and the bundled reviewer. Codex used an explicit installed skill path;
this tests installed content, not automatic skill selection. Both review
inputs stayed unchanged and both edits changed only the authorized copies.
The installed Haiku review still had format and companion-reading issues.

The preparation and assembly helpers passed 17 deterministic tests,
including byte preservation, ordering, invalid input, symlinks, aliases,
exclusive creation, and partial-write cleanup. Source manifests also
reproduced the three documents and four assets from cached and fresh
downloads at test time. Mutable publisher assets may change later.

All original corpus sources remained unchanged. Tests used disposable
working copies. The trusted-fixture Claude parent had shell access; Codex
used explicit `danger-full-access` because nested sandboxing was unavailable.
Neither setup establishes filesystem isolation. Authentication was reused
through isolated-profile references without copying credentials; credential
metadata stayed unchanged. An official-marketplace timestamp refreshed
during concurrent CLI runs, so the checks do not claim all global metadata
remained untouched.

## Evidence and limits

[run-index.json](run-index.json) records attempts, snapshots, requested and
reported identities, results, and evidence locations. Raw logs, full source
texts, rewrites, figures, and evaluator notes remain in temporary directories
outside the repository. They are inspectable in the recorded environment,
not permanent hosted artifacts. The index retains incomplete runs and
retests separately; exit code zero is not a writing-quality pass.

The changes improve report preservation and address specific rule
contradictions. They do not make publication verdicts authoritative or
establish that smaller models can run the workflow unattended. Review
meaning-preservation and sensitive-disclosure decisions before applying
an edit or publishing text.
