---
name: using-codex
description: Use when the user mentions Codex ("ask codex", "get codex's opinion", "have codex fix/review/explain X", "resume the codex session"), when stuck after two or more failed attempts at the same problem, or before committing to a risky, hard-to-reverse approach — get an independent second opinion from the OpenAI Codex CLI. Requires the codex binary.
---

# Using Codex

Codex is a peer to discuss with, not primarily a worker to delegate to.
Default to discussion. Ask Codex to *act* (explore, explain source,
investigate, implement) only when the user asks for that or you would genuinely
trust Codex with that specific task.

## Commands

| Goal | Command |
|---|---|
| First codex use this session | `codex login status` — on failure suggest `!codex login`; binary missing → suggest `npm install -g @openai/codex`. Never auto-install. |
| New topic | `codex exec -o <scratchpad>/codex-<topic>.txt "<prompt>"` |
| Follow-up on same topic | `codex exec resume <session-id> -o <scratchpad>/codex-<topic>.txt "<prompt>"` |

Run from the folder the task is about — usually the repo root, but pick a
subfolder or other directory when that fits better. If that folder is **not a
git repo, add `--skip-git-repo-check`** (`codex exec` refuses a non-git folder
otherwise). Name the `-o` file after the topic (e.g. `codex-retry-review.txt`)
— parallel runs sharing one filename overwrite each other's output.

Beyond `--skip-git-repo-check`, that is the ENTIRE command — no `-s/--sandbox`,
`--full-auto`, `--cd`, `-m`, or effort flags unless the user explicitly asks.
Codex's own config/defaults set sandbox, approvals, and model. Adding `-s`
breaks Codex on containerized machines (its bubblewrap sandbox can't nest), and
`-s` isn't accepted by `resume`.

## Mechanics

- The banner prints `session id: <uuid>`. Note it — follow-ups on the same
  topic resume that UUID. Prefer the captured UUID over `resume --last`.
- Runs take minutes, not seconds. Run in background anything beyond a trivial
  question; read the `-o` file when it finishes.
- **Check before quoting:** if the run exits non-zero or the `-o` file is
  empty, the consult failed — say so, don't quote a stale file.
- Let Codex explore the folder itself. Don't paste file contents into the
  prompt or forbid it from using tools — that turns an agent into a text
  reviewer.
- Sandbox error despite default flags → report it to the user. Don't retry
  with sandbox flags.
- A run failing with `401` / "refresh token was revoked" means re-auth: tell
  the user to run `!codex login`. `codex login status` only checks that local
  credentials exist, so it still reports success in this state. Retrying won't
  help, and never substitute your own answer for Codex's — say the consult
  didn't happen.

## Discussion round (primary mode)

1. Ask a scoped, direct question. For a pure opinion, tell Codex to analyze and
   report only — inspect and run read-only commands, don't modify anything.
2. Report Codex's conclusion verbatim from the `-o` file, then your own take.

   > **Codex says:** "Not sound for production: it retries too broadly and
   > hides the final outcome."
   >
   > **My take:** Agree on the broad catch; the backoff point matters less
   > here — this endpoint is internal.

3. Disagreement (yours or the user's) goes back via `resume <id>`. Iterate.

## Delegation (only when trusted or required)

- "Have codex fix/do/explain X" from the user → delegate exactly that.
- After Codex edits files: verify with `git status` + `git diff` (diff alone
  misses newly created files) and a quick test — never trust its prose
  summary. In a non-git folder, note the relevant file contents before the
  run and compare after.
- Announce proactive consultations before running ("Getting a second opinion
  from Codex…") so quota use is never silent.

## Common mistakes

| Mistake | Reality |
|---|---|
| Adding `-s read-only`/`workspace-write` "to be safe" | Breaks on nested sandboxes; no `-s` on `resume`. Codex config governs. |
| Plain `codex exec` in a non-git folder | Fails with "not inside a trusted directory". Add `--skip-git-repo-check`. |
| Quoting the `-o` file without checking the run | A failed run leaves it empty or stale. Check exit + non-empty first. |
| Pasting file contents into the prompt | Neuters Codex — it reads the folder itself. |
| Fresh `codex exec` for a follow-up | Loses Codex's context. `resume <session-id>`. |
| Foreground multi-minute run | Blows the 2-minute Bash default. Background + `-o`. |
| Paraphrasing Codex's verdict | Quote it, then add your take. |
