# Writing plugin 0.3.0 validation

Checked on 2026-10-29 with Claude Code 2.1.312 and its default
`claude-fable-5-1` model. Native runs loaded local plugin snapshots into
isolated temporary workspaces, with MCP and persistent sessions disabled.
Readers received raw cases, not the separate rubrics. Logs recorded model,
plugin hashes, prompts, tool calls, responses, and before/after file hashes.

The corpus now contains 32 behavioral cases. The adoption checks exercised
all 15 new cases, selected existing regressions, and additional variants;
they were not a rerun of every historical case.

## Verified behavior

| Area | Evidence |
|---|---|
| Embedded style output | After fixing an observed preface/follow-up failure, three commit-message trials and one academic trial returned only the requested artifact. |
| File modes | Explicit editing changed the intended prose and preserved protected bytes. Review-only and path-only requests left files unchanged. |
| Meaning and voice | Checks retained factual negations, technical names, uncertainty, useful explanation, math, citations, and code. The academic rhythm probe retained varied sentence shapes without a fixed alternation. |
| Comprehension | Readers recovered the requested actor/action/deadline, identified an ambiguous approval request and contradictory access rules, and treated informational text as needing no call to action. Answers cited source passages. |
| Apply guard | A plain `apply` after a readback, with no author answers, left the draft unchanged while editing tools were available. |
| Sequential reading | Four final trials invoked the preparation helper, reconstructed source bytes exactly, and returned checkpoints before subsequent chunk handoffs. Reviewer traces showed no access to future chunks, manifests, or original source paths. |
| Reachability | An explicit forward reference resolved its term; an unannounced later definition remained a first-use gap. Same-slide notes resolved terms, while later-slide notes arrived too late. |
| Combined modes | The slide trial completed sequential reading before its source-backed comprehension readback. |
| Missing helper | With Bash unavailable but scratch-file writes allowed, the mode returned `INCOMPLETE`, dispatched no reading stages, and created no substitute chunks. |
| Ordinary review | The existing clean release note and misleading-slide cases retained their expected outcomes. Ordinary reading already found the seeded gaps in both sequential comparison cases. |

Seven deterministic unittest methods passed, including LF/CRLF variants,
absent terminal newlines, exact forward excerpts, intact multiline blocks
at supplied boundaries, invalid input, and overwrite protection. All four
skill validators, both plugin validators, marketplace validation, version
matching, fixture/rubric matching, relative links, and whitespace checks
passed. Plugin validation retained the existing optional-icon warnings.

## Corrections and limits

The style work used 15 native attempts: an initial eight, four checks after
the embedded-output fix, and three final checks. Reader-mode work retained
33 attempts: 29 completed responses and four intentional interruptions.
These totals include failed prototypes and harness diagnostics, not just
passing runs. The final reader evidence comprises nine mode/apply cases,
four ordinary controls, and the unavailable-helper check.

Manual chunk copies once added a terminal newline. Single-call readers
also deferred observations until the final report despite instructions.
Those failures led to the deterministic helper and parent-controlled
stages. A later helper-denial trial exposed a hand-copy fallback; the
final guard requires a corrected invocation or an incomplete result.
Permission-rule failures in the test harness were recorded separately.
One intended clean informational fixture had ambiguous field coverage;
its source was clarified before treating it as a clean control.

The native harness exercised the fresh-reader fallback with prior public
text and checkpoints; same-reader resumption was not exercised. A final
chunk may return its checkpoint and consolidation together. No final
trial introduced context findings only during consolidation.

These are short synthetic cases, not an accuracy estimate. Some additional
questions varied, including the retention baseline, an operator reference,
and a slide heading. One commit-message variant repeated its subject in
the body despite satisfying artifact-only output. Sequential reading found
the same seeded gaps as ordinary reading in the two comparison cases;
the trials do not establish a reliability advantage. It remains opt-in
and experimental. None of these checks establish credential-scanning or
publication-safety guarantees.
