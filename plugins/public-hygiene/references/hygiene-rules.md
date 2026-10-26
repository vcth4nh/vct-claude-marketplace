# Public-output hygiene rules

Everything public is read by people with zero access to this team's
infrastructure, chat history, or experiment trackers. Write for that reader.

The categories below are examples, not the boundary. Any span an external
reader cannot resolve — or should not see — is a leak, listed here or not.

| Category | Leak | Fix |
|---|---|---|
| path | Absolute/local paths: `/home/*`, `/Users/*`, `/scratch/*`, `/tmp/*`, `C:\*` | Docs/commits: repo-relative paths. Papers: name the artifact or config, never a filesystem path. |
| run-id | Run/experiment IDs: W&B runs and sweeps, `exp_v3_fixed`, seed hashes | Describe the method, ablation, or configuration itself. |
| infra | Hosts, IPs, buckets, cluster names, Jira/Slack/Notion URLs, ticket IDs (`DEV-123`) | Omit. Public issue/PR references like `#123` are fine. |
| provenance | People and private channels: "per Alice", "as discussed in standup" | State the rationale itself. Credit people only where public convention expects it (Co-authored-by, acknowledgments). |
| dev-log | Chronology and scrap: "tried X, broke", "hack for demo", TODO/FIXME, commented-out alternatives | Commits: what changed and why. Papers: final method and ablations, not the journey. |
| jargon | Unexpanded internal jargon, acronyms, codenames | Map via the repo leak glossary or define in plain language on first use. |
| meta | AI/session scaffolding: "Here is the updated...", placeholders, tool or session references | Emit only the finalized deliverable. |

Replacements come from the glossary or by generalizing. Never invent facts,
names, numbers, or citations to fill a redaction.
