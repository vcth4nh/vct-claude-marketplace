# Real-document results for the writing plugins

Tested on 2026-11-04 (Asia/Bangkok). This is a small, judgment-based pilot,
not an accuracy estimate or publication certification. It supports narrow
improvements to version 0.3.1 and leaves several behavior failures open.
An ordinary review audits the document in one pass. Sequential reading
exposes one chunk at a time and records a checkpoint before the next chunk.
Comprehension adds source-backed questions and answers to either review.

## What was tested

Eight artifacts received initial comprehension, style, and leak checks:
24 artifact/mode cases. Additional runs compared ordinary and sequential
reading on the README and two seven-slide excerpts, compared two style
outputs with no-skill baselines, tested publication-context controls, and
retested observed failures. Originals and simulated defects are reported
separately. Source manifests and [case requests](cases.json) preserve the
chosen audiences and scopes.

| Artifact | Useful evidence | Limits or failures |
|---|---|---|
| retrospect README | Readback recovered session scopes and the approval gate; questions identified an unexplained rule, an unclear size threshold, and an unnamed performance metric. | A schema question exceeded interpretation needs. Initial style edits lost label rationale; the retest preserved it. Earlier leak candidates overflagged test history; the final corrected reviewer passed it. |
| uv projects guide | Small style edits preserved code and operational qualifiers; final native leak review used a fresh reviewer and passed. | A guide/CLI-companion conflict was found, but the generated CLI companion came from a separately retrieved publication, so revision drift limits that finding. |
| PEP 703 | Full-document comprehension found conflicting descriptions of GC metadata and allocator heap counts; the style excerpt retained compatibility and performance conditions. | Style testing covers only the recorded excerpt. These findings concern communicated consistency, not external implementation correctness. |
| Cloudflare outage report | Readback distinguished service recovery from later WAF re-enablement and retained multiple contributing causes. Leak review correctly read identifiers and artifact paths inside screenshots. | One measurement-window question was probably unnecessary. Screenshot disclosures require publisher judgment; their public availability alone does not settle that judgment. Initial SRE/P0 jargon flags disappeared in the retest. |
| Raft paper | Abstract/introduction readbacks preserved the comparative study population and result without universalizing them; style edits retained citations and technical qualifications. | The full paper was not evaluated. This excerpt has no mathematics or tables, so it provides no evidence of mathematical-layout preservation. |
| ESLint talk | Readbacks recovered the configuration and broader tooling claims. | Initial style edits narrowed the opening and removed a non-recommendation; the retest preserved both. A visible IDE status label was real but weak evidence for blocking publication. |
| Make Tools That People Love | Readbacks and technical meaning were preserved; no context or leak findings were returned. | Some deliberate spoken repetition was flattened. Changes to visible prose in component attributes were not structural-code damage; the initial blanket attribute-preservation rubric was too strict. |

The third-party sources are linked in the manifests. None of their original
documents, the local retrospect README, or their companions were edited.
All style changes occurred in temporary copies.

## Changes supported by the tests

**Anti-slop:** the shared rules now explicitly preserve an author's stated
intent and recommendations, and apply factual-heading preservation to bold
list lead-ins. The same-source README and ESLint retests retained the
previously lost meaning and protected spans. Five targeted synthetic style
regressions also passed, including factual negation, technical heading
causality, uncertainty, speaker intent, and label rationale.

**Public hygiene:** the leak reviewer now uses audience field knowledge
and distinguishes deliberate history/design rationale from private working
notes. Unfamiliar installation coordinates alone do not imply private
status. Explicit internal designations, glossary terms, private paths and
hosts, credentials, and anonymity constraints still apply. Whole READMEs,
guides, and slide/talk documents now explicitly take the fresh-reviewer
route. Sequential handoffs now require the exact snapshot's reader
instruction-file path, preventing ambiguous relative-reference searches.

The first leak candidate still flagged install names and test-history
evidence. A further clarification removed the installation-name ambiguities
but left two test-history false positives. Review found that the agent's
own instructions still called development narrative a leak, conflicting with
the shared rules. Aligning that wording and treating self-contained results
as evidence produced a PASS on the same README. All earlier failures remain
recorded. A planted internal name, path, run ID, and host inside that same
history section were still flagged without a glossary.

The instruction-location guard now applies to both reviewer agents, not
only the sequential-mode reference. Two direct instruction probes without
a supplied location returned `INCOMPLETE`. Final native leak traces resolved
rules from their supplied snapshot without searching for rule files.

The final Cloudflare retest returned 15 image-derived findings instead of
19. It dropped SRE/P0 questions while still detecting internal IDs and
artifact paths. The count change includes other variation and is not a
measured precision/recall gain.

## Controls that changed the interpretation

