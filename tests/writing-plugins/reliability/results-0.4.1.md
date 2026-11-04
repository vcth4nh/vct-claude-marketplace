# Focused reliability checks

Public-hygiene 0.4.1 adds per-checkpoint validation to experimental sequential
reading and requires concrete evidence for leak findings. Anti-slop remains
at 0.3.2: the [blind style comparison](../style-comparison/README.md) rejected
a proposed relaxation of its length rule under the predefined criteria.

These checks follow the [earlier medium-effort comparison](../heldout/results-0.4.0.md).
They do not establish reliable end-to-end review. Native Haiku runs still
invented publication constraints, failed to save one report, and frequently
returned paths without clickable links. All attempts are retained, including
those failures.

## Sequential checkpoints

The assembly helper now supports `--validate-checkpoint FILE --stage I --total N`.
It validates the reserved handoff path against the expected position and
returns its hash only after accepting the checkpoint. The parent must invoke
it successfully before sending another chunk or requesting consolidation.
Malformed headers, misplaced or repeated markers, an incorrect position,
and `STAGE: INCOMPLETE` stop validation without changing files. A recorded
incomplete stage has a separate diagnostic from malformed syntax.

All 21 deterministic helper tests pass, including a parent stub that does
not advance when validation fails. Replaying a malformed checkpoint from
the earlier Haiku run also rejects stage 2 before stage 3 without repairing
its bytes. These checks cover rejection mechanically; they cannot force an
LLM parent to call the helper or honor its result.

One native Haiku 5.5 run, with medium effort requested, used the unchanged
complete sd README and sequential-comprehension request. It produced four
checkpoints. Each successful validator result preceded the next dispatch,
including the final consolidation. The reserved paths and recorded hashes
matched; every checkpoint appeared byte-for-byte exactly once in the final
report. Reviewer traces showed no original-source, manifest, or unprovided
future-chunk reads. Inputs and reviewer-written reports remained unchanged.

This run generated no malformed checkpoint, so native failure-stop behavior
remains untested. Input hashes were rechecked at assembly, rather than after
each stage as instructed. Its final verdict matched the saved report, but
the reply used a non-clickable path and added workflow narration. Finding
correctness was outside this protocol audit. Sequential reading therefore
remains experimental, with no demonstrated advantage over ordinary review.

## Leak findings

The revised rules require evidence of private context, a publication
restriction, or unfinished working material. Explained names, relevant
public bylines, informal tone, and absent separate approval alone do not
establish a leak. Explicit internal designations, glossary terms, private
paths and infrastructure, and anonymity requirements still apply. An
explicit submission request with identifying text but no stated anonymity
policy receives one policy question.

Five native Haiku 5.5 skill invocations requested medium effort. The
[synthetic pair](../leak-evidence.json) holds its public incident narrative
constant and adds five private disclosure groups to the second version.
The other inputs were the complete Spike incident postmortem with all three
figures, and the Raft abstract and introduction under explicit anonymous
submission and unspecified submission-policy requests. Pair expectations
stayed in [separate rubrics](../leak-evidence-rubrics.json), outside model
context. The evaluator authored the synthetic pair and assessed these
outputs; this part of the evaluation was not blind.

| Case | Content observation | Integration result |
|---|---|---|
| Public narrative | Saved PASS; no unsupported finding | Working link and matching verdict; parent added interpretive approval commentary |
| Same narrative with private additions | Child text found all five planted disclosure groups with no extra finding | No report saved; parent reproduced unsaved findings |
| Spike postmortem | Saved PASS | Confounded by parent-invented approval for the published narrative |
| Raft, explicit anonymous submission | Correctly flagged authors and affiliation as one identity group | Working link and matching BLOCK |
| Raft, unspecified submission policy | Two policy findings, including an unsupported duplicate | Confounded by parent-invented anonymity expectations |

All five processes exited successfully, but that does not make the reviews
successful. Four reports were saved and matched their child Write payloads;
only two final replies had a working report link and matching verdict. The
private-additions reviewer declined a parent-chosen Markdown path without
attempting Write. Its stated prohibition came from the model, not a native
tool rejection. Coverage of five groups in unsaved text is not a completed
review. No source, glossary, or figure changed.

