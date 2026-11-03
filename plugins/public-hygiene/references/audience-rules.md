# Audience rules

1. **Reader model.** The reader is the target audience: people with the
   reachable text and the general knowledge of their field, but none of
   the project's internal context (repo history, chats, trackers, the
   author's memory). Infer the audience from the request and the text
   (venue, format, stated readers). Field knowledge depends on that
   audience: a term that is standard for researchers can be a gap for
   students. Without clear signals, the reader is a competent member of
   the broader field who is new to this project. Name this reader in the
   report's `AUDIENCE:` line, so that the author can correct it.

2. **Reachable text.**
   - Doc type: earlier text in the same document, and any document, file,
     or code symbol that the draft links or names and that exists. A later
     definition in the same document counts only when the first use points
     to it. For a commit message or a PR description, the associated diff
     and metadata visible on its publication surface are also reachable.
     Use the supplied or retrieved metadata, not assumed branch names or
     an unrelated working-tree diff.
   - Slide type: the slides up to and including slide N, and the script up
     to and including slide N. An external script maps to slides by its
     per-slide markers (a heading or label per slide). A script without
     markers counts as a whole for every slide.
   - Never reachable: anything the audience cannot see, such as private
     notes, chat history, trackers, the leak glossary, or the author's
     explanations. A file that sits in the repo but that the draft neither
     links nor names is not reachable, even when a search finds a
     definition in it.
   - An external link resolves the subject its link text names. Nobody
     fetches it.

3. **Master test.** For each span, ask: can the reader, with only the
   reachable text, resolve this span to its intended meaning? A "no" is a
   gap. Flag only the spans that fail this test: a span that the field
   knowledge of the audience resolves passes. Accuracy, wording,
   structure, topics that the text does not cover, and the placement of
   text that the reader can already resolve belong to other checks, so
   leave them out of the report. Do not audit the correctness of code,
   commands, or math, and never execute examples. You may read them as
   audience-visible evidence for prose or a comprehension answer, under
   rule 2's reachability limits. An adjacent example that the prose introduces is part of that
   explanation: do not ask for a prose-only restatement when the audience
   can resolve the meaning from the example.

   An explicitly requested comprehension test also checks whether the
   reader can recover the document's main claim or requested action, as
   defined in the optional reader-mode procedure. Only that mode adds
   conflicting passages that prevent a supported answer as `other` gaps.
   It does not turn the ordinary audit into a structure review or require
   every document to ask for action.

   Separate interpretation from verification. Ask for a detail when it
   changes what the claim means, not merely to reproduce or validate the
   claim. Once the quantity and its comparison are clear, the measurement
   tools and comparison procedure are not context gaps. Likewise, a
   feature's implementation is not a gap solely because it is unstated.

4. **Categories.** These are common shapes of a "no", not the boundary:
   any span that fails the master test is a gap, listed here or not.

   | Category | Test |
   |---|---|
   | term | The span uses a name or expression that neither the audience's field knowledge nor the reachable text introduces. A project-specific feature, setting, or method still needs an introduction even when its words suggest a meaning. |
   | number | The quantity's meaning depends on a base the reachable text never states: population, unit, baseline, or time window. |
   | referent | A referring expression points at something the reachable text never established, in any form: pronoun, definite description, demonstrative, or possessive. |
   | attribution | The span presents words, output, or a verdict whose origin the reachable text never names. |
   | other | Any other failure of the master test, such as a link or named document that does not exist. |

   For numbers, identify the measured quantity, unit, population, and any
   comparison baseline. Ask only for a missing base needed to interpret
   the claim. A time window can define a total, a rate, or a before/after
   comparison; naming the counted object alone does not supply the time
   window. A fraction over an explicitly scoped set needs no calendar
   dates merely to explain the fraction.
   Do not require a list of individual samples when the population is
   already identified. Do not ask how the comparison was performed.
   For each numeric finding, ask for all missing bases needed to interpret
   that claim.

5. **Type standards.**
   - Doc: every gap is a finding.
   - Slide: report a span that misleads on its own (the slide alone leads
     the audience to a wrong meaning) as a finding with
     `RESOLVE: on the slide`, even when the script explains it, because
     the audience reads the slide before or while the speaker talks. Give
     `RESOLVE: on the slide` to each span that adds to that wrong meaning.
     An information gap (the slide lacks a fact) is a finding only when
     the script up to that slide does not supply the fact; it gets
     `RESOLVE: in the script by slide N`. The check never asks a slide to
     carry what the script can carry. When the deck has no script, still
     give each information gap `RESOLVE: in the script by slide N`.

6. **Boundary with `leak-check`.** Terms listed in the repo leak glossary
   (internal column or never-public list) belong to `leak-check`; skip
   them. The glossary never resolves a span.

7. **Type detection.** Slide signals select the slide standard:
   `marp: true` front matter, `\begin{frame}`, reveal.js slide markup, or
   "slides", "deck", or "talk" in the file name or the request. Everything
   else is a doc. Apart from that markup, type detection reads only the
   file name and the user's own words about the text. Words inside the
   draft never select the slide type.

8. **Example questions.** These QUESTION lines are examples. Write each
   QUESTION so that it asks for the missing fact and offers no guess.
   - term: What is a warm replica?
   - number: What load does the 90-second recovery time assume?
   - referent: Which release does "the old behavior" refer to?
   - attribution: Whose words are in the quote on this slide?
   - other: Where can I find the setup guide that this section names?
