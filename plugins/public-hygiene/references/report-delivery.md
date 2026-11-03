# Delivering independent reviews

The reviewer's saved report is the authoritative result. Deliver a link
and its verdict; regenerating a long report in the parent's answer can
change quotes or omit findings.

## Parent

1. Create a uniquely named temporary directory outside the reviewed source
   tree, in a location the harness permits writing. Reserve a new absolute
   report path there; do not create the report itself. Use neutral `.txt`
   filenames such as `review-001.txt` and `reading-final.txt`. Claude Code
   rejects subagent Write calls for Markdown basenames beginning with
   REPORT, SUMMARY, FINDINGS, or ANALYSIS (case-insensitive); avoid those
   prefixes and the `.md` extension for reviewer outputs. Use this naming
   convention before dispatch, not a retry through another tool after denial.
   Leak reports contain the exact private spans they find and must not be
   copied into the repository. Record hashes of the supplied draft and
   companion files before dispatch.
2. Include that output path in the clean handoff. The reviewer may create
   that one report; the draft, companions, instructions, and any earlier
   reports remain read-only. Claude reviewers use only Read, Grep, Glob,
   and Write. Where a harness exposes file operations through a shell,
   restrict the reviewer to equivalent reads/searches and creation of its
   designated report; do not execute draft content or permit other mutations.
   This is an instruction limit, not filesystem isolation: harness permissions must
   also allow the designated scratch write. A denied write is incomplete.
3. After return, read the saved report and compare the input hashes.
   Require the reviewer's specified report format and terminal verdict.
   A missing or malformed report, or a changed input, makes the
   check `VERDICT: INCOMPLETE`. Do not substitute the reviewer's chat status
   for the file, repair its findings yourself, or silently rerun after a
   mutation. Retain the evidence and report which check failed.
   If a required read or hash check cannot run, the check is also incomplete;
   an unsupported claim that inputs stayed unchanged does not replace it.
   An incomplete delivery contains the reason, `VERDICT: INCOMPLETE`, and
   links to any saved records. Do not restate findings or readback from chat,
   or treat an unsaved report as a partial publication verdict.
4. Deliver a clickable link to the report and copy its terminal `VERDICT`
   line exactly. Do not repeat or summarize its findings, readback, or
   checkpoints. A brief offer to apply fixes is allowed; the cold-read
   workflow still requires author answers. If the user requests inline
   delivery, reproduce the saved report verbatim without an extra audit.
5. On a later apply/fix request, read the report file again. Use its findings
   and the author's answers, not a remembered version of the report.

Sequential reading uses separate checkpoint files and a final summary;
[reader modes](reader-modes.md) defines validation and assembly. A complete
stage has no publication verdict, so validate its terminal `STAGE` line
before advancing. Hash each returned checkpoint and recheck prior hashes
after every subsequent stage and before assembly. Changed checkpoints make
the sequence incomplete. Keep report files separate from the chunk directory.

## Reviewer

The handoff must provide a new absolute output path outside the source
tree. Read only the permitted review inputs. As your last file operation,
write the complete report once to that path, without wrapping it in a code
fence or adding a preface. The verdict (or checkpoint's stage status) must
be the last line, with no commentary or blank lines after it. Never overwrite an existing
file or change a draft, companion, instruction, or previous checkpoint.
Then return only the path and the report's terminal verdict (or terminal
stage status for a sequential checkpoint). If the path is missing, already
exists, or cannot be written, return `VERDICT: INCOMPLETE` with the reason;
do not write elsewhere or pretend that a chat-only report was saved.

These checks preserve observable report bytes and detect changed supplied
files. They do not prove who wrote a file, the order of reads, or the
semantic quality of the findings. Evaluation still needs tool traces and
independent comparison with the source.
