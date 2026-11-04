# Public-output hygiene rules

Everything public is read by people with zero access to this team's
infrastructure, chat history, or experiment trackers. Write for that reader.
Use the target audience's normal field knowledge: unfamiliarity alone does
not make a standard technical term internal jargon.
A term the public draft explains is not unexpanded jargon either; an
explicit glossary designation still takes precedence.

Require a concrete disclosure concern for each finding: evidence of private
context, a stated publication restriction, or unfinished working material
left in the deliverable. Unfamiliar spelling, informal tone, and the absence
of separate release approval are not that evidence. An explained service or
data-field name, public byline, or relevant participant attribution does not
become a leak on those grounds alone.
When a concrete concern exists but its intended disclosure is unclear,
mark it AMBIGUOUS and ask the specific question needed to decide. State the
observed concern without declaring the material private merely because its
approval is unknown. Explicit private/internal designations, glossary terms,
private infrastructure or working paths, and stated anonymity constraints
still require checking even when the surrounding text explains them.

For an explicit submission request with identifying text and no stated
anonymity policy, ask one AMBIGUOUS question about whether that identifying
material is allowed. Do not assume anonymous review or add this policy
question to a generic paper or public-article review.

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

The categories below are examples, not the boundary. Apply the evidence
test to other disclosures too. Missing explanations, inconsistent claims,
or awkward prose alone belong to context or style review, not leak findings.

| Category | Leak | Fix |
|---|---|---|
| path | Working paths that expose machine-specific or private layout, such as a user's home or experiment scratch tree | For a flagged path, use a repo-relative path in docs/commits, or name the artifact or config in papers. |
| run-id | Private run/experiment IDs: W&B runs and sweeps, `exp_v3_fixed`, seed hashes | Describe the method, ablation, or configuration itself. |
| infra | Private infrastructure or operational identifiers whose exposure raises a concrete concern: hosts, IPs, buckets, clusters, internal URLs, or ticket IDs | Omit the private detail, or ask whether it is intended for disclosure when that is unclear. Public service coordinates and public issue/PR references are not leaks by themselves. |
| provenance | Attribution that exposes private communications or relationships: "as discussed in the private incident channel" | State the public rationale. Preserve bylines and participant attribution relevant to the intended genre; a person's name alone is not evidence of private provenance. |
| dev-log | Private working notes or scrap left in the deliverable: "hack for demo", unaddressed TODO/FIXME, abandoned alternatives unrelated to its purpose | Remove the working notes; preserve deliberate public history, evidence, and design rationale. |
| jargon | Jargon, acronyms, or codenames supported as private/internal by the glossary, an explicit designation, or concrete private context | Use the approved glossary replacement or ask how to generalize. Defining a private name does not clear it for publication. |
| meta | AI/session scaffolding: "Here is the updated...", placeholders, tool or session references | Emit only the finalized deliverable. |

Apply the same evidence test to documented service coordinates and paths:
absolute syntax or a hostname alone does not establish a private working
location. A generic example does not exempt actual private details within it.

Replacements come from the glossary or by generalizing. Never invent facts,
names, roles, numbers, or citations to fill a redaction. Replacing a person
with "the on-call engineer" requires that role to be stated in the source.
