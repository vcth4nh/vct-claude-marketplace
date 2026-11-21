---
name: doc-care
description: Use when creating, updating, or reviewing project documentation, including documentation changes during implementation, or when the user asks to remove duplicate, misplaced, or stale documentation.
---

# Doc Care

Apply these rules to public and internal project docs. For a review-only
request, report findings and proposed edits without changing files. For
an edit request, apply the rules within the task's scope.

## Rules

1. Before editing a doc, identify its reader and the question it answers; follow the project's stated document roles.
2. Before adding a line, ask whether that reader could do their job without it; if yes, omit it or put it where the reader who needs it will look.
   Include a quantity only if it helps the reader. Give an exact count when precision matters. When only scale or coverage matters, use an estimate or a descriptive word the evidence supports. Otherwise, omit the quantity.
3. Search before adding; update an existing fact where it stands so there is one place to maintain it.
4. Link to facts held elsewhere to prevent drift; repeat only what a document read on its own needs.
5. Keep how-to docs procedural; results and status, including dates and untested cases, belong in the project's designated record because they age separately.
6. If no results record exists, put results in your report so routine work does not create another document to maintain.
7. Correct every claim the change makes false in the same change, including "not tried," "not supported yet," and "currently," so docs agree.
8. Keep incidental details of your machines, accounts, and data out of project guidance; local observations do not establish project behavior.
9. Put attempts and previous versions in commit messages so docs describe the current project; retain a past failure when it explains a rule.
10. In your report, list each line added to a doc and which reader needs it, so the additions can be reviewed.

Claude Code: `/public-hygiene:doc-care`. Codex: `$public-hygiene:doc-care`.
