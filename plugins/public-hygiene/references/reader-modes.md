# Optional reader modes

Load this reference only when the user requests comprehension testing,
sequential reading, or both. Ordinary `cold-read` keeps its existing scope
and report. These modes use the same audience, reachable-text rules,
read-only reviewer, and author-only corrections.

## Comprehension

### Prepare the handoff

Request `MODE: comprehension` from a fresh reader. Include the draft and
its public companions, plus any questions the user wants tested. Keep
expected answers and private author explanations out of the handoff. If
there are no supplied questions, let the reader derive two or three from
the document's main claim, scope, or decision. Do not manufacture a quiz
about topics the document does not need to cover.

### Reader procedure

Run the context audit, then demonstrate what the text communicates:

- For an action-oriented artifact such as a proposal, request, or bug
  report, state in one sentence what the audience is being asked to do.
  Quote the passage supporting that reading. When the action is ambiguous,
  say so and report the relevant span as a context question. An informative
  document needs no call to action; mark the action check not applicable.
- Answer the supplied questions, or two or three questions derived from
  the public text. For each answer, quote supporting text and identify its
  location. Answer only to the extent that reachable text supports it.
  Mark an unsupported or ambiguous part unresolved and ask for the missing
  fact; do not choose a plausible interpretation to make the test pass.
- Check that each answer preserves the source's scope, conditions, and
  negations. If passages support conflicting answers, quote both and ask
  which applies. This checks communicated meaning, not external truth.

After `AUDIENCE`, add a `READBACK` section: the action (or not
applicable), then each question, answer, and supporting quote/location.
Put any resulting gaps in the ordinary numbered findings, grouped with
duplicates from the context audit. A question outside the document's
purpose may be marked outside scope without failing the audit; a missing
answer needed to interpret its claim or request is a gap.

The normal verdict covers unresolved context, including the readback.
After relaying the report, the author can correct a mistaken readback or
supply missing facts. Do not use private expected answers to silently
rewrite the reader's report or declare its reading correct. Apply only
author-provided corrections under the skill's existing apply workflow.
The readback's answers are never author answers: an "apply" request alone
does not authorize turning them into new document facts.

## Sequential reading (experimental)

Use this mode to test where a first-time reader loses context. It adds
tool calls and is intended for longer text, not every publication check.

### Prepare the handoff

1. Read the plain-text or Markdown source and choose section or paragraph
   boundaries; for a Markdown deck, use one complete slide with its notes.
   Keep code fences, tables, quotations, front matter, and note blocks
   intact. For other formats, use a supplied text export with its reading
   order intact or report this mode as incomplete. With only one meaningful
   chunk, say that the mode adds no sequential test and run the ordinary
   fresh-reviewer audit (plus comprehension if requested).
2. Choose a new temporary destination outside the source tree. Use the
   [preparation script](../scripts/prepare_reader_chunks.py) to copy bytes
   into it:

   ```text
   python3 SCRIPT SOURCE NEW_DIRECTORY --starts 1 8 15 --forward 1:15:20
   ```

   Resolve SCRIPT relative to this reference. `--starts` lists the actual
   1-based starting lines of the chosen chunks, always beginning with 1.
   Optional `--forward CHUNK:START:END` maps an explicit forward reference
   from that chunk to an inclusive source-line excerpt. Supply real line
   boundaries, not these example numbers. The script preserves line endings
   and an absent terminal newline, verifies concatenation, and writes a
   manifest of neutral filenames and source locations. It does not parse
   markup: choosing intact boundaries remains the parent's job. Temporary
   copies do not authorize editing the source. Manifest paths are relative
   to NEW_DIRECTORY; resolve them before each handoff.
3. Keep the full manifest with the parent. For every stage, include the
   absolute path of the bundled reader instruction file from this plugin
   snapshot, so the reviewer can resolve its relative rule links. Hand it
   `MODE: sequential`, the current chunk path and source location,
   stage number, type, and the user's audience/venue words. Include only
   forward-reference excerpts mapped to this chunk. Never hand over the
   source path, future chunk paths, summaries, or terms to watch. The parent
   may have read the source; the initial reviewer must be fresh.
   If the reader cannot locate the supplied instructions or their bundled
   rules, stop as incomplete; do not search other checkouts or snapshots.
4. Make only reachable companions available at each step. For a marked
   slide script, provide the script through that slide, not later notes.
   An unmarked script remains reachable as a whole under audience rule 2.
   Other linked/named companions become reachable when the reader encounters
   their reference. Preserve relative-link resolution using the source
   directory without giving the reviewer the original draft path.
   Do not map a future definition merely because the parent thinks it will
   help: the current text must explicitly point to it.

If the helper fails, correct a recoverable invocation error or report the
mode incomplete; do not fall back to hand-copying chunks. If byte-preserving
preparation or a fresh reviewer is unavailable, report the mode incomplete.
Do not issue a sequential PASS after reading the whole
source at once. Use `VERDICT: INCOMPLETE` when the requested sequence or a
required forward lookup cannot be performed, retaining findings already made.

### Parent-controlled stages

Dispatch one chunk stage, wait for its returned checkpoint, and only then
send the next chunk. Resume the same reviewer without adding private
context. If the harness cannot resume it, use a fresh reviewer with the
prior public chunks and the returned checkpoints verbatim, plus the new
chunk. Never substitute the parent's interpretation for a checkpoint.

For each chunk stage, the reviewer:

- Reads the current chunk and only its reachable companions. The original
  draft is not a companion. Do not open the manifest, list the chunk
  directory, or read/search any unprovided sibling chunk or excerpt.
- Uses a mapped forward excerpt only when the current text points to it,
  records the lookup, and reads no unrelated future content. A missing
  mapping makes the stage incomplete. A later unannounced definition cannot
  erase a prior first-use gap.
- Applies the ordinary slide rules: same-slide notes may fill an information
  gap, future notes cannot, and a misleading slide remains a finding.
- Returns `FIRST READ <chunk/location>` with quoted gaps and their context
  questions, or no gaps, followed by `STAGE: COMPLETE` or `STAGE: INCOMPLETE`.
  This is a returned reading outcome, not internal reasoning or a promise
  to emit a record later. An incomplete stage also ends with
  `VERDICT: INCOMPLETE`; a complete stage has no publication verdict unless
  it also performs the final consolidation below.

Stop on an incomplete stage and relay its report verbatim; do not advance
or label a partial prefix as passed. Once all stages return, ask
the reviewer to consolidate the public prefix and immutable checkpoints.
The last chunk's call may return its checkpoint and then consolidate in
the same response, since no unread chunk remains. It must complete that
stage before any readback or publication verdict.
It returns `AUDIENCE`, the first-read records verbatim, any requested
`READBACK`, then the normal consolidated findings and publication verdict.
Consolidation may only merge checkpoint findings and add gaps established
by a requested readback; it must not run another whole-document context
audit. Merge duplicate findings but retain their first locations and records;
later definitions do not erase unannounced first-use gaps. When combined
with comprehension, do the readback only in this final consolidation.

Sequential exposure is an instruction boundary, not a filesystem sandbox.
When evaluating this mode, inspect the returned stage results and subsequent
handoffs: each checkpoint must arrive before the next chunk is supplied.
Also inspect reviewer reads and searches for the original source, manifest,
and unprovided sibling files; handoff isolation alone is insufficient.
A final report alone cannot prove the sequence.
