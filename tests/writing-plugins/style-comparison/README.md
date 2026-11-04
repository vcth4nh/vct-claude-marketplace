# Blind style comparison

The proposed relaxation of anti-slop's length constraint was **not adopted**.
Both independent graders preferred its guide explanations, but both also
recorded meaning-preservation concerns relative to the current plugin.
That fails the acceptance condition registered before generation: meaning
preservation and protected spans must not worsen on either source, with a
useful clarity improvement on at least one.

## Setup

The trial used two retained public excerpts: the complete Quick Guide
section of the [sd README](https://github.com/chmln/sd/blob/44febdf86343c653255ae4f20f5e1882dad6be17/README.md),
237 words, and the published title, authors, and complete
[FaultProfIT v1 abstract](https://arxiv.org/abs/2402.17583v1), 256 words.
[sources.json](sources.json) records exact scope, licenses, and hashes.
Full third-party texts and edits remain outside the repository.

One fresh Sonnet 5.5 parent, with medium effort requested, edited each
source under each of three conditions: current anti-slop 0.3.2, a minimal
candidate, and no plugin. The current and candidate snapshots differed only
in two statements of the same constraint. The candidate replaced the
absolute prohibition on growth with a preference for concise prose that
allows clarification of existing meaning and respects user length limits.
Other style and preservation rules were unchanged. The exact rejected
change is retained as [candidate.patch](candidate.patch).

[cases.json](cases.json) contains the identical raw tasks and audiences.
[protocol.json](protocol.json) was written and hashed before generation.
The six attempts completed once each; there were no repeated conditions or
additional candidates. Native responses identified Sonnet 5.5. The CLI
requested medium effort; the result stream does not verify effective effort.
Reported generation cost was $0.3201, excluding the separate graders.

Two fresh graders, Terra and Luna at requested medium effort, saw only the
source, neutral task, three randomly labeled edits, criteria, and mechanical
preservation checks. They did not see condition names, the candidate
hypothesis, generation prompts, or the permutation key. The key was opened
only after both assessments returned. Output style can still suggest an
approach; this procedure hides the labels, not all possible stylistic clues.

## Results

All six edits preserved the tested code blocks, existing inline-code
values, and link targets. The abstract's title and author list were also
preserved in all three conditions. Original inputs remained unchanged.

| Source and condition | Words | Meaning judgment: Terra / Luna | Blind comparison |
|---|---:|---|---|
| Guide, current | 220 | Preserved / preserved | Faithful, with limited clarity changes |
| Guide, candidate | 254 | Minor concern / minor concern | Both preferred its explanations |
| Guide, no plugin | 303 | Material drift / minor concern | Added general behavior and changed a recommendation |
| Abstract, current | 242 | Minor concern / preserved | Similar to the candidate |
| Abstract, candidate | 245 | Minor concern / preserved | Terra tied it with current; Luna slightly preferred it |
| Abstract, no plugin | 236 | Minor concern / minor concern | Both noted loss of a source qualifier |

The candidate guide explains the replacement example and the file-finding
command more directly. Both graders viewed those explanations as useful,
but also as additional interpretations beyond the source prose. This is a
preservation concern, not proof that the explanations are technically wrong.
Because the predefined rule required preservation not to worsen, the
clarity preference alone is insufficient to adopt the candidate.

The graders differed on the severity of the no-plugin guide's added claims
and on whether the abstract's revised opening strengthened its meaning.
Those disagreements are retained. One Luna assessment also credited the
candidate guide with an explicit preview-without-modification explanation
that is absent from the artifact. Its original grade remains in the raw
evidence; that example is excluded from this summary. The separately
identified parsing and file-discovery additions are present in the output.

Anti-slop therefore retains its current instructions. This trial does not
establish that the absolute length rule is optimal, or that the candidate
is generally worse. It supplies insufficient evidence to replace the rule
under the acceptance condition chosen before looking at outputs.

## Evidence and reproduction

[run-index.json](run-index.json) records the now-unblinded mapping, snapshot
hashes, six execution results, mechanical checks, two grader assessments,
and decision. Raw generation evidence and the anonymous bundle remain under
`/tmp/writing-style-blind`; grader responses are referenced by path and
hash. These are temporary evidence locations, not hosted artifacts.

The sources can be prepared with the retained held-out corpus procedure.
For the guide, copy exactly README lines 112–183 without changing bytes;
for the abstract, use the complete prepared file. Verify the hashes in
sources.json. Use the native runner with the same cases, model, and effort
for each condition, selecting the corresponding isolated plugin snapshot
or `--baseline`. Never supply the protocol, grading notes, or outputs from
another condition to the editor. A fresh blind grading round needs new
anonymous labels and a hidden key, since this report discloses the mapping.

This is one generation per condition on two reused sources. Random model
variation and grader judgment remain material; it cannot establish a
robust causal effect or a general writing-quality advantage.
