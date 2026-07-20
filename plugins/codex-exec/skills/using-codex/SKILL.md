---
name: using-codex
description: Use when the user mentions Codex ("ask codex", "get codex's opinion", "have codex fix/review/explain X", "resume the codex session"), when stuck after two or more failed attempts at the same problem, or before committing to a risky, hard-to-reverse approach — get an independent second opinion from the OpenAI Codex CLI. Requires the codex binary.
---

# Using Codex

Codex is a peer to discuss with, not primarily a worker to delegate to.
Default to discussion. Ask Codex to *act* on the repo (explore, explain
source, investigate, implement) only when the user asks for that or you would
genuinely trust Codex with that specific task.

## Commands

| Goal | Command |
|---|---|
| First codex use this session | `codex login status` — on failure suggest `!codex login`; binary missing → suggest `npm install -g @openai/codex`. Never auto-install. |
| New topic | `codex exec -o <scratchpad>/codex-<topic>.txt "<prompt>"` |
| Follow-up on same topic | `codex exec resume <session-id> -o <scratchpad>/codex-<topic>.txt "<prompt>"` |

Name the `-o` file after the topic (e.g. `codex-retry-review.txt`) — parallel
runs sharing one filename overwrite each other's output.

Run from the repo root. That is the ENTIRE command — no `-s/--sandbox`,
`--full-auto`, `--cd`, `-m`, or effort flags unless the user explicitly asks.
`~/.codex/config.toml` already sets sandbox, approvals, and model. Adding `-s`
breaks Codex outright on containerized machines (its bubblewrap sandbox can't
nest), and the flag doesn't exist on `resume`.

## Mechanics

- The banner prints `session id: <uuid>`. Note it — follow-ups on the same
  topic resume it. `resume --last` is machine-global (another session may be
  "last"); only safe immediately after your own run.
- Runs take minutes, not seconds. Run in background anything beyond a trivial
  question; read the `-o` file when it finishes.
- Let Codex explore the repo itself. Don't paste file contents into the prompt
  or forbid it from using tools — that turns an agent into a text reviewer.
- Sandbox error despite default flags → report it to the user. Don't retry
  with sandbox flags.
- A run failing with `401` / "refresh token was revoked" means re-auth: tell
  the user to run `!codex login`. `codex login status` only checks that local
  credentials exist, so it still reports success in this state. Retrying won't
  help, and never substitute your own answer for Codex's — say the consult
  didn't happen.

## Discussion round (primary mode)

1. Ask: `codex exec` with a scoped, direct question.
2. Report: Codex's conclusion verbatim from the `-o` file, then your own take.

   > **Codex says:** "Not sound for production: it retries too broadly and
   > hides the final outcome."
   >
   > **My take:** Agree on the broad catch; the backoff point matters less
   > here — this endpoint is internal.

3. Disagreement (yours or the user's) goes back via `resume <id>`. Iterate.

## Delegation (only when trusted or required)

- "Have codex fix/do/explain X" from the user → delegate exactly that.
- After Codex edits files: verify with `git diff` and a quick test — never
  trust its prose summary alone.
- Announce proactive consultations before running ("Getting a second opinion
  from Codex…") so quota use is never silent.

## Common mistakes

| Mistake | Reality |
|---|---|
| Adding `-s read-only`/`workspace-write` "to be safe" | Breaks on nested sandboxes; no `-s` on `resume`. User config governs. |
| Pasting file contents into the prompt | Neuters Codex — it reads the repo itself. |
| Fresh `codex exec` for a follow-up | Loses Codex's context. `resume <session-id>`. |
| Foreground multi-minute run | Blows the 2-minute Bash default. Background + `-o`. |
| Paraphrasing Codex's verdict | Quote it, then add your take. |