- The initial archived-PR style case also requested a meaning review against
  the merged diff. It changed factual framing. With that extra request
  removed, the **unchanged** plugin left the source untouched. The proposed
  additional style rule was therefore dropped; this is a harness confound,
  not a demonstrated repair.
- Adding explicit already-public/non-anonymous context made both initial
  README/PR leak reports pass before any rule change. A seeded control under
  the old rules still detected the private path, host, and glossary name,
  including its use in an installation command. The context line did not
  cause blanket acceptance in that control.
- Final native seeded controls also detected those planted details with and
  without prior-publication context. A separate anonymous-submission control
  caught the author byline, but added a speculative study-population finding.
  These are sensitivity controls, not naturally occurring leaks.
- A glossary-free control with an explicitly internal name in prose, a path,
  and a URL was detected. A separate invented public-name control did not
  receive a codename finding merely for repetition; it did receive a
  placeholder-link finding. It is not counted as a clean-document PASS.
- One early control incorrectly listed its private glossary as a public
  companion, causing a spurious finding against the glossary itself. The
  runner now separates private setup files from public companions; only
  corrected controls support the conclusions above.
- No-skill style baselines edited more broadly and sometimes expanded or
  interpreted claims. Plugin outputs preserved more protected bytes. The
  baseline did not receive the plugin's preservation/no-growth rules, so
  this is a behavior comparison, not a blinded preference score or proof of
  overall superiority.

## Sequential reading

| Same-input Codex comparison | Ordinary/comprehension | Sequential/comprehension |
|---|---:|---:|
| retrospect README | 54.91 s; 4 findings | 96.68 s; 3 findings |
| ESLint slides 3–9 | 62.10 s; 0 findings | 120.45 s; 0 findings |
| Tools slides 4–10 | 46.95 s; 0 findings | 103.77 s; 0 findings |

Sequential added no useful finding in these comparisons. On the README it
missed the size-threshold question while retaining an unnecessary schema
question. Both slide reports duplicated the last checkpoint before listing
all checkpoints. Correct chunk bytes were observed, but Codex's exported
logs did not establish actual child exposure or handoff isolation.

Claude's full native trace exposed the missing instruction-path problem:
readers first tried relative rule paths beside the source, then searched
other snapshots. The final five-stage retest took 598.89 seconds. Every
checkpoint returned before the next handoff; all observed child reads stayed
within supplied chunks, allowed glossary locations, and the correct plugin
snapshot. No original-source, manifest, future-sibling, or other-snapshot
reads occurred. This verifies the path correction and observed exposure
boundary, not the complete workflow: some headings were orphaned at chunk
ends, the final child omitted earlier checkpoints, and the parent rebuilt
the report and altered quote punctuation. The one returned gap was valid,
but two useful numeric questions were missed. Sequential remains opt-in
and experimental; the pilot does not establish a reliability advantage.

## Remaining limits

- Native parents sometimes paraphrased a reviewer despite the verbatim-relay
  rule. One earlier handoff added a presumed-public explanation, which the
  reader recast as user approval. Existing rules forbid both; these remain
  observed compliance failures.
- Earlier native README leak reviews blocked legitimate test evidence;
  the final PASS is one corrected trial, not proof that false alarms are
  eliminated. Do not treat BLOCK counts as confirmed unintended disclosures.
- Most cases have one trial. Retests follow demonstrated failures and are
  reported separately; no cross-model aggregate score is claimed.
- Published material may be familiar to the models. There is no blinded
  human preference study, complete ground-truth defect inventory, or
  credential-scanner evaluation.
- PDF/slide extraction was checked before testing. Raft's default extraction
  scrambled columns; a verified excerpt replaced it. Slide exports exclude
  disabled content and retain notes, but cannot establish animation/demo
  fidelity. Live render snapshots are separately hashed from Git source.

## Execution record

Initial tests used Codex CLI 0.165.0 with its default model; the JSON stream
did not identify the model, so none is inferred. Native follow-ups used
Claude Code 2.1.317, whose result events report `claude-opus-4-6`. A separate
coding-agent review challenged the design, findings, and proposed changes.

The first Claude smoke attempt failed authentication. Six Codex attempts
could not start nested sandboxing and were retained as environment failures.
One native runner process was interrupted; its complete child result events
were recovered without inventing process exit codes. Later long runs used a
detached runner with per-case timeouts. Full raw logs remain in the recorded
temporary cache; the committed [run index](run-index.json) retains their
hashes and process outcomes. The qualitative assessment is this report;
those process outcomes are not quality grades. The index records 66 native
CLI attempts: 51 Codex and 15 Claude, including failures and retests. The two
direct instruction-location probes are separate from this CLI count.

Seven deterministic chunk-helper tests, all four skill validators, plugin
and marketplace validation, fixture/rubric consistency, and whitespace
checks are part of the release checks. Existing optional-icon warnings do
not affect the behavioral results.