An explained, unmarked name such as the synthetic Beacon supplies no
evidence of private status. A PASS on that input neither establishes
approval nor tests detection of a concealed private name. Publication
history also does not clear the operational identifier visible in the Spike
screenshot. The invented approval makes that skill result unsuitable for
measuring reduced false alarms.

## Direct reviewer checks

Three additional Haiku 5.5 attempts invoked the plugin's native
`external-reviewer` directly, with medium effort requested. A script supplied
the original request and publication constraints verbatim, a reserved neutral
`.txt` output path, and the absolute reviewer-instruction path. This removed
the LLM parent that had invented approval or anonymity expectations. Each
run used a fresh workspace, disabled automatic memory, excluded user/project
settings and MCP servers, and exposed only Read, Grep, Glob, and Write.
This is instruction isolation, not an operating-system sandbox.

| Case | Direct reviewer result |
|---|---|
| Private additions | Saved all five required disclosure groups, with no extra finding; unnecessarily described the host as a production machine |
| Raft, unspecified submission policy | Saved exactly one anonymity-policy question, without assuming anonymous review |
| Spike postmortem | Asked about the screenshot's operational ID, but also labeled its ID and service labels internal without enough evidence |

All three saved reports matched their Write payloads, and all supplied
inputs stayed unchanged. Only the private-additions reply obeyed the
reviewer's path-and-verdict-only contract; the other two added summaries.
The Spike identifier is a plausible disclosure ambiguity, but the labels
bundled into that finding are not independently supported as private.
The direct tests therefore support limited rule behavior while retaining a
remaining false-alarm problem. They do not repair or validate the failed
parent handoffs, and they are not counted as successful skill invocations.
Both leak batches used Claude Code 2.1.318, but their source snapshots and
invocation routes differ. This is not a comparison that changes only one variable.

Across this phase there were 15 CLI attempts: one sequential review, five
leak-check skill invocations, three direct leak reviewers, and six style
edits. Each condition ran once; none was silently retried. Two separate blind
graders assessed the style edits. Costs and exact invocation routes are
recorded separately in the execution ledgers.

## Package validation

The frozen source at `821054b` contains public-hygiene 0.4.1, anti-slop
0.3.2, and marketplace 0.1.6. Fresh installs and upgrades from the actual
0.4.0 source passed through supported local-marketplace commands in Claude
Code 2.1.318 and Codex 0.165.0. All 76 installed-file comparisons matched
the 19 tracked package files across four isolated profiles. Each profile
discovered all four skills; Claude also found both agents. Three manifest
validators and four skill validators passed. The plugin manifests had only
optional missing-icon warnings.

Installation made no model calls, created no authentication files or
references, and left the checked real configuration and plugin registries
unchanged. These results cover local installation, upgrade, discovery, and
package integrity. They do not test remote marketplace distribution or
model behavior.

## Evidence and reproduction

[run-index.json](run-index.json) records attempts, assessments, source
snapshots, and file hashes. The stage run preceded the final diagnostic and
reserved-path clarification; deterministic tests cover those follow-ups.
The five skill runs preceded the final metadata and hostname-sentence
clarification. Exact snapshots are retained instead of treating all runs as
tests of identical bytes.

Use the existing [native runner](../real-documents/run_native.py) and
[held-out preparation procedure](../heldout/README.md) for the stage and
Spike inputs. The Raft excerpt and its preparation are recorded in the
[real-document corpus](../real-documents/README.md). Create the synthetic
pair from its `files` objects; the glossary is workspace setup, never a
public companion. Give reviewers only the raw case, source, stated audience,
and permitted companions, keeping rubrics and earlier outputs out of context.

Raw traces, reports, and copied third-party material remain outside the
repository. The ledger uses `EVIDENCE_ROOT` for their logical locations;
the actual local directory mapping is retained separately. These paths
are not hosted or included artifacts. Artifact hashes refer to unmodified
evidence, and the public assessment omits the screenshot's exact incident
identifier. Each condition ran once. Native responses
identify Haiku or Sonnet; medium effort was requested but is not independently
verified by the result streams. The blind style graders were separate fresh
Terra and Luna agents at requested medium effort. Small samples, reused
sources, and evaluator judgment limit any claim of broader effectiveness.
