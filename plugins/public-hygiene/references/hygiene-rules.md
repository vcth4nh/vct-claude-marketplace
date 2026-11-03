# Public-output hygiene rules

Everything public is read by people with zero access to this team's
infrastructure, chat history, or experiment trackers. Write for that reader.
Use the target audience's normal field knowledge: unfamiliarity alone does
not make a standard technical term internal jargon.
A term the public draft explains is not unexpanded jargon either; an
explicit glossary designation still takes precedence.

Judge material in the artifact's intended genre. An incident timeline,
public design discussion, or deliberate build-history section is not
private development scrap merely because it describes work in progress.
Check its concrete disclosures; do not delete the whole narrative by category.
Prior publication or a genre label does not waive checks for private paths,
infrastructure, provenance, glossary terms, or the stated anonymity rules.
Treat self-contained test measurements and observations as evidence. Check
any embedded private paths, identifiers, names, or other protected details
under their own categories.

Do not flag a package, repository, or marketplace identifier in the draft's
own installation instructions solely because its spelling is unfamiliar or
no separate release approval was supplied. Still check explicit internal
designations, glossary entries, credentials, private hosts and paths, and
anonymity constraints in those same instructions.

The categories below are examples, not the boundary. Any span an external
reader cannot resolve — or should not see — is a leak, listed here or not.

| Category | Leak | Fix |
|---|---|---|
| path | Absolute/local paths: `/home/*`, `/Users/*`, `/scratch/*`, `/tmp/*`, `C:\*` | Docs/commits: repo-relative paths. Papers: name the artifact or config, never a filesystem path. |
| run-id | Run/experiment IDs: W&B runs and sweeps, `exp_v3_fixed`, seed hashes | Describe the method, ablation, or configuration itself. |
| infra | Hosts, IPs, buckets, cluster names, Jira/Slack/Notion URLs, ticket IDs (`DEV-123`) | Omit. Public issue/PR references like `#123` are fine. |
| provenance | People and private channels: "per Alice", "as discussed in standup" | State the rationale itself. Credit people only where public convention expects it (Co-authored-by, acknowledgments). |
| dev-log | Private working notes or scrap left in the deliverable: "hack for demo", unaddressed TODO/FIXME, abandoned alternatives unrelated to its purpose | Remove the working notes; preserve deliberate public history, evidence, and design rationale. |
| jargon | Unexpanded internal jargon, acronyms, codenames | Map via the repo leak glossary or define in plain language on first use. |
| meta | AI/session scaffolding: "Here is the updated...", placeholders, tool or session references | Emit only the finalized deliverable. |

Replacements come from the glossary or by generalizing. Never invent facts,
names, numbers, or citations to fill a redaction.
