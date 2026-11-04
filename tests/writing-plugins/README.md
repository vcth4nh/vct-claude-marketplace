# Writing plugin behavior cases

These cases check decisions that manifest validation cannot check:
necessary numeric context, first-read understanding, slide/script timing,
factual preservation during style edits, and output modes.

[0.3.0 validation](validation-0.3.0.md) records the adoption results and
their limits.
[The real-document pilot](real-documents/results-0.3.1.md) records the eight
artifact tests, controls, fixes, and remaining limitations for 0.3.1.
[The held-out comparison](heldout/README.md) adds three unfamiliar artifacts
and matched medium-effort model conditions.
[Its results](heldout/results-0.4.0.md) retain failures and targeted retests
for public-hygiene 0.4.0 and anti-slop 0.3.2.
[Focused reliability checks](reliability/results-0.4.1.md) cover checkpoint
validation and leak evidence for public-hygiene 0.4.1.
[The blind style trial](style-comparison/README.md) records the rejected
length-rule candidate; anti-slop remains at 0.3.2.

- [cold-read.json](cold-read.json) contains reader requests and drafts.
- [anti-slop.json](anti-slop.json) contains style requests and drafts.
- [rubrics.json](rubrics.json) contains the semantic expectations.
- [reader-modes.json](reader-modes.json) contains optional comprehension
  and sequential requests, including an apply request after a readback.
- [reader-modes-rubrics.json](reader-modes-rubrics.json) contains their
  separate expectations and sequential tool-trace checks.
- [leak-evidence.json](leak-evidence.json) contains the paired public narrative
  and private additions; [leak-evidence-rubrics.json](leak-evidence-rubrics.json)
  keeps expectations separate from reviewer input.

Run each case in a fresh context with the relevant skill or reviewer and
its bundled references. Give the reader only that case's request and draft,
plus any explicitly named companions. Do not provide the rubric, other
cases, unrelated prior reports, or the suspected failure. Use a temporary working
directory with no project glossary or writing samples unless a case adds
one. Preserve the plugin's relative reference paths when copying it.
For a case with a `files` object, create those relative files inside the
temporary workspace. A `prior_report` is conversation context for the
apply request, not an author answer. Only supply fields present in that
case; do not substitute its rubric for missing setup.

For `cold-read`, test both the inline route and the bundled reviewer when
changing their shared rules. For style cases, check the rewritten text
against the source before judging tone. The rubric accepts equivalent
questions and rewrites; it does not require exact output wording. Quoting
a number is insufficient if the question omits a necessary base.

For file-edit cases, compare actual file bytes before and after: protected
spans must survive, prose must change when requested, and review-only or
path-only requests must not write. Give an explicit edit case permission
to edit its temporary target; a denied write does not prove restraint.
For embedded drafts, check the complete response for prefatory text,
change reports, or follow-up offers as well as the artifact's meaning.

For sequential cases, keep preparation scratch files outside the source
tree. Run the bundled preparation helper through the native parent, and
verify that the ordered draft chunks concatenate byte-for-byte to
the source (exclude separately mapped forward-reference excerpts). Inspect
the handoff trace: the parent receives a completed first-read checkpoint
before supplying the next chunk. Neither the whole source nor unrelated
future chunk paths may be supplied to an earlier stage. A resumed reader
keeps its prior public context; a fresh replacement receives the prior
public prefix and checkpoints verbatim. Check same-slide notes and forward-reference lookups
against the fixture. Run matching ordinary audits to assess whether the
extra sequence finds additional gaps; equal findings demonstrate parity,
not improved recall. An unavailable reviewer or failed sequence is
incomplete, never a passing test.

The preparation and report-assembly helpers have deterministic tests for
byte preservation, forward excerpts, line endings, invalid input, ordered
checkpoints, and refusal to overwrite existing files:

```sh
python3 -m unittest discover -s tests/writing-plugins -p 'test_*.py' -v
```

Record the plugin revision or file hashes, harness, model, actual output,
and pass/fail reasons. A single successful run is a pilot. Repeat cases
whose behavior is known to vary, and retain failures rather than selecting
only successful outputs. Compare a suspected regression with the original
instructions before adding another rule.

Direct instruction probes do not verify native plugin dispatch. When
changing agents or handoffs, also run the installed harness and inspect
which agent ran, which context it received, and whether files changed.
Useful integration cases include a PR whose diff resolves a term while a
private project note defines a different term, and an anonymous submission
with an explicitly approved public system name.

Keep these test files outside the plugin directories so installation does
not expose the rubric as reviewer context. These checks assess writing
behavior; they are not credential scanning or proof of publication safety.
