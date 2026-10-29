# Writing plugin behavior cases

These cases check decisions that manifest validation cannot check:
necessary numeric context, first-read understanding, slide/script timing,
and factual preservation during style edits.

- [cold-read.json](cold-read.json) contains reader requests and drafts.
- [anti-slop.json](anti-slop.json) contains style requests and drafts.
- [rubrics.json](rubrics.json) contains the semantic expectations.

Run each case in a fresh context with the relevant skill or reviewer and
its bundled references. Give the reader only that case's request and draft,
plus any explicitly named companions. Do not provide the rubric, other
cases, previous reports, or the suspected failure. Use a temporary working
directory with no project glossary or writing samples unless a case adds
one. Preserve the plugin's relative reference paths when copying it.

For `cold-read`, test both the inline route and the bundled reviewer when
changing their shared rules. For style cases, check the rewritten text
against the source before judging tone. The rubric accepts equivalent
questions and rewrites; it does not require exact output wording. Quoting
a number is insufficient if the question omits a necessary base.

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
